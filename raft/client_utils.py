from abc import ABC
from typing import Any
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from openai import AzureOpenAI, OpenAI
import logging
from env_config import read_env_config, set_env
from os import environ, getenv
import time
from threading import Lock
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.identity import get_bearer_token_provider


logger = logging.getLogger("client_utils")

def build_openai_client(env_prefix : str = "COMPLETION", **kwargs: Any) -> OpenAI:
    """
    Build OpenAI client based on the environment variables.
    """

    kwargs = _remove_empty_values(kwargs)
    env = read_env_config(env_prefix)
    with set_env(**env):
        if is_azure():
            auth_args = _get_azure_auth_client_args()
            client = AzureOpenAI(**auth_args, **kwargs)
        else:
            client = OpenAI(**kwargs)
        return client

def build_langchain_embeddings(**kwargs: Any) -> OpenAIEmbeddings:
    """
    Build OpenAI embeddings client based on the environment variables.
    """

    kwargs = _remove_empty_values(kwargs)
    env = read_env_config("EMBEDDING")
    with set_env(**env):
        if is_azure():
            auth_args = _get_azure_auth_client_args()
            client = AzureOpenAIEmbeddings(**auth_args, **kwargs)
        else:
            client = OpenAIEmbeddings(**kwargs)
        return client

def _remove_empty_values(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}

def _get_azure_auth_client_args() -> dict:
    """Handle Azure OpenAI Keyless, Managed Identity and Key based authentication
    https://techcommunity.microsoft.com/t5/microsoft-developer-community/using-keyless-authentication-with-azure-openai/ba-p/4111521
    """
    client_args = {}
    if getenv("AZURE_OPENAI_KEY"):
        logger.info("Using Azure OpenAI Key based authentication")
        client_args["api_key"] = getenv("AZURE_OPENAI_KEY")
    else:
        if client_id := getenv("AZURE_OPENAI_CLIENT_ID"):
            # Authenticate using a user-assigned managed identity on Azure
            logger.info("Using Azure OpenAI Managed Identity Keyless authentication")
            azure_credential = ManagedIdentityCredential(client_id=client_id)
        else:
            # Authenticate using the default Azure credential chain
            logger.info("Using Azure OpenAI Default Azure Credential Keyless authentication")
            azure_credential = DefaultAzureCredential()

        client_args["azure_ad_token_provider"] = get_bearer_token_provider(
            azure_credential, "https://cognitiveservices.azure.com/.default")
    client_args["api_version"] = getenv("AZURE_OPENAI_API_VERSION") or "2024-02-15-preview"
    client_args["azure_endpoint"] = getenv("AZURE_OPENAI_ENDPOINT")
    client_args["azure_deployment"] = getenv("AZURE_OPENAI_DEPLOYMENT")
    return client_args

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
