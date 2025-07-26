import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'level': 'DEBUG',
            'filename': 'app.log',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'my_module': {  # Logger for a specific module
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    }
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)