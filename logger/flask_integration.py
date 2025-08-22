"""
Flask 集成模块

将结构化日志系统集成到 Flask 应用中
"""

import time
import uuid
from flask import Flask, request, g
from functools import wraps
from typing import Optional

from .structured_logger import get_logger, StructuredLogger


class FlaskLoggerIntegration:
    """Flask 日志集成类"""
    
    def __init__(self, app: Optional[Flask] = None, config: Optional[dict] = None):
        self.app = app
        self.config = config or {}
        self.logger = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化 Flask 应用"""
        self.app = app
        
        # 获取日志配置
        log_config = app.config.get('LOGGING_CONFIG', self.config)
        
        # 创建应用日志记录器
        self.logger = get_logger('flask_app', log_config)
        
        # 注册请求钩子
        self._register_hooks()
        
        # 替换应用日志记录器
        app.logger.handlers.clear()
        app.logger = self.logger.logger
    
    def _register_hooks(self):
        """注册 Flask 请求钩子"""
        
        @self.app.before_request
        def before_request():
            """请求开始前的处理"""
            # 生成请求ID
            request_id = str(uuid.uuid4())[:8]
            g.request_id = request_id
            g.start_time = time.time()
            
            # 设置日志记录器的请求ID
            self.logger.set_request_id(request_id)
            
            # 记录请求开始日志
            self.logger.info(
                "Request started",
                method=request.method,
                path=request.path,
                remote_addr=request.remote_addr,
                user_agent=str(request.user_agent)
            )
        
        @self.app.after_request
        def after_request(response):
            """请求结束后的处理"""
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                
                # 记录请求完成日志
                self.logger.info(
                    "Request completed",
                    method=request.method,
                    path=request.path,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2)
                )
                
                # 记录性能日志
                self.logger.performance(
                    f"{request.method} {request.path}",
                    duration,
                    status_code=response.status_code
                )
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_exception(error):
            """全局异常处理"""
            self.logger.error(
                "Unhandled exception occurred",
                error=error,
                method=request.method,
                path=request.path,
                remote_addr=request.remote_addr
            )
            
            # 返回通用错误响应
            from flask import jsonify
            return jsonify({
                "error": "Internal server error",
                "request_id": getattr(g, 'request_id', 'unknown')
            }), 500


def log_function_call(operation_name: str = None):
    """函数调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('function_calls')
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                logger.debug(f"Function call started: {op_name}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.performance(op_name, duration)
                logger.debug(f"Function call completed: {op_name}")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function call failed: {op_name}",
                    error=e,
                    duration_ms=round(duration * 1000, 2)
                )
                raise
        
        return wrapper
    return decorator


def log_api_call(func):
    """API 调用日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger('api_calls')
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录成功的 API 调用
            logger.info(
                f"API call successful: {func.__name__}",
                endpoint=request.endpoint,
                method=request.method,
                duration_ms=round(duration * 1000, 2)
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # 记录失败的 API 调用
            logger.error(
                f"API call failed: {func.__name__}",
                error=e,
                endpoint=request.endpoint,
                method=request.method,
                duration_ms=round(duration * 1000, 2)
            )
            raise
    
    return wrapper