from google.cloud import logging


def log_message(message):
    logging_client = logging.Client()
    logger = logging_client.logger("compute-log")
    logger.log_text(message)
