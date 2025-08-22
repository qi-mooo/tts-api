"""
Flask 集成模块 - 重启控制器与Flask应用的集成

提供请求跟踪中间件和重启相关的路由
"""

import uuid
import time
from datetime import datetime
from flask import Flask, request, g, jsonify, Blueprint
from functools import wraps

from .restart_controller import restart_controller
from logger.structured_logger import get_logger
from error_handler.error_handler import ErrorHandler


class RestartMiddleware:
    """重启中间件 - 跟踪活跃请求和重启状态"""
    
    def __init__(self, app: Flask = None):
        """初始化中间件"""
        self.logger = get_logger('restart_middleware')
        self.error_handler = ErrorHandler(self.logger.logger)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """初始化Flask应用"""
        # 注册请求前处理器
        app.before_request(self._before_request)
        
        # 注册请求后处理器
        app.after_request(self._after_request)
        
        # 注册异常处理器
        app.teardown_request(self._teardown_request)
        
        # 注册重启相关路由
        restart_bp = self._create_restart_blueprint()
        app.register_blueprint(restart_bp)
        
        self.logger.info("重启中间件已初始化")
    
    def _before_request(self):
        """请求前处理 - 注册活跃请求"""
        # 检查系统是否正在重启
        if restart_controller.is_restarting:
            return jsonify({
                'error': '系统正在重启中，请稍后再试',
                'code': 'SYSTEM_RESTARTING',
                'restart_status': restart_controller.get_restart_status()
            }), 503
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        g.request_id = request_id
        g.request_start_time = time.time()
        
        # 注册活跃请求
        restart_controller.register_request(
            request_id=request_id,
            endpoint=request.endpoint or request.path,
            remote_addr=request.remote_addr or '',
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # 添加请求ID到响应头
        g.add_request_id_header = True
    
    def _after_request(self, response):
        """请求后处理 - 注销活跃请求"""
        if hasattr(g, 'request_id'):
            # 注销活跃请求
            restart_controller.unregister_request(g.request_id)
            
            # 添加请求ID到响应头
            if hasattr(g, 'add_request_id_header'):
                response.headers['X-Request-ID'] = g.request_id
            
            # 记录请求处理时间
            if hasattr(g, 'request_start_time'):
                duration = time.time() - g.request_start_time
                response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    def _teardown_request(self, exception):
        """请求清理 - 确保请求被注销"""
        if hasattr(g, 'request_id'):
            restart_controller.unregister_request(g.request_id)
    
    def _create_restart_blueprint(self) -> Blueprint:
        """创建重启相关的路由蓝图"""
        bp = Blueprint('restart', __name__, url_prefix='/api/restart')
        
        @bp.route('/status', methods=['GET'])
        def get_restart_status():
            """获取重启状态"""
            try:
                status = restart_controller.get_restart_status()
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                return self.error_handler.handle_error(e)
        
        @bp.route('/request', methods=['POST'])
        def request_restart():
            """请求重启"""
            try:
                data = request.get_json() or {}
                
                # 这里应该添加权限验证
                # 暂时使用简单的用户标识
                user = data.get('user', 'anonymous')
                reason = data.get('reason', '手动重启')
                force = data.get('force', False)
                config_reload = data.get('config_reload', True)
                timeout = data.get('timeout', 30)
                
                result = restart_controller.request_restart(
                    user=user,
                    reason=reason,
                    force=force,
                    config_reload=config_reload,
                    timeout=timeout
                )
                
                return jsonify(result)
                
            except Exception as e:
                return self.error_handler.handle_error(e)
        
        @bp.route('/cancel', methods=['POST'])
        def cancel_restart():
            """取消重启"""
            try:
                data = request.get_json() or {}
                user = data.get('user', 'anonymous')
                
                result = restart_controller.cancel_restart(user)
                return jsonify(result)
                
            except Exception as e:
                return self.error_handler.handle_error(e)
        
        @bp.route('/history', methods=['GET'])
        def get_restart_history():
            """获取重启历史"""
            try:
                limit = request.args.get('limit', 10, type=int)
                history = restart_controller.get_restart_history(limit)
                
                return jsonify({
                    'success': True,
                    'data': history,
                    'total': len(history)
                })
                
            except Exception as e:
                return self.error_handler.handle_error(e)
        
        return bp


def require_restart_permission(f):
    """重启权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 这里应该实现实际的权限检查
        # 暂时允许所有请求
        return f(*args, **kwargs)
    return decorated_function


# 创建全局中间件实例
restart_middleware = RestartMiddleware()