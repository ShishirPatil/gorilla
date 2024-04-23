from os import environ as env
from typing import Any
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from openai import AzureOpenAI, OpenAI
import logging

logger = logging.getLogger("client_utils")

load_dotenv()  # take environment variables from .env.

def build_openai_client(**kwargs: Any) -> OpenAI:
    """
    Build OpenAI client based on the environment variables.
    """
    if is_azure():
        client = AzureOpenAI(**kwargs)
    else:
        client = OpenAI(**kwargs)
    return client

def build_langchain_embeddings(**kwargs: Any) -> OpenAIEmbeddings:
    """
    Build OpenAI embeddings client based on the environment variables.
    """
    if is_azure():
        client = AzureOpenAIEmbeddings(**kwargs)
    else:
        client = OpenAIEmbeddings(**kwargs)
    return client

def is_azure():
    azure = "AZURE_OPENAI_ENDPOINT" in env or "AZURE_OPENAI_KEY" in env or "AZURE_OPENAI_AD_TOKEN" in env
    if azure:
        logger.debug("Using Azure OpenAI environment variables")
    else:
        logger.debug("Using OpenAI environment variables")
    return azure
