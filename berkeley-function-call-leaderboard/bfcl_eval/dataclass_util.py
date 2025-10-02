"""
Holds various dataclasses to house json data. 
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum
import json


class MessageRole(Enum):
    """Enum for message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


def _parse_function_parameters(func_data: Dict[str, Any]) -> Dict[str, 'FunctionParameter']:
    """Helper function to parse function parameters from dict."""
    parameters = {}
    for param_name, param_data in func_data.get("parameters", {}).get("properties", {}).items():
        parameters[param_name] = FunctionParameter(
            type=param_data.get("type", "string"),
            description=param_data.get("description", ""),
            default=param_data.get("default"),
            enum=param_data.get("enum"),
            items=param_data.get("items")
        )
    return parameters


def _serialize_function_parameters(func: 'FunctionDefinition') -> Dict[str, Any]:
    """Helper function to serialize function parameters to dict."""
    return {
        "type": "dict",
        "properties": {
            param_name: {
                "type": param.type,
                "description": param.description,
                **({"default": param.default} if param.default is not None else {}),
                **({"enum": param.enum} if param.enum else {}),
                **({"items": param.items} if param.items else {})
            }
            for param_name, param in func.parameters.items()
        },
        "required": func.required
    }


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: MessageRole
    content: str


@dataclass
class FunctionParameter:
    """Represents a function parameter definition."""
    type: str
    description: str
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None  # For array items


@dataclass
class FunctionDefinition:
    """Represents a function definition in a test case."""
    name: str
    description: str
    parameters: Dict[str, FunctionParameter]
    required: List[str]


@dataclass
class InferenceData:
    """
    Represents inference data used during model inference.
    """
    message: List[Dict[str, Any]] 
    function: List[FunctionDefinition]
    tools: Optional[List[Dict[str, Any]]] = None
    inference_input_log: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InferenceData':
        """Create InferenceData from a dictionary."""
        functions = []
        for func in data.get("function", []):
            if isinstance(func, dict):
                functions.append(FunctionDefinition(
                    name=func["name"],
                    description=func["description"],
                    parameters=_parse_function_parameters(func),
                    required=func.get("parameters", {}).get("required", [])
                ))

        return cls(
            message=data.get("message", []),
            function=functions,
            tools=data.get("tools"),
            inference_input_log=data.get("inference_input_log")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert InferenceData back to dictionary format."""
        result = {
            "message": self.message,
            "function": [
                {
                    "name": func.name,
                    "description": func.description,
                    "parameters": _serialize_function_parameters(func)
                }
                for func in self.function
            ]
        }
        
        if self.tools:
            result["tools"] = self.tools
        if self.inference_input_log:
            result["inference_input_log"] = self.inference_input_log
            
        return result


@dataclass
class ModelResponse:
    """
    Represents model response data.
    """
    model_responses: Any 
    input_token: int
    output_token: int
    reasoning_content: Optional[str] = None
    model_responses_message_for_chat_history: Optional[Dict[str, Any]] = None
    tool_call_ids: Optional[List[str]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelResponse':
        """Create ModelResponse from a dictionary."""
        return cls(
            model_responses=data["model_responses"],
            input_token=data["input_token"],
            output_token=data["output_token"],
            reasoning_content=data.get("reasoning_content"),
            model_responses_message_for_chat_history=data.get("model_responses_message_for_chat_history"),
            tool_call_ids=data.get("tool_call_ids"),
            tool_calls=data.get("tool_calls")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ModelResponse back to dictionary format."""
        result = {
            "model_responses": self.model_responses,
            "input_token": self.input_token,
            "output_token": self.output_token
        }
        
        if self.reasoning_content:
            result["reasoning_content"] = self.reasoning_content
        if self.model_responses_message_for_chat_history:
            result["model_responses_message_for_chat_history"] = self.model_responses_message_for_chat_history
        if self.tool_call_ids:
            result["tool_call_ids"] = self.tool_call_ids
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
            
        return result


@dataclass
class TestCase:
    """
    Represents a test case loaded from JSON with full type safety.
    
    This dataclass replaces raw dictionary usage when working with test cases.
    """
    id: str
    question: List[List[Message]]
    function: List[FunctionDefinition]
    initial_config: Optional[Dict[str, Any]] = None
    involved_classes: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None
    missed_function: Optional[Dict[str, List[str]]] = None
    scenario: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """
        Create a TestCase from a dictionary (loaded from JSON).
        
        Args:
            data: Dictionary containing test case data
            
        Returns:
            TestCase object with typed fields
        """
        # Parse question messages - handle empty turns
        question_messages = []
        for turn in data.get("question", []):
            turn_messages = []
            for msg in turn:  # Skip empty turns
                turn_messages.append(Message(
                    role=MessageRole(msg["role"]),
                    content=msg["content"]
                ))
            question_messages.append(turn_messages)

        functions = []
        for func in data.get("function", []):
            functions.append(FunctionDefinition(
                name=func["name"],
                description=func["description"],
                parameters=_parse_function_parameters(func),
                required=func.get("parameters", {}).get("required", [])
            ))

        return cls(
            id=data["id"],
            question=question_messages,
            function=functions,
            initial_config=data.get("initial_config"),
            involved_classes=data.get("involved_classes"),
            depends_on=data.get("depends_on"),
            missed_function=data.get("missed_function"),
            scenario=data.get("scenario")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert TestCase back to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of the test case
        """
        result = {
            "id": self.id,
            "question": [
                [
                    {
                        "role": msg.role.value,
                        "content": msg.content
                    }
                    for msg in turn
                ]
                for turn in self.question
            ],
            "function": [
                {
                    "name": func.name,
                    "description": func.description,
                    "parameters": _serialize_function_parameters(func)
                }
                for func in self.function
            ]
        }
        
        # Add optional fields
        if self.initial_config:
            result["initial_config"] = self.initial_config
        if self.involved_classes:
            result["involved_classes"] = self.involved_classes
        if self.depends_on:
            result["depends_on"] = self.depends_on
        if self.missed_function:
            result["missed_function"] = self.missed_function
        if self.scenario:
            result["scenario"] = self.scenario
            
        return result


def load_test_cases_from_json(file_path: str) -> List[TestCase]:
    """
    Load test cases from a JSON file with type safety.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of TestCase objects
    """
    test_cases = []
    
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                test_cases.append(TestCase.from_dict(data))
    
    return test_cases


def save_test_cases_to_json(test_cases: List[TestCase], file_path: str) -> None:
    """
    Save test cases to a JSON file.
    
    Args:
        test_cases: List of TestCase objects to save
        file_path: Path to save the JSON file
    """
    with open(file_path, 'w') as f:
        for test_case in test_cases:
            f.write(json.dumps(test_case.to_dict()) + '\n')