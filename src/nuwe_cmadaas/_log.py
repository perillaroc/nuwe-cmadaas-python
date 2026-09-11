import logging


def get_logger(name):
    try:
        from loguru import logger
        return logger
    except ImportError:
        logger = logging.getLogger(name)
    return logger

logger = get_logger(__name__)
