import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")
LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Set up basic config (this affects root logger)
logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)

# File handler for writing logs to disk
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)
file_handler.setLevel(LOGGING_LEVEL)
file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
logging.getLogger("").addHandler(file_handler)

# Stream handler for printing logs to stdout
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(LOGGING_LEVEL)
stream_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
logging.getLogger("").addHandler(stream_handler)