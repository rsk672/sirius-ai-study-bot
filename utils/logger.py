import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

class LoggerSingleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerSingleton, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        main_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        main_handler.setFormatter(formatter)
        root_logger.addHandler(main_handler)
        
        error_handler = RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        if os.getenv("ENV", "development") != "production":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            root_logger.addHandler(console_handler)
        
        logging.getLogger("uvicorn").propagate = True
        logging.getLogger("uvicorn.error").propagate = True
        logging.getLogger("uvicorn.access").propagate = True
        logging.getLogger("fastapi").propagate = True

    @staticmethod
    def get_logger(name: str = "app") -> logging.Logger:
        """Получить логгер с указанным именем"""
        return logging.getLogger(name)

logger = LoggerSingleton().get_logger()