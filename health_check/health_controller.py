"""
健康检查控制器

提供健康检查相关的API端点和控制逻辑
"""

from flask import Blueprint, jsonify, request
import asyncio
from typing import Dict, Any
import logging
from .health_monitor import health_monitor


class HealthController:
    """健康检查控制器"""
    
    def __init__(self):
        """初始化健康检查控制器"""
        self.logger = logging.getLogger(__name__)
        self.blueprint = self._create_blueprint()
    
    def _create_blueprint(self) -> Blueprint:
        """创建Flask蓝图"""
        bp = Blueprint('health', __name__, url_prefix='/health')
        
        # 注册路由
        bp.add_url_rule('', 'health_check', self.health_check, methods=['GET'])
        bp.add_url_rule('/detailed', 'detailed_health', self.detailed_health, methods=['GET'])
        bp.add_url_rule('/ready', 'readiness_check', self.readiness_check, methods=['GET'])
        bp.add_url_rule('/live', 'liveness_check', self.liveness_check, methods=['GET'])
        
        return bp
    
    def health_check(self):
        """
        基本健康检查端点
        
        Returns:
            JSON响应包含基本健康状态信息
        """
        try:
            # 获取健康状态摘要
            health_summary = health_monitor.get_health_summary()
            
            # 根据状态返回相应的HTTP状态码
            status_code = self._get_http_status_code(health_summary['status'])
            
            return jsonify(health_summary), status_code
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': 'Health check failed',
                'detail': str(e)
            }), 503
    
    def detailed_health(self):
        """
        详细健康检查端点
        
        Returns:
            JSON响应包含详细的系统状态信息
        """
        try:
            # 检查是否需要强制刷新
            force_refresh = request.args.get('refresh', 'false').lower() == 'true'
            
            # 获取详细系统状态
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                system_status = loop.run_until_complete(
                    health_monitor.get_system_status(force_refresh=force_refresh)
                )
            finally:
                loop.close()
            
            # 根据状态返回相应的HTTP状态码
            status_code = self._get_http_status_code(system_status.status)
            
            return jsonify(system_status.to_dict()), status_code
            
        except Exception as e:
            self.logger.error(f"详细健康检查失败: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': 'Detailed health check failed',
                'detail': str(e)
            }), 503
    
    def readiness_check(self):
        """
        就绪性检查端点
        
        检查应用是否准备好接收流量
        
        Returns:
            JSON响应表示应用就绪状态
        """
        try:
            # 获取健康状态
            health_summary = health_monitor.get_health_summary()
            
            # 检查关键服务是否可用
            is_ready = (
                health_summary['status'] in ['healthy', 'degraded'] and
                health_summary['edge_tts_available']
            )
            
            response = {
                'ready': is_ready,
                'status': health_summary['status'],
                'edge_tts_available': health_summary['edge_tts_available'],
                'timestamp': health_summary['timestamp']
            }
            
            status_code = 200 if is_ready else 503
            return jsonify(response), status_code
            
        except Exception as e:
            self.logger.error(f"就绪性检查失败: {e}")
            return jsonify({
                'ready': False,
                'error': 'Readiness check failed',
                'detail': str(e)
            }), 503
    
    def liveness_check(self):
        """
        存活性检查端点
        
        检查应用是否仍在运行
        
        Returns:
            JSON响应表示应用存活状态
        """
        try:
            # 简单的存活性检查
            response = {
                'alive': True,
                'timestamp': health_monitor.get_health_summary()['timestamp'],
                'uptime_seconds': health_monitor.get_health_summary()['uptime_seconds']
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            self.logger.error(f"存活性检查失败: {e}")
            return jsonify({
                'alive': False,
                'error': 'Liveness check failed',
                'detail': str(e)
            }), 503
    
    def _get_http_status_code(self, health_status: str) -> int:
        """
        根据健康状态获取HTTP状态码
        
        Args:
            health_status: 健康状态字符串
            
        Returns:
            int: HTTP状态码
        """
        status_mapping = {
            'healthy': 200,
            'degraded': 200,  # 降级但仍可用
            'unhealthy': 503
        }
        return status_mapping.get(health_status, 503)
    
    def register_with_app(self, app):
        """
        将健康检查蓝图注册到Flask应用
        
        Args:
            app: Flask应用实例
        """
        app.register_blueprint(self.blueprint)
        self.logger.info("健康检查端点已注册")


# 全局健康检查控制器实例
health_controller = HealthController()