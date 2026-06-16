import os
import logging

from .logging_config import configure_logging

configure_logging()

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "backend", ".env"))
except ImportError:
    pass

logger = logging.getLogger("agile_agent")
logger.info("Backend package initialized — logging configured")