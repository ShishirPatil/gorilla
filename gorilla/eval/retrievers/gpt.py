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

from typing import Any, Dict, List, cast, Optional

from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_random_exponential
from retrievers.schema import BaseRetriever, Document
import openai
import numpy as np
import os
import copy
import json

class GPTRetriever(BaseRetriever, BaseModel):

    index: Any
    query_kwargs: Dict = dict(similarity_top_k = 5)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def get_embeddings(
        self,
	list_of_text: List[str],
	engine: Optional[str] = None,
    ) -> List[List[float]]:
        assert len(list_of_text) <= 2048, "The number of docs should be <= 2048"
        list_of_text = [text.replace("\n", " ") for text in list_of_text]
        openai.api_key = os.environ["OPENAI_API_KEY"]
        data = openai.Embedding.create(input=list_of_text, engine="text-embedding-ada-002").data
        data = sorted(data, key=lambda x: x["index"])  # maintain the same order as input.
        return [d["embedding"] for d in data]
  
    def from_documents(self, documents: List):
        contents = [document.page_content for document in documents]
        embeddings = self.get_embeddings(list_of_text=contents)
        self.index = []
        for i, (embedding, document) in enumerate(zip(embeddings, documents)):
            new_node = {}
            new_node["embedding"] = embedding
            new_node["text"] = document.page_content
            self.index.append(new_node)
        return self.index

    def save_to_disk(self, index, save_path):
        with open(save_path, "w") as outfile:
            json.dump(self.index, outfile)

    def load_from_disk(self, load_path):
        with open(load_path, "r") as loadfile:
            self.index = json.load(loadfile)
        
    def get_relevant_documents(self, query: str) -> List[Document]:
        docs_embeddings = np.array([doc["embedding"] for doc in self.index])

        query_embedding = np.array(self.get_embeddings([query])[0])

        # get cos similarity
        docs_embeddings = docs_embeddings / np.linalg.norm(docs_embeddings, axis=-1, keepdims=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=-1, keepdims=True)
        logits = np.sum(query_embedding[None, :] * docs_embeddings, axis=-1)
        top_k = logits.argsort()[-self.query_kwargs["similarity_top_k"]:][::-1]
        top_k_docs = [self.index[i]["text"] for i in top_k]

        # parse source nodes
        docs = []
        for source_node in top_k_docs:
            docs.append(
                Document(page_content=source_node, metadata="")
            )
        return docs

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("LlamaIndexRetriever does not support async")
