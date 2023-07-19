"""
Thanks to llama-index for the template of this code.
"""
from pydantic import BaseModel, Field
from retrievers.schema import BaseRetriever, Document
from rank_bm25 import BM25Okapi
from typing import Any, Dict, List, cast


class BM25Retriever(BaseRetriever, BaseModel):

    index: Any
    corpus: Any
    query_kwargs: Dict = dict(similarity_top_k = 5)

    def get_relevant_documents(self, query: str) -> List[Document]:

        tokenized_query = query.split(" ")
        bm25_docs = self.index.get_top_n(tokenized_query, self.corpus, n=self.query_kwargs["similarity_top_k"])
        docs = []
        for source_node in bm25_docs:
            metadata = {}
            docs.append(
                Document(page_content=str(source_node), metadata=metadata)
            )
        return docs

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("Does not support async")

