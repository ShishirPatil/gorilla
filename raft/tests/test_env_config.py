import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from env_config import read_env_config

def test_openai_simple():
    """
    Simple OpenAI only env vars. Non OpenAI related env vars are ignored.
    """

    env = {
        'HOSTNAME': 'localhost',
        'OPENAI_API_KEY': '<key_1>',
    }

    config = read_env_config("COMPLETION", env)

    assert 'HOSTNAME' not in config
    assert config['OPENAI_API_KEY'] == '<key_1>'


def test_azure_simple():
    """
    Simple Azure OpenAI only env vars. Non OpenAI related env vars are ignored.
    """

    env = {
        'HOSTNAME': 'localhost',
        'AZURE_OPENAI_ENDPOINT': '<endpoint_1>',
        'AZURE_OPENAI_API_KEY': '<key_1>',
        'OPENAI_API_VERSION': '<version_1>',
    }

    config = read_env_config("COMPLETION", env)

    assert 'HOSTNAME' not in config
    assert config['AZURE_OPENAI_ENDPOINT'] == '<endpoint_1>'
    assert config['AZURE_OPENAI_API_KEY'] == '<key_1>'
    assert config['OPENAI_API_VERSION'] == '<version_1>'

def test_azure_override():
    """
    Test that the completion config overrides the base config and that the embedding config doesn't 
    interfere and that non OpenAI related env vars are ignored.
    """

    env = {
        'HOSTNAME': 'localhost',
        'AZURE_OPENAI_ENDPOINT': '<endpoint_1>',
        'AZURE_OPENAI_API_KEY': '<key_1>',
        'OPENAI_API_VERSION': '<version_1>',
        'COMPLETION_AZURE_OPENAI_ENDPOINT': '<endpoint_2>',
        'COMPLETION_AZURE_OPENAI_API_KEY': '<key_2>',
        'EMBEDDING_AZURE_OPENAI_ENDPOINT': '<endpoint_3>',
        'EMBEDDING_AZURE_OPENAI_API_KEY': '<key_3>',
    }

    comp_config = read_env_config("COMPLETION", env)
    assert 'HOSTNAME' not in comp_config
    assert comp_config['AZURE_OPENAI_ENDPOINT'] == '<endpoint_2>'
    assert comp_config['AZURE_OPENAI_API_KEY'] == '<key_2>'
    assert comp_config['OPENAI_API_VERSION'] == '<version_1>'

    emb_config = read_env_config("EMBEDDING", env)
    assert 'HOSTNAME' not in emb_config
    assert emb_config['AZURE_OPENAI_ENDPOINT'] == '<endpoint_3>'
    assert emb_config['AZURE_OPENAI_API_KEY'] == '<key_3>'
    assert emb_config['OPENAI_API_VERSION'] == '<version_1>'

def test_openai_override():
    """
    Test that the completion config overrides the base config and that the embedding config doesn't 
    interfere and that non OpenAI related env vars are ignored.
    """

    env = {
        'HOSTNAME': 'localhost',
        'OPENAI_ENDPOINT': '<endpoint_1>',
        'OPENAI_API_KEY': '<key_1>',
        'OPENAI_API_VERSION': '<version_1>',
        'COMPLETION_OPENAI_ENDPOINT': '<endpoint_2>',
        'COMPLETION_OPENAI_API_KEY': '<key_2>',
        'EMBEDDING_OPENAI_ENDPOINT': '<endpoint_3>',
        'EMBEDDING_OPENAI_API_KEY': '<key_3>',
    }

    comp_config = read_env_config("COMPLETION", env)
    assert 'HOSTNAME' not in comp_config
    assert comp_config['OPENAI_ENDPOINT'] == '<endpoint_2>'
    assert comp_config['OPENAI_API_KEY'] == '<key_2>'
    assert comp_config['OPENAI_API_VERSION'] == '<version_1>'

    emb_config = read_env_config("EMBEDDING", env)
    assert 'HOSTNAME' not in emb_config
    assert emb_config['OPENAI_ENDPOINT'] == '<endpoint_3>'
    assert emb_config['OPENAI_API_KEY'] == '<key_3>'
    assert emb_config['OPENAI_API_VERSION'] == '<version_1>'
