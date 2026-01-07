import os
import logging
from logging.handlers import RotatingFileHandler

# Logging configuration
LOG_LEVEL = os.environ.get("RAG_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log directory and file settings
LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "rag_app.log")
LOG_MAX_BYTES = int(os.environ.get("RAG_LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10 MB default
LOG_BACKUP_COUNT = int(os.environ.get("RAG_LOG_BACKUP_COUNT", 5))  # Keep 5 backup files

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT
)

# Create file handler with rotation
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
    encoding='utf-8'
)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

# Add file handler to root logger so all modules use it
logging.getLogger().addHandler(file_handler)

# Application logger
logger = logging.getLogger("rag_app")
logger.info(f"Logging initialized. Log file: {LOG_FILE}")

DATA_DIR = os.path.join(os.getcwd(), "data")
DEFAULT_INDEX_PATH = os.path.join(DATA_DIR, "index.joblib")

# LLM provider selection: 'openai', 'local', 'gpt4all', or 'simple'
LLM_PROVIDER = os.environ.get("RAG_LLM_PROVIDER", "simple")  # Default to simple for offline use
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Request limits
MAX_QUERY_LENGTH = int(os.environ.get("RAG_MAX_QUERY_LENGTH", "500"))
MAX_RESULTS_PER_PAGE = int(os.environ.get("RAG_MAX_RESULTS_PER_PAGE", "100"))
DEFAULT_RESULTS_PER_PAGE = int(os.environ.get("RAG_DEFAULT_RESULTS_PER_PAGE", "10"))

# Timeouts
OPENAI_TIMEOUT = int(os.environ.get("RAG_OPENAI_TIMEOUT", "30"))
