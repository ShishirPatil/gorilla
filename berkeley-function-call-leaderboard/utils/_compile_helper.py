import inspect
import json
import re
from typing import Dict, Union

TYPE_MAPPING = {
    "str": "string",
    "int": "integer",
    "float": "float",
    "bool": "boolean",
    "any": "any",
    "dict": "dict",
    "list": "array",
    "tuple": "tuple",
}


# Type Conversions
def convert_type_to_json_compatible(type_name: str) -> str:

    return TYPE_MAPPING.get(type_name.lower(), "any")


def parse_type_string(type_str: str) -> dict:
    """
    Parses a type string and returns a dict with type information.
    """
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        type_str = type_str[len("Optional[") : -1]

    if type_str.startswith("Union[") and type_str.endswith("]"):
        union_types = type_str[len("Union[") : -1].split(", ")
        if "NoneType" in union_types or "None" in union_types:
            union_types = [t for t in union_types if t != "NoneType" and t != "None"]
        if len(union_types) == 1:
            return parse_type_string(union_types[0])
        else:
            return {"type": "any"}

    list_match = re.match(r"(?:List|list)\[(.+)\]", type_str)
    if list_match:
        inner_type_str = list_match.group(1)
        items_type = parse_type_string(inner_type_str)
        return {"type": "array", "items": items_type}

    tuple_match = re.match(r"(?:Tuple|tuple)\[(.+)\]", type_str)
    if tuple_match:
        inner_type_str = tuple_match.group(1)
        inner_types_strs = [t.strip() for t in inner_type_str.split(",")]
        items_types = [parse_type_string(t) for t in inner_types_strs]
        return {"type": "array", "items": items_types}

    dict_match = re.match(r"(?:Dict|dict)\[(.+),\s*(.+)\]", type_str)
    if dict_match:
        key_type_str, value_type_str = dict_match.groups()
        key_type = convert_type_to_json_compatible(key_type_str)
        value_type = parse_type_string(value_type_str)
        if key_type != "string":
            key_type = "string"
        return {"type": "dict", "additionalProperties": value_type}

    base_type = convert_type_to_json_compatible(type_str)
    return {"type": base_type}


def parse_docstring(docstring: str) -> Dict[str, Union[str, dict]]:
    description = ""
    parameters = {}
    response = {}
    lines = docstring.strip().split("\n")
    current_section = None
    indent_levels = []
    base_indent = None

    for idx, line in enumerate(lines):
        original_line = line
        line = line.rstrip()
        stripped_line = line.lstrip()
        current_indent = len(line) - len(stripped_line)

        if stripped_line.startswith("Args:"):
            current_section = "parameters"
            continue
        elif stripped_line.startswith("Returns:"):
            current_section = "response"
            continue

        if current_section is None:
            description += stripped_line + " "
        elif current_section == "parameters":
            match = re.match(r"(\w+)\s*\(([^)]+)\):\s*(.+)", stripped_line)
            if match:
                param_name, param_type_str, param_desc = match.groups()
                param_desc = (
                    param_desc.replace("[Required]", "").replace("[Optional]", "").strip()
                )
                type_info = parse_type_string(param_type_str)
                param_entry = type_info
                param_entry["description"] = param_desc
                parameters[param_name] = param_entry
            else:
                if parameters:
                    last_param = list(parameters.keys())[-1]
                    parameters[last_param]["description"] += " " + stripped_line
        elif current_section == "response":
            if not stripped_line:
                continue

            match = re.match(r"-?\s*(\w+)\s*\(([^)]+)\):\s*(.+)", stripped_line)
            if match:
                name, type_str, desc = match.groups()
                type_info = parse_type_string(type_str)
                desc = desc.strip()
                new_property = {"type": type_info.get("type", "any"), "description": desc}
                if "items" in type_info:
                    new_property["items"] = type_info["items"]
                if "properties" in type_info:
                    new_property["properties"] = type_info["properties"]
                if "additionalProperties" in type_info:
                    new_property["additionalProperties"] = type_info["additionalProperties"]

                if base_indent is None:
                    base_indent = current_indent

                # assume 4 spaces for each indent
                level = (current_indent - base_indent) // 4

                while len(indent_levels) > level:
                    indent_levels.pop()

                if not indent_levels:
                    response[name] = new_property
                    indent_levels.append(response[name])
                else:
                    parent = indent_levels[-1]
                    if parent.get("type") == "array":
                        if "items" not in parent:
                            parent["items"] = {}
                        if "properties" not in parent["items"]:
                            parent["items"]["properties"] = {}
                        parent["items"]["properties"][name] = new_property
                        indent_levels.append(parent["items"]["properties"][name])
                    else:
                        if "properties" not in parent:
                            parent["properties"] = {}
                        parent["properties"][name] = new_property
                        indent_levels.append(parent["properties"][name])
            else:
                if indent_levels:
                    current_property = indent_levels[-1]
                    current_property["description"] += " " + stripped_line
                else:
                    if "description" in response:
                        response["description"] += " " + stripped_line
                    else:
                        response["description"] = stripped_line

    return {
        "description": description.strip(),
        "parameters": {"type": "dict", "properties": parameters},
        "response_properties": response,
    }


def function_to_json(func) -> str:
    func_name = func.__name__
    docstring = func.__doc__

    if not docstring:
        raise ValueError("Function must have a docstring.")

    parsed_data = parse_docstring(docstring)

    # Response is always a dictionary
    response_structure = {"type": "dict", "properties": parsed_data["response_properties"]}

    json_representation = {
        "name": func_name,
        "description": parsed_data["description"],
        "parameters": parsed_data["parameters"],
        "response": response_structure,
    }

    # Adjust parameters based on function signature
    sig = inspect.signature(func)
    required_params = []
    for param_name, param in sig.parameters.items():
        if param_name == "self" or param_name == "cls":
            continue

        if param.default is inspect.Parameter.empty:
            required_params.append(param_name)
        else:
            if param_name in json_representation["parameters"]["properties"]:
                default_value = param.default
                param_type = json_representation["parameters"]["properties"][param_name][
                    "type"
                ]
                if param_type == "string":
                    default_value = str(default_value)
                elif param_type == "integer":
                    default_value = int(default_value)
                elif param_type == "number":
                    default_value = float(default_value)
                elif param_type == "boolean":
                    default_value = bool(default_value)
                json_representation["parameters"]["properties"][param_name][
                    "default"
                ] = default_value

    # Always include 'required', even if it's empty
    json_representation["parameters"]["required"] = required_params

    return json.dumps(json_representation)


# PROOF OF CONCEPT TEST


class TestAPI:
    # Amitoj Note: PASTE WHICHEVER FUNCTION YOU WANT TO CHECK HERE AND REPLACE
    def displayCarStatus(
        self, option: str, format: str = "detailed"
    ) -> Dict[str, Union[str, float, Dict[str, str]]]:
        """
        Displays the status of the vehicle based on the provided display option.
        Args:
            option (str): The option to display. [Enum]: ["fuel", "battery", "doors", "climate", "headlights", "brake", "engine"]
            format (str): [Optional] The format of the display. [Enum]: ["detailed", "simple"]
        Returns:
            status (Dict): The status of the vehicle based on the option.
                - fuelLevel (float): The fuel level of the vehicle in gallons.
                - batteryVoltage (float): The battery voltage of the vehicle in volts.
                - doorStatus (Dict): The status of the doors. [Enum]: ["driver", "passenger", "rear_left", "rear_right"]
                    - driver (str): The status of the driver door. [Enum]: ["locked", "unlocked"]
                    - passenger (str): The status of the passenger door. [Enum]: ["locked", "unlocked"]
                    - rear_left (str): The status of the rear left door. [Enum]: ["locked", "unlocked"]
                    - rear_right (str): The status of the rear right door. [Enum]: ["locked", "unlocked"]
                - currentACTemperature (float): The current temperature set in degree Celsius.
                - headlightStatus (str): The status of the headlights. [Enum]: ["on", "off"]
                - brakeStatus (str): The status of the brake. [Enum]: ["engaged", "released"]
                - engineState (str): The state of the engine. [Enum]: ["running", "stopped"]
        """
        pass


# test_api = TestAPI()
# print(function_to_json(test_api.displayCarStatus))
