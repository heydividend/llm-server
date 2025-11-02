"""
Centralized logging configuration for Harvey backend services.
Provides consistent logging across all modules with proper formatting and rotation.
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Determine environment
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
IS_AZURE_VM = os.path.exists("/opt/harvey-backend")

# Log directory configuration
if IS_AZURE_VM:
    LOG_DIR = Path("/var/log/harvey")
else:
    LOG_DIR = Path("logs")

# Create log directory if it doesn't exist
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log levels by module
LOG_LEVELS = {
    "default": logging.INFO,
    "harvey_intelligence": logging.DEBUG if not IS_PRODUCTION else logging.INFO,
    "model_router": logging.INFO,
    "model_audit": logging.INFO,
    "dividend_strategies": logging.INFO,
    "ml_integration": logging.INFO,
    "llm_providers": logging.INFO,
    "azure_openai": logging.WARNING,  # Reduce Azure OpenAI verbosity
    "openai": logging.WARNING,  # Reduce OpenAI verbosity
    "httpx": logging.WARNING,  # Reduce HTTP client logs
    "urllib3": logging.WARNING,  # Reduce urllib3 logs
    "sqlalchemy": logging.WARNING,  # Reduce SQLAlchemy logs except errors
    "scheduler": logging.INFO,
    "alerts": logging.INFO,
    "feedback": logging.INFO,
}


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name for console output
        if not IS_PRODUCTION and sys.stderr.isatty():
            levelname = record.levelname
            record.levelname = f"{self.COLORS.get(levelname, '')}{levelname}{self.RESET}"
        
        # Format the message
        result = super().format(record)
        
        # Reset color after formatting
        if not IS_PRODUCTION and sys.stderr.isatty():
            record.levelname = record.levelname.replace(self.COLORS.get(record.levelname.strip(), ''), '').replace(self.RESET, '')
        
        return result


def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Set up a logger with consistent formatting and handlers.
    
    Args:
        name: Logger name (usually module name)
        level: Log level (defaults to LOG_LEVELS or INFO)
        log_file: Custom log file name (defaults to {name}.log)
        enable_console: Whether to log to console
        enable_file: Whether to log to file
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Don't reconfigure if already set up
    if logger.handlers:
        return logger
    
    # Set log level
    if level is None:
        level = LOG_LEVELS.get(name, LOG_LEVELS.get("default", logging.INFO))
    logger.setLevel(level)
    
    # Create formatters
    if IS_PRODUCTION:
        # Production: Structured logs for parsing
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Development: Readable colored logs
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        if not log_file:
            log_file = f"{name}.log"
        
        file_path = LOG_DIR / log_file
        
        # Use rotating file handler (10MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def setup_all_loggers():
    """
    Set up all Harvey service loggers with appropriate configurations.
    """
    # Main application logger
    setup_logger("harvey", logging.INFO, "harvey_main.log")
    
    # Service loggers
    services = [
        "harvey_intelligence",
        "model_router",
        "model_audit_service",
        "dividend_strategy_analyzer",
        "ml_integration",
        "azure_openai_client",
        "gemini_client",
        "llm_providers",
        "scheduler",
        "alert_service",
        "feedback_service",
        "document_processor",
        "portfolio_analyzer"
    ]
    
    for service in services:
        setup_logger(service, log_file=f"{service}.log")
    
    # API route loggers
    routes = [
        "harvey_status",
        "dividend_strategies",
        "chat_api",
        "portfolio_api",
        "alerts_api",
        "insights_api"
    ]
    
    for route in routes:
        setup_logger(route, logging.INFO, log_file=f"api_{route}.log")
    
    # Database logger (less verbose)
    setup_logger("database", logging.WARNING, "database.log")
    setup_logger("sqlalchemy.engine", logging.WARNING, "sqlalchemy.log", enable_console=False)
    
    # External library loggers (reduce noise)
    for lib in ["urllib3", "httpx", "openai", "azure", "google"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    # Create a startup log entry
    main_logger = logging.getLogger("harvey")
    main_logger.info("=" * 60)
    main_logger.info(f"Harvey Backend Starting - Environment: {'PRODUCTION' if IS_PRODUCTION else 'DEVELOPMENT'}")
    main_logger.info(f"Log Directory: {LOG_DIR}")
    main_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    main_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    # Ensure logger is set up
    if not logging.getLogger(name).handlers:
        setup_logger(name)
    
    return logging.getLogger(name)


# Initialize all loggers when module is imported
setup_all_loggers()