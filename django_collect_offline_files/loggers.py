file_handler = {
    "level": "DEBUG",
    "class": "logging.FileHandler",
    "filename": "/tmp/django_collect_offline_files.log",
    "formatter": "verbose",
}

verbose_formatter = {
    "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
}


loggers = {
    "django_collect_offline_files": {
        "handlers": ["file"],
        "level": "DEBUG",
        "propagate": True,
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": verbose_formatter},
    "handlers": {"file": file_handler},
    "loggers": loggers,
}
