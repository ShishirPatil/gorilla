# Copyright 2023 https://github.com/ShishirPatil/gorilla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import json

from retrievers.schema import Document


class JSONLReader(abc.ABC):
    def __init__(
        self,
        levels_back: int | None = None,
        collapse_length: int | None = None,
    ) -> None:
        """Initialize with arguments."""
        super().__init__()
        self.levels_back = levels_back
        self.collapse_length = collapse_length

    def load_data(self, input_file: str) -> list[Document]:
        """Load data from the input file."""
        data = []
        with open(input_file) as f:
            for line in f:
                data.append(str(json.loads(line)))
        if self.levels_back is None:
            return [Document(page_content=_data) for _data in data]
        elif self.levels_back is not None:
            lines = [
                *_depth_first_yield(
                    data, self.levels_back, self.collapse_length, []
                )
            ]
            return [Document(page_content="\n".join(lines))]
