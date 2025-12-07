import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logger(name: str = "arr_cleaner", level: int = logging.INFO) -> logging.Logger:
    """Setup rich logger for the application"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Add rich handler
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    rich_handler.setLevel(level)

    formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(formatter)

    logger.addHandler(rich_handler)

    return logger


# Global logger instance
logger = setup_logger()
