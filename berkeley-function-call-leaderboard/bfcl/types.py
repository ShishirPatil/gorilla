import json
import hashlib
from enum import Enum
from pathlib import Path
from typing import Any, List, Dict, Type

from pydantic import BaseModel, model_validator
from huggingface_hub import hf_hub_download

from bfcl.utils import CustomEnum


class ModelType(str, Enum):
    OSS = 'oss'
    PROPRIETARY = 'proprietary'

class LeaderboardNonPythonCategory(str, CustomEnum):
    JAVA = 'java'
    JAVASCRIPT = 'javascript'

class LeaderboardAstCategory(str, CustomEnum):
    SIMPLE = 'simple'
    RELEVANCE = 'relevance'
    MULTIPLE_FUNCTION = 'multiple_function'
    PARALLEL_FUNCTION = 'parallel_function'
    PARALLEL_MULTIPLE_FUNCTION = 'parallel_multiple_function'
    JAVA = LeaderboardNonPythonCategory.JAVA.value
    JAVASCRIPT = LeaderboardNonPythonCategory.JAVASCRIPT.value

class LeaderboardExecutableCategory(str, CustomEnum):
    EXECUTABLE_SIMPLE = 'executable_simple'
    EXECUTABLE_PARALLEL_FUNCTION = 'executable_parallel_function'
    EXECUTABLE_MULTIPLE_FUNCTION = 'executable_multiple_function'
    EXECUTABLE_PARALLEL_MULTIPLE_FUNCTION = 'executable_parallel_multiple_function'
    REST = 'rest'

LeaderboardPythonCategory: Type[CustomEnum] = (
    LeaderboardAstCategory
    .add(LeaderboardExecutableCategory)
    .subtract(LeaderboardNonPythonCategory)
    .rename('LeaderboardPythonCategory')
)

LeaderboardCategory: Type[CustomEnum] = (
    LeaderboardPythonCategory
    .add(LeaderboardNonPythonCategory)
    .rename('LeaderboardCategory')
    .update(dict(SQL='sql', CHATABLE='chatable'))
)

class LeaderboardCategoryGroup(str, Enum):
    AST = 'ast'
    EXECUTABLE = 'executable'
    NON_PYTHON = 'non_python'
    PYTHON = 'python'
    ALL = 'all'

CATEGORY_GROUP_MAPPING = {
    LeaderboardCategoryGroup.AST: LeaderboardAstCategory,
    LeaderboardCategoryGroup.EXECUTABLE: LeaderboardExecutableCategory,
    LeaderboardCategoryGroup.NON_PYTHON: LeaderboardNonPythonCategory,
    LeaderboardCategoryGroup.PYTHON: LeaderboardPythonCategory,
    LeaderboardCategoryGroup.ALL: LeaderboardCategory
}

class LeaderboardVersion(str, Enum):
    V1 = 'v1'


class Leaderboard(BaseModel):
    test_group: LeaderboardCategoryGroup | None = None
    test_categories: List[LeaderboardCategory] | None = None # type: ignore
    version: LeaderboardVersion = LeaderboardVersion.V1
    cache_dir: Path | str = '.cache'

    @model_validator(mode='before')
    @classmethod
    def check_either_field_provided(cls, values):
        if values.get('test_group') is not None and values.get('test_categories') is not None:
            raise ValueError("Provide either 'test_group' or 'test_categories', not both")
        elif values.get('test_group') is None and values.get('test_categories') is None:
            raise ValueError("Provide either 'test_group' or 'test_categories'")
        return values

    def model_post_init(self, __context: Any) -> None:
        if self.test_group:
            self.test_categories = [cat for cat in CATEGORY_GROUP_MAPPING[self.test_group]]
        self.cache_dir = Path.cwd() / self.cache_dir

    @property
    def test_data_cache_dir(self) -> Path:
        test_data_dir = self.cache_dir / f'gorilla_openfunctions_{self.version.value}_test_data'
        test_data_dir.mkdir(exist_ok=True, parents=True)
        return test_data_dir

    def load_test_data(self) -> Dict[LeaderboardCategory, List[Dict]]: # type: ignore
        data = {}
        for test_category, infile_path in self._get_test_data():
            data[test_category] = []
            # We add `id` and `test_category` to each dataset sample
            # Save the dataset in the cache with the updated keys for user reference
            outfile_path = self.test_data_cache_dir / self.get_file_name(test_category)
            if outfile_path.exists():
                with open(outfile_path, 'r') as file:
                    for line in file:
                        data[test_category].append(json.loads(line))
            else:
                with open(infile_path, 'r') as infile, open(outfile_path, 'w') as outfile:
                    for line in infile:
                        item = json.loads(line)
                        item['test_category'] = test_category.value
                        item['id'] = self._generate_hash(json.dumps(item))
                        data[test_category].append(item)
                        outfile.write(json.dumps(item) + '\n')
        return data

    def get_file_name(self, test_category: LeaderboardCategory) -> str: # type: ignore
        return f'gorilla_openfunctions_{self.version.value}_test_{test_category.value}.json'

    def _get_test_data(self):
        for test_category in self.test_categories:
            file_path = hf_hub_download(
                repo_id='gorilla-llm/Berkeley-Function-Calling-Leaderboard',
                filename=self.get_file_name(test_category),
                repo_type='dataset',
                cache_dir=self.cache_dir
            )
            yield test_category, file_path

    def _generate_hash(self, input_str) -> str:
        hash_object = hashlib.sha256(input_str.encode('utf-8'))
        return hash_object.hexdigest()
