import logging
import logging.config
import os
import yaml

def log_setup():
    """
    Set up basic console logging. Root logger level can be set with ROOT_LOG_LEVEL environment variable.
    """

    # Load the config file
    with open(os.getenv('LOGGING_CONFIG', 'logging.yaml'), 'rt') as f:
        config = yaml.safe_load(f.read())

    # Configure the logging module with the config file
    logging.config.dictConfig(config)
