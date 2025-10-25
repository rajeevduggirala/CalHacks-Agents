"""
Logger utility for Agentic Grocery project.
Uses rich for beautiful console output and structured logging.
"""

import logging
import sys
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

# Install rich traceback handler
install_rich_traceback(show_locals=True)

# Create console instance
console = Console()


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with rich handler for beautiful console output.
    
    Args:
        name: Name of the logger (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Add rich handler
    handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    
    return logger


def log_agent_message(agent_name: str, message: str, level: str = "info"):
    """
    Log a message with agent-specific formatting.
    
    Args:
        agent_name: Name of the agent logging the message
        message: Message to log
        level: Log level (info, warning, error, debug)
    """
    color_map = {
        "ChatAgent": "cyan",
        "RecipeAgent": "green",
        "GroceryAgent": "yellow"
    }
    color = color_map.get(agent_name, "white")
    console.print(f"[bold {color}][{agent_name}][/bold {color}] {message}")


def log_api_call(endpoint: str, status: str = "started"):
    """
    Log API call information.
    
    Args:
        endpoint: API endpoint being called
        status: Status of the call (started, completed, failed)
    """
    status_color = {
        "started": "blue",
        "completed": "green",
        "failed": "red"
    }
    color = status_color.get(status, "white")
    console.print(f"[{color}]API {status.upper()}: {endpoint}[/{color}]")

