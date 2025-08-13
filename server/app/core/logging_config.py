import logging
import sys

def setup_logging():
    """Setup application logging with industry best practices."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True
    )

def get_logger(name: str = __name__):
    """Get a logger instance."""
    return logging.getLogger(name)

# Initialize logging on import
setup_logging()