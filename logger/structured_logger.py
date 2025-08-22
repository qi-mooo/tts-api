"""
结构化日志系统模块

提供多级别日志记录、日志轮转、性能监控和审计日志功能
"""

import logging
import logging.handlers
import json
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import threading
import uuid


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化结构化日志记录器
        
        Args:
            name: 日志记录器名称
            config: 日志配置字典
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)
        self._setup_logger()
        self._request_local = threading.local()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 设置日志级别
        level = getattr(logging, self.config.get('level', 'INFO').upper())
        self.logger.setLevel(level)
        
        # 创建日志目录
        log_file = self.config.get('file', 'logs/app.log')
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置轮转文件处理器
        max_bytes = self._parse_size(self.config.get('max_size', '10MB'))
        backup_count = self.config.get('backup_count', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 设置控制台处理器
        console_handler = logging.StreamHandler()
        
        # 设置格式化器
        formatter = StructuredFormatter()
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _get_request_id(self) -> str:
        """获取或生成请求ID"""
        if not hasattr(self._request_local, 'request_id'):
            self._request_local.request_id = str(uuid.uuid4())[:8]
        return self._request_local.request_id
    
    def set_request_id(self, request_id: str):
        """设置请求ID"""
        self._request_local.request_id = request_id
    
    def _create_log_record(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """创建结构化日志记录"""
        record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'module': self.name,
            'message': message,
            'request_id': self._get_request_id()
        }
        
        # 添加额外字段
        record.update(kwargs)
        
        return record
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        record = self._create_log_record('DEBUG', message, **kwargs)
        self.logger.debug(json.dumps(record, ensure_ascii=False))
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        record = self._create_log_record('INFO', message, **kwargs)
        self.logger.info(json.dumps(record, ensure_ascii=False))
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        record = self._create_log_record('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(record, ensure_ascii=False))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """记录错误日志"""
        record = self._create_log_record('ERROR', message, **kwargs)
        
        if error:
            record['error_type'] = type(error).__name__
            record['error_message'] = str(error)
            record['traceback'] = traceback.format_exc()
        
        self.logger.error(json.dumps(record, ensure_ascii=False))
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """记录严重错误日志"""
        record = self._create_log_record('CRITICAL', message, **kwargs)
        
        if error:
            record['error_type'] = type(error).__name__
            record['error_message'] = str(error)
            record['traceback'] = traceback.format_exc()
        
        self.logger.critical(json.dumps(record, ensure_ascii=False))
    
    def performance(self, operation: str, duration: float, **kwargs):
        """记录性能监控日志"""
        record = self._create_log_record('INFO', f'Performance: {operation}', **kwargs)
        record['operation'] = operation
        record['duration_ms'] = round(duration * 1000, 2)
        record['log_type'] = 'performance'
        
        self.logger.info(json.dumps(record, ensure_ascii=False))
    
    def audit(self, action: str, user: str, **kwargs):
        """记录审计日志"""
        record = self._create_log_record('INFO', f'Audit: {action}', **kwargs)
        record['action'] = action
        record['user'] = user
        record['log_type'] = 'audit'
        
        self.logger.info(json.dumps(record, ensure_ascii=False))


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        """格式化日志记录"""
        try:
            # 尝试解析为 JSON
            log_data = json.loads(record.getMessage())
            return json.dumps(log_data, ensure_ascii=False, indent=None)
        except (json.JSONDecodeError, ValueError):
            # 如果不是 JSON，使用标准格式
            return super().format(record)


class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, logger: StructuredLogger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.performance(self.operation, duration, **self.kwargs)


# 全局日志管理器
class LoggerManager:
    """日志管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.loggers = {}
            self.default_config = {
                'level': 'INFO',
                'file': 'logs/app.log',
                'max_size': '10MB',
                'backup_count': 5
            }
            self.initialized = True
    
    def get_logger(self, name: str, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
        """获取或创建日志记录器"""
        if name not in self.loggers:
            logger_config = config or self.default_config
            self.loggers[name] = StructuredLogger(name, logger_config)
        return self.loggers[name]
    
    def update_config(self, config: Dict[str, Any]):
        """更新默认配置"""
        self.default_config.update(config)
        # 重新配置所有现有的日志记录器
        for logger in self.loggers.values():
            logger.config.update(config)
            logger._setup_logger()


# 便捷函数
def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """获取结构化日志记录器"""
    manager = LoggerManager()
    return manager.get_logger(name, config)


def performance_timer(logger: StructuredLogger, operation: str, **kwargs) -> PerformanceTimer:
    """创建性能计时器"""
    return PerformanceTimer(logger, operation, **kwargs)