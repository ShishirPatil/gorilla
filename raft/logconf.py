import logging
import logging.config
import os
import yaml

def log_setup():
    """
    Set up basic console logging. Root logger level can be set with ROOT_LOG_LEVEL environment variable.
    """

    # Load the config file
    conf_path = os.getenv('LOGGING_CONFIG', None)
    if not conf_path:
        conf_path = os.path.dirname(__file__) + '/logging.yaml'
    with open(conf_path, 'rt') as f:
        config = yaml.safe_load(f.read())

    # Configure the logging module with the config file
    logging.config.dictConfig(config)

    install_default_record_field(logging, 'progress', '')


def install_default_record_field(logging, field, value):
    """
    Wraps the log record factory to add a default progress field value
    Required to avoid a KeyError when the progress field is not set
    Such as when logging from a different thread
    """
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        if not hasattr(record, field):
            record.progress = value
        return record

    logging.setLogRecordFactory(record_factory)
