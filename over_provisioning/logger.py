import logging

logging.basicConfig(level=logging.INFO)

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def get_logger():
    logger = logging.getLogger(__name__)
    return logger
