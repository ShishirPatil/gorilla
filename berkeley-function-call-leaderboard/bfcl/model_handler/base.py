import json
from typing import List, Dict
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod


class ModelStyle(str, Enum):
    GORILLA = "gorilla"
    OPENAI = "openai"
    ANTHROPIC_FC = "claude"
    ANTHROPIC_PROMPT = "claude"
    MISTRAL = "mistral"
    GOOGLE = "google"
    COHERE = "cohere"
    FIREWORK_AI = "firework_ai"
    NEXUS = "nexus"
    OSS_MODEL = "oss_model"


class BaseHandler(ABC):
    model_style: str

    def __init__(
        self, 
        model_name: str,
        temperature: float = 0.7, 
        top_p: int = 1, 
        max_tokens: int = 1000,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        self.result_dir = Path.cwd() / 'result'
        self.result_dir.mkdir(exist_ok=True)

    @classmethod
    @abstractmethod
    def supported_models(cls) -> List[str]:
        pass

    @abstractmethod
    def inference(self):
        """Fetch response from the model."""
        pass

    @abstractmethod
    def decode_ast(self, result, language):
        """Takes raw model output and converts it to the standard AST checker input."""
        pass

    @abstractmethod
    def decode_execute(self, result):
        """Takes raw model output and converts it to the standard execute checker input."""
        pass

    def write(self, responses: List[Dict], file_name):
        """Write the model responses to the file."""

        model_dir = self.result_dir / self.model_name.replace('/', '--')
        model_dir.mkdir(exist_ok=True, parents=True)
        file_path = model_dir / file_name
        with open(file_path, 'w') as file:
            for response in responses:
                file.write(json.dumps(response) + '\n')
        print(f'Saved model responses at "{file_path}".')

    def load_result(self, file_path):
        """Load the result from the file."""

        with open(file_path, 'r') as f:
            result = [json.loads(line) for line in f]
        return result
