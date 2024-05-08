import contextlib
import os

# List of environment variables prefixes that are allowed to be used for configuration.
env_prefix_whitelist = [
    'OPENAI', 
    'AZURE_OPENAI'
]

def read_env_config(use_prefix: str, env: dict = os.environ) -> str:
    """
    Read whitelisted environment variables and return them in a dictionary.
    Overrides the whitelisted environment variable with ones prefixed with the given use_prefix if available.
    """
    config = {}
    for prefix in [None, use_prefix]:
        read_env_config_prefixed(prefix, config, env)
    return config

def read_env_config_prefixed(use_prefix: str, config: dict, env: dict = os.environ) -> str:
    """
    Read whitelisted environment variables prefixed with use_prefix and adds them to the dictionary 
    with use_prefix stripped.
    """
    use_prefix = format_prefix(use_prefix)
    for key in env:
        for env_prefix in env_prefix_whitelist:
            key_prefix = f"{use_prefix}{format_prefix(env_prefix)}"
            if key.startswith(key_prefix):
                striped_key = key.removeprefix(use_prefix)
                config[striped_key] = env[key]

def format_prefix(prefix: str) -> str:
    """
    Format the prefix to be used in the environment variable.
    """
    if prefix and len(prefix) > 0 and not prefix.endswith("_"):
        prefix = f"{prefix}_"
    if not prefix:
        prefix = ""
    return prefix


@contextlib.contextmanager
def set_env(**environ: dict[str, str]):
    """
    Temporarily set the process environment variables.
    Warning, this is not thread safe as the environment is updated for the whole process.

    >>> with set_env(PLUGINS_DIR='test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
