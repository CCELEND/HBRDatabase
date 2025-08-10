
import logging
import logging.handlers
import os
from typing import Optional, Dict

# 单例模式
class AdvancedLogger:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 name: str = "root",
                 log_level: int = logging.INFO,  # INFO
                 log_dir: str = "日志",
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)  # 设置logger的最低记录级别
        
        # 防止重复添加处理器
        if self.logger.handlers:
            return
            
        # 通用日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s [%(pathname)s line:%(lineno)d] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.INFO)
        # console_handler.setFormatter(formatter)
        # self.logger.addHandler(console_handler)
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 为不同级别创建不同的文件处理器
        self._setup_level_handlers(log_dir, max_bytes, backup_count, formatter)
    
    def _setup_level_handlers(self, log_dir: str, max_bytes: int, backup_count: int, formatter: logging.Formatter):
        """为不同日志级别设置不同的文件处理器"""
        level_files = {
            logging.DEBUG: "debug.log",      # 记录DEBUG
            logging.INFO: "info.log",        # 记录INFO
            logging.WARNING: "warning.log",  # 记录WARNING
            logging.ERROR: "error.log",      # 记录ERROR
            logging.CRITICAL: "critical.log" # 记录CRITICAL
        }
        
        # 为每个级别创建处理器
        for level, filename in level_files.items():
            file_path = os.path.join(log_dir, filename)
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            handler.setLevel(level)  # 设置处理器接受的最低级别
            handler.setFormatter(formatter)

            # 通过默认参数捕获当前level的值，避免闭包陷阱
            handler.addFilter(lambda record, level=level: record.levelno == level)

            self.logger.addHandler(handler)
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        if name:
            return cls(name=name).logger
        return cls().logger

# 默认日志器
default_logger = AdvancedLogger.get_logger()
