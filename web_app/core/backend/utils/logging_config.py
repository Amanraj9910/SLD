"""
Logging configuration for SLD Processing API
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/app.log)
        log_format: Custom log format string
        enable_console: Enable console logging
        enable_file: Enable file logging
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    
    # Set default log file
    if log_file is None:
        log_file = "logs/app.log"
    
    # Create logs directory
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set default log format
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_specific_loggers(log_level)
    
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file}")

def configure_specific_loggers(log_level: str):
    """Configure specific loggers for different modules"""
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # Set our application loggers
    app_loggers = [
        "main",
        "api.component_detection",
        "api.text_detection", 
        "api.annotation",
        "services.component_service",
        "services.text_service",
        "services.annotation_service"
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

class StructuredLogger:
    """Structured logger for better log analysis"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_request(self, method: str, path: str, status_code: int, duration: float):
        """Log HTTP request"""
        self.logger.info(
            f"HTTP {method} {path} - {status_code} - {duration:.3f}s",
            extra={
                "event_type": "http_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration": duration
            }
        )
    
    def log_component_detection(self, image_path: str, detections_count: int, processing_time: float):
        """Log component detection event"""
        self.logger.info(
            f"Component detection completed - {detections_count} components found in {processing_time:.3f}s",
            extra={
                "event_type": "component_detection",
                "image_path": image_path,
                "detections_count": detections_count,
                "processing_time": processing_time
            }
        )
    
    def log_text_detection(self, document_path: str, text_elements_count: int, processing_time: float):
        """Log text detection event"""
        self.logger.info(
            f"Text detection completed - {text_elements_count} text elements found in {processing_time:.3f}s",
            extra={
                "event_type": "text_detection",
                "document_path": document_path,
                "text_elements_count": text_elements_count,
                "processing_time": processing_time
            }
        )
    
    def log_annotation_operation(self, operation: str, project_name: str, annotations_count: int):
        """Log annotation operation"""
        self.logger.info(
            f"Annotation {operation} - Project: {project_name}, Annotations: {annotations_count}",
            extra={
                "event_type": "annotation_operation",
                "operation": operation,
                "project_name": project_name,
                "annotations_count": annotations_count
            }
        )
    
    def log_error(self, error_type: str, error_message: str, **kwargs):
        """Log error with context"""
        self.logger.error(
            f"Error: {error_type} - {error_message}",
            extra={
                "event_type": "error",
                "error_type": error_type,
                "error_message": error_message,
                **kwargs
            }
        )

class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = StructuredLogger("middleware.request")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            import time
            start_time = time.time()
            
            # Capture response
            status_code = 500  # Default to error
            
            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                # Log request
                duration = time.time() - start_time
                method = scope["method"]
                path = scope["path"]
                
                self.logger.log_request(method, path, status_code, duration)
        else:
            await self.app(scope, receive, send)

# Performance logging decorator
def log_performance(operation_name: str):
    """Decorator to log function performance"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Error logging utilities
def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """Log exception with full traceback"""
    import traceback
    
    error_msg = f"Exception in {context}: {type(exc).__name__}: {exc}"
    logger.error(error_msg, exc_info=True)
    
    # Also log the full traceback
    tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.debug(f"Full traceback:\n{tb_str}")

def setup_uvicorn_logging():
    """Setup Uvicorn logging configuration"""
    uvicorn_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - \"%(request_line)s\" %(status_code)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }
    
    return uvicorn_config

if __name__ == "__main__":
    # Test logging setup
    setup_logging(log_level="DEBUG")
    
    logger = get_logger(__name__)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test structured logger
    structured_logger = StructuredLogger("test")
    structured_logger.log_request("GET", "/api/test", 200, 0.123)
    structured_logger.log_component_detection("test.jpg", 5, 1.234)
    structured_logger.log_error("TestError", "This is a test error", context="testing")
    
    print("Logging test completed")
