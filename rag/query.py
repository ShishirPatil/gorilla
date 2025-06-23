from sentence_transformers import SentenceTransformer
from datasets import load_dataset

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain import HuggingFacePipeline
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
import torch

embedder_path = "rag-embed-model"

embedder = HuggingFaceEmbeddings(
    model_name=embedder_path,     
    model_kwargs={'device':'cpu'}, 
    encode_kwargs={'normalize_embeddings': False} 
)

db = FAISS.load_local("faiss_index", embedder)
retriever = db.as_retriever(search_kwargs={"k": 2})


#################
query = "What is on top of the Main Building at the University of Notre Dame?"
model_name = "Intel/dynamic_tinybert" 
#################


tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

def run(query):
    context = ''.join(c.page_content for c in retriever.get_relevant_documents(query))
    inputs = tokenizer(query, context, return_tensors="pt")

    outputs = model(**inputs)


    start_logits = outputs.start_logits
    end_logits = outputs.end_logits
    
    # Get the answer span (start and end positions)
    start_index = torch.argmax(start_logits)
    end_index = torch.argmax(end_logits)
    
    # Decode the answer from the token indices
    answer = tokenizer.decode(inputs["input_ids"][0, start_index:end_index+1])
    
    return answer

print(run(query))
