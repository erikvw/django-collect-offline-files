from edc_base.logging import verbose_formatter, file_handler
from edc_sync_files.loggers import loggers

file_handler['filename'] = '/tmp/edc_sync_files.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': verbose_formatter,
    },
    'handlers': {
        'file': file_handler
    },
    'loggers': loggers,
}
