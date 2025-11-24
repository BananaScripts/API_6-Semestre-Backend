import logging
from logging.handlers import RotatingFileHandler


LOG_FILE = "chatbot.log"


# Rotating handler para limitar tamanho de log
handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)


logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


# helper
def log_info(msg):
    logger.info(msg)


def log_error(msg):
    logger.error(msg)