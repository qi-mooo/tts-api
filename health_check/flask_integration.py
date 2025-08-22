"""
Flask集成模块

将健康检查功能集成到Flask应用中
"""

from flask import Flask, request, g
import time
import functools
from typing import Optional
import logging
from .health_monitor import health_monitor
from .health_controller import health_controller


class HealthCheckMiddleware:
    """健康检查中间件"""
    
    def __init__(self, app: Optional[Flask] = None):
        """
        初始化健康检查中间件
        
        Args:
            app: Flask应用实例
        """
        self.logger = logging.getLogger(__name__)
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化Flask应用
        
        Args:
            app: Flask应用实例
        """
        # 注册健康检查蓝图
        health_controller.register_with_app(app)
        
        # 注册请求钩子
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
        
        # 注册错误处理器
        app.errorhandler(Exception)(self._handle_exception)
        
        self.logger.info("健康检查中间件已初始化")
    
    def _before_request(self):
        """请求开始前的处理"""
        # 记录请求开始时间
        g.request_start_time = time.time()
        
        # 增加活跃请求计数
        health_monitor.increment_active_requests()
        
        # 设置请求ID（如果有的话）
        request_id = request.headers.get('X-Request-ID')
        if request_id:
            g.request_id = request_id
    
    def _after_request(self, response):
        """请求结束后的处理"""
        # 减少活跃请求计数
        health_monitor.decrement_active_requests()
        
        # 记录请求处理时间
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            
            # 如果是API请求，记录性能日志
            if request.path.startswith('/api'):
                self.logger.info(f"API请求完成: {request.path}, 耗时: {duration:.3f}s")
        
        return response
    
    def _teardown_request(self, exception):
        """请求清理"""
        if exception:
            # 记录错误
            health_monitor.record_error()
            self.logger.error(f"请求异常: {exception}")
    
    def _handle_exception(self, error):
        """全局异常处理"""
        # 记录错误到健康监控器
        health_monitor.record_error()
        
        # 记录详细错误日志
        self.logger.error(f"未处理的异常: {error}", exc_info=True)
        
        # 返回错误响应
        from flask import jsonify
        return jsonify({
            'error': 'Internal server error',
            'message': str(error)
        }), 500


def monitor_cache_operations(cache_instance):
    """
    监控缓存操作的装饰器工厂
    
    Args:
        cache_instance: 缓存实例
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 更新缓存统计
            if hasattr(cache_instance, 'current_size'):
                health_monitor.update_cache_stats(cache_instance.current_size)
            
            return result
        return wrapper
    return decorator


def setup_health_monitoring(app: Flask, cache_instance=None, app_version: str = "1.0.0"):
    """
    设置健康监控
    
    Args:
        app: Flask应用实例
        cache_instance: 缓存实例（可选）
        app_version: 应用版本号
    """
    # 设置应用版本
    health_monitor.app_version = app_version
    
    # 初始化健康检查中间件
    middleware = HealthCheckMiddleware(app)
    
    # 如果提供了缓存实例，监控缓存操作
    if cache_instance:
        # 装饰缓存的add方法
        if hasattr(cache_instance, 'add'):
            original_add = cache_instance.add
            
            @functools.wraps(original_add)
            def monitored_add(*args, **kwargs):
                result = original_add(*args, **kwargs)
                health_monitor.update_cache_stats(
                    getattr(cache_instance, 'current_size', 0)
                )
                return result
            
            cache_instance.add = monitored_add
        
        # 装饰缓存的combine方法
        if hasattr(cache_instance, 'combine'):
            original_combine = cache_instance.combine
            
            @functools.wraps(original_combine)
            def monitored_combine(*args, **kwargs):
                result = original_combine(*args, **kwargs)
                # 记录缓存命中或未命中
                hit = result is not None
                health_monitor.update_cache_stats(
                    getattr(cache_instance, 'current_size', 0),
                    hit=hit
                )
                return result
            
            cache_instance.combine = monitored_combine
    
    logging.getLogger(__name__).info("健康监控已设置完成")
    return middleware