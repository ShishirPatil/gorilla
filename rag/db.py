from sentence_transformers import SentenceTransformer
from datasets import load_dataset

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

### Build and embed a dataset to the FAISS vector db

dataset = load_dataset("databricks/databricks-dolly-15k")

contexts = ''.join(dataset['train']['context'])

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150, length_function=len, is_separator_regex=False)

docs = text_splitter.create_documents([contexts])

embedder_path = "rag-embed-model"

embedder = HuggingFaceEmbeddings(
    model_name=embedder_path,
    model_kwargs={'device':'cpu'}, 
    encode_kwargs={'normalize_embeddings': False} 
)

db = FAISS.from_documents(docs, embedder)

db.save_local("faiss_index")