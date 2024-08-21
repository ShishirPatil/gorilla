from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.handler import BaseHandler
from bfcl.model_handler.utils import (
    ast_parse,
    func_doc_language_specific_pre_processing,
)
import requests, time


class NexusHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.NEXUS

    def generate_functions_from_dict(self, func_dicts):
        func_template = """
    Function:
    def {func_name}({func_args}) -> None:
        \"\"\"
        {description}

        Parameters:
        {param_descriptions}
        \"\"\"

    """

        functions = []
        for func_dict in func_dicts:
            func_name = func_dict['name']
            description = func_dict['description']
            parameters = func_dict['parameters']['properties']
            required_params = func_dict['parameters'].get('required', [])

            func_args_list = []
            param_descriptions = []

            for param, details in parameters.items():
                param_type = details['type']
                if 'enum' in details:
                    param_type = f"""String[{', '.join(f"'{e}'" for e in details['enum'])}]"""

                param_type = param_type.replace("string", "str").replace("number", "float").replace("integer", "int").replace("object", "dict").replace("array", "list").replace("boolean", "bool")

                type_hint = param_type

                if param in required_params:
                    func_args_list.append(f"{param}: {type_hint}")
                else:
                    func_args_list.append(f"{param}: {type_hint} = None")

                param_description = f"{param} ({param_type}): {details.get('description', 'No description available. Please make a good guess.')}"

                if 'enum' in details:
                    param_description += f""". Choose one of {', '.join(f"'{e}'" for e in details['enum'])}."""

                if param not in required_params:
                    param_description += " (Optional)"
                param_descriptions.append(param_description)

            func_args = ', '.join(func_args_list)
            param_descriptions_str = '\n    '.join(param_descriptions)

            function_str = func_template.format(
                func_name=func_name,
                func_args=func_args,
                description=description,
                param_descriptions=param_descriptions_str
            )

            functions.append(function_str)

        functions.append(
    '''
    Function:
    def out_of_domain(user_query: str) -> str:
        """
        This function is designed to handle out-of-domain queries from the user.
        If the user provides any input user query that is out of the domain of the other APIs provided above,
        this function should be used with the input user query as the string.

        - user_query (str): The input string that is out of domain.

        Returns nothing.
        """

    ''')

        return functions


    def _format_raven_function(self, user_prompts, functions):
        """
        Nexus-Raven requires a specific format for the function description.
        This function formats the function description in the required format.
        """
        raven_prompt = "\n".join(self.generate_functions_from_dict(functions)) + "\n\n"
        raven_prompt += "Setting: Allowed to issue multiple calls with semicolon\n"
        for user_prompt in user_prompts:
            raven_prompt += f"{user_prompt['role']}: {user_prompt['content']}\n"
        
        raven_prompt += f"<human_end>"
            
        return raven_prompt


    def _query_raven(self, prompt):
        """
        Query Nexus-Raven.
        """

        API_URL = "http://nexusraven.nexusflow.ai"
        headers = {"Content-Type": "application/json"}

        def query(payload):
            """
            Sends a payload to a TGI endpoint.
            """
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()

        start = time.time()
        output = query(
            {
                "inputs": prompt,
                "parameters": {
                    "temperature": self.temperature,
                    "stop": ["<bot_end>"],
                    "do_sample": False,
                    "max_new_tokens": self.max_tokens,
                    "return_full_text": False,
                },
            }
        )
        latency = time.time() - start
        call = output[0]["generated_text"].replace("Call:", "").strip()
        return call, {"input_tokens": 0, "output_tokens": 0, "latency": latency}

    def inference(self, prompt, functions, test_category):
        functions = func_doc_language_specific_pre_processing(functions, test_category)
        raven_prompt = self._format_raven_function(prompt, functions)
        result, metadata = self._query_raven(raven_prompt)
        return result, metadata

    def decode_ast(self, result, language="Python"):
        if result.endswith(";"):
            result = result[:-1]
        result = result.replace(";", ",")
        func = "[" + result + "]"
        decoded_output = ast_parse(func, language)
        if "out_of_domain" in result:
            return "irrelevant"

        return decoded_output

    def decode_execute(self, result):
        if result.endswith(";"):
            result = result[:-1]
        result = result.replace(";", ",")
        func = "[" + result + "]"
        decoded_output = ast_parse(func)
        execution_list = []
        for function_call in decoded_output:
            for key, value in function_call.items():
                execution_list.append(
                    f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                )
        return execution_list
