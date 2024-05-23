from abc import ABC
from typing import Any
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from openai import AzureOpenAI, OpenAI
import logging
from env_config import read_env_config, set_env
from os import environ
import time
from threading import Lock


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

def safe_min(a: Any, b: Any) -> Any:
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)

def safe_max(a: Any, b: Any) -> Any:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)

class UsageStats:
    def __init__(self) -> None:
        self.start = time.time()
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.total_tokens = 0
        self.end = None
        self.duration = 0
        self.calls = 0

    def __add__(self, other: 'UsageStats') -> 'UsageStats':
        stats = UsageStats()
        stats.start = safe_min(self.start, other.start)
        stats.end = safe_max(self.end, other.end)
        stats.completion_tokens = self.completion_tokens + other.completion_tokens
        stats.prompt_tokens = self.prompt_tokens + other.prompt_tokens
        stats.total_tokens = self.total_tokens + other.total_tokens
        stats.duration = self.duration + other.duration
        stats.calls = self.calls + other.calls
        return stats

class StatsCompleter(ABC):
    def __init__(self, create_func):
        self.create_func = create_func
        self.stats = None
        self.lock = Lock()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        response = self.create_func(*args, **kwds)
        self.lock.acquire()
        try:
            if not self.stats:
                self.stats = UsageStats()
            self.stats.completion_tokens += response.usage.completion_tokens
            self.stats.prompt_tokens += response.usage.prompt_tokens
            self.stats.total_tokens += response.usage.total_tokens
            self.stats.calls += 1
            return response
        finally:
            self.lock.release()
    
    def get_stats_and_reset(self) -> UsageStats:
        self.lock.acquire()
        try:
            end = time.time()
            stats = self.stats
            if stats:
                stats.end = end
                stats.duration = end - self.stats.start
                self.stats = None
            return stats
        finally:
            self.lock.release()

class ChatCompleter(StatsCompleter):
    def __init__(self, client):
        super().__init__(client.chat.completions.create)

class CompletionsCompleter(StatsCompleter):
    def __init__(self, client):
        super().__init__(client.completions.create)
