import logging.config


def set_logger():
    """
    Configure and initialize the logging system.

    This function sets up a logging configuration with the following:
    - Console handler that outputs to stdout
    - Rotating file handler that writes to 'logs/api.log' with 10MB max file size and 10 backup files
    - Root logger level set to INFO
    - Custom formatter that includes timestamp, log level, module, function name and message

    Returns:
        None
    """
    log_path = 'logs/api.log'
    dict_log_config = {
        "version": 1,
        "handlers": {
            "consoleHandler": {
                "class": "logging.StreamHandler",
                "formatter": "myFormatter",
                "stream": "ext://sys.stdout"
            },
            "RotatingFileHandler": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_path,
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 10,
                "formatter": "myFormatter"
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ["consoleHandler", "RotatingFileHandler"]
        },
        "formatters": {
            "myFormatter": {
                "format": "%(asctime)s:%(levelname)s in %(module)s:%(funcName)s: %(message)s"
            }
        }
    }
    logging.config.dictConfig(dict_log_config)
