from typing import List, Dict, Optional

class ApiCallDetail:
    def __init__(
        self,
        user_name: str,
        api_name: str,
        api_call: str,
        api_version: Optional[str],
        api_arguments: List[List[str]],
        functionality: str,
        env_requirements: Optional[str],
        example_code: str,
        meta_data: Optional[str],
        questions: List[str]
    ) -> None:
        self.user_name = user_name
        self.api_name = api_name
        self.api_call = api_call
        self.api_version = api_version
        self.api_arguments = api_arguments
        self.functionality = functionality
        self.env_requirements = env_requirements
        self.example_code = example_code
        self.meta_data = meta_data
        self.questions = questions

class ConvertedURL:
    def __init__(self, status: str, data: List[ApiCallDetail]) -> None:
        self.status = status
        self.data = data

class ConvertResult:
    def __init__(self, results: Dict[str, ConvertedURL]) -> None:
        self.results = results