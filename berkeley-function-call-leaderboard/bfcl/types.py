import json
import hashlib
from enum import Enum
from typing import Any, List, Dict
from pathlib import Path

from pydantic import BaseModel
from huggingface_hub import hf_hub_download


class ModelType(str, Enum):
    OSS = 'oss'
    PROPRIETARY = 'proprietary'


class LeaderboardExecutableCategory(str, Enum):
    EXEC_SIMPLE = 'executable_simple'
    EXEC_PARALLEL_FUNCTION = 'executable_parallel_function'
    EXEC_MULTIPLE_FUNCTION = 'executable_multiple_function'
    EXEC_PARALLEL_MULTIPLE_FUNCTION = 'executable_parallel_multiple_function'
    REST = 'rest'


class LeaderboardAstCategory(str, Enum):
    SIMPLE = 'simple'
    RELEVANCE = 'relevance'
    PARALLEL_FUNCTION = 'parallel_function'
    MULTIPLE_FUNCTION = 'multiple_function'
    PARALLEL_MULTIPLE_FUNCTION = 'parallel_multiple_function'
    JAVA = 'java'
    JAVASCRIPT = 'javascript'


class LeaderboardCategory(str, Enum):
    EXEC_SIMPLE = LeaderboardExecutableCategory.EXEC_SIMPLE.value
    EXEC_PARALLEL_FUNCTION = LeaderboardExecutableCategory.EXEC_PARALLEL_FUNCTION.value
    EXEC_MULTIPLE_FUNCTION = LeaderboardExecutableCategory.EXEC_MULTIPLE_FUNCTION.value
    EXEC_PARALLEL_MULTIPLE_FUNCTION = LeaderboardExecutableCategory.EXEC_PARALLEL_MULTIPLE_FUNCTION.value
    REST = LeaderboardExecutableCategory.REST.value
    SIMPLE = LeaderboardAstCategory.SIMPLE.value
    RELEVANCE = LeaderboardAstCategory.RELEVANCE.value
    PARALLEL_FUNCTION = LeaderboardAstCategory.PARALLEL_FUNCTION.value
    MULTIPLE_FUNCTION = LeaderboardAstCategory.MULTIPLE_FUNCTION.value
    PARALLEL_MULTIPLE_FUNCTION = LeaderboardAstCategory.PARALLEL_MULTIPLE_FUNCTION.value
    JAVA = LeaderboardAstCategory.JAVA.value
    JAVASCRIPT = LeaderboardAstCategory.JAVASCRIPT.value
    SQL = 'sql'
    CHATABLE = 'chatable'
    ALL = 'all'  # Adding the 'ALL' category


class LeaderboardVersion(str, Enum):
    V1 = 'v1'


class LeaderboardCategories(BaseModel):
    categories: List[LeaderboardCategory]
    version: LeaderboardVersion = LeaderboardVersion.V1
    cache_dir: Path | str = '.cache'

    def model_post_init(self, __context: Any) -> None:
        if LeaderboardCategory.ALL in self.categories:
            self.categories = [cat for cat in LeaderboardCategory if cat != LeaderboardCategory.ALL]
        self.cache_dir = Path.cwd() / self.cache_dir
    
    @property
    def output_file_path(self) -> Path:
        uid = self._generate_hash(self.model_dump_json())
        file_name = f'{uid}.jsonl'
        return self.cache_dir / file_name

    def load_data(self) -> List[Dict]:
        data = []
        if self.output_file_path.exists():
            print(f'Loading test data from "{self.output_file_path}" 🦍')
            # Load cached data
            with open(self.output_file_path, 'r') as file:
                for line in file:
                    item = json.loads(line)
                    data.append(item)
        else:
            # Load data for each test category
            for category, file_path in self._get_test_data():
                with open(file_path, 'r') as file:
                    for line in file:
                        item = json.loads(line)
                        item['test_category'] = category.value
                        item['id'] = self._generate_hash(json.dumps(item))
                        data.append(item)
            
            # Save data
            with open(self.output_file_path, 'w') as file:
                for item in data:
                    file.write(item + '\n')
            print(f'Test data successfully saved at "{self.output_file_path}" 🦍')

        return data

    def _get_test_data(self):
        template = f'gorilla_openfunctions_{self.version.value}_test_{{}}.json'
        for category in self.categories:
            file_path = hf_hub_download(
                repo_id='gorilla-llm/Berkeley-Function-Calling-Leaderboard',
                filename=template.format(category.value),
                repo_type='dataset',
                cache_dir=self.cache_dir
            )
            yield category, file_path

    def _generate_hash(self, input_str) -> str:
        hash_object = hashlib.sha256(input_str.encode('utf-8'))
        return hash_object.hexdigest()
