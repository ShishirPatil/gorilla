from typing import Any
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from openai import AzureOpenAI, OpenAI
import logging
from env_config import read_env_config, set_env
from os import environ
import time


logger = logging.getLogger("client_utils")

def build_openai_client(env_prefix : str = "COMPLETION", **kwargs: Any) -> OpenAI:
    """
    Build OpenAI client based on the environment variables.
    """

    env = read_env_config(env_prefix)
    with set_env(**env):
        if is_azure():
            client = AzureOpenAI(**kwargs)
        else:
            client = OpenAI(**kwargs)
        return client

def build_langchain_embeddings(**kwargs: Any) -> OpenAIEmbeddings:
    """
    Build OpenAI embeddings client based on the environment variables.
    """

    env = read_env_config("EMBEDDING")

    with set_env(**env):
        if is_azure():
            client = AzureOpenAIEmbeddings(**kwargs)
        else:
            client = OpenAIEmbeddings(**kwargs)
        return client

def is_azure():
    azure = "AZURE_OPENAI_ENDPOINT" in environ or "AZURE_OPENAI_KEY" in environ or "AZURE_OPENAI_AD_TOKEN" in environ
    if azure:
        logger.debug("Using Azure OpenAI environment variables")
    else:
        logger.debug("Using OpenAI environment variables")
    return azure

class CompleterState:
    def __init__(self) -> None:
        self.start = time.time()
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.total_tokens = 0
        self.end = None
        self.duration = 0
        self.calls = 0

    def __add__(self, other: 'CompleterState') -> 'CompleterState':
        state = CompleterState()
        state.start = min(self.start, other.start)
        state.end = max(self.end, other.end)
        state.completion_tokens = self.completion_tokens + other.completion_tokens
        state.prompt_tokens = self.prompt_tokens + other.prompt_tokens
        state.total_tokens = self.total_tokens + other.total_tokens
        state.duration = self.duration + other.duration
        state.calls = self.calls + other.calls
        return state

class ChatCompleter:
    def __init__(self, client):
        self.client = client
        self.state = None

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if not self.state:
            self.state = CompleterState()
        response = self.client.chat.completions.create(*args, **kwds)
        self.state.completion_tokens += response.usage.completion_tokens
        self.state.prompt_tokens += response.usage.prompt_tokens
        self.state.total_tokens += response.usage.total_tokens
        self.state.calls += 1
        return response
    
    def get_and_reset(self) -> CompleterState:
        end = time.time()
        state = self.state
        state.end = end
        state.duration = end - self.state.start
        self.state = None
        return state
