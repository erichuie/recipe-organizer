
from logging.config import dictConfig

def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": "src/logs/recipe_organizer_api.log",  # Log file name
                "maxBytes": 5 * 1024 * 1024,  # 5MB per log file
                "backupCount": 3,  # Keep 3 backups
            },
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["file", "console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["file", "console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    dictConfig(logging_config)