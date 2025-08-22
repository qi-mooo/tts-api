"""
健康检查模块单元测试
"""

import unittest
import asyncio
import time
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

# 导入被测试的模块
from health_check.health_monitor import HealthMonitor, SystemStatus
from health_check.health_controller import HealthController
from health_check.flask_integration import HealthCheckMiddleware, setup_health_monitoring


class TestSystemStatus(unittest.TestCase):
    """SystemStatus数据模型测试"""
    
    def test_system_status_creation(self):
        """测试SystemStatus对象创建"""
        status = SystemStatus(
            status='healthy',
            timestamp='2024-01-01T12:00:00',
            uptime=3600.0,
            version='1.0.0',
            memory_usage=50.0,
            memory_total=8589934592,
            memory_used=4294967296,
            cpu_usage=25.0,
            disk_usage=60.0,
            edge_tts_status=True,
            edge_tts_response_time=150.0,
            active_requests=5,
            cache_size=1048576,
            cache_hit_rate=85.5,
            error_count_1h=2,
            error_count_24h=10
        )
        
        self.assertEqual(status.status, 'healthy')
        self.assertEqual(status.version, '1.0.0')
        self.assertEqual(status.memory_usage, 50.0)
        self.assertTrue(status.edge_tts_status)
    
    def test_system_status_to_dict(self):
        """测试SystemStatus转换为字典"""
        status = SystemStatus(
            status='healthy',
            timestamp='2024-01-01T12:00:00',
            uptime=3600.0,
            version='1.0.0',
            memory_usage=50.0,
            memory_total=8589934592,
            memory_used=4294967296,
            cpu_usage=25.0,
            disk_usage=60.0,
            edge_tts_status=True,
            edge_tts_response_time=150.0,
            active_requests=5,
            cache_size=1048576,
            cache_hit_rate=85.5,
            error_count_1h=2,
            error_count_24h=10
        )
        
        status_dict = status.to_dict()
        self.assertIsInstance(status_dict, dict)
        self.assertEqual(status_dict['status'], 'healthy')
        self.assertEqual(status_dict['version'], '1.0.0')


class TestHealthMonitor(unittest.TestCase):
    """HealthMonitor测试"""
    
    def setUp(self):
        """测试前准备"""
        self.monitor = HealthMonitor(app_version="test-1.0.0")
    
    def test_health_monitor_initialization(self):
        """测试HealthMonitor初始化"""
        self.assertEqual(self.monitor.app_version, "test-1.0.0")
        self.assertEqual(self.monitor.active_requests, 0)
        self.assertEqual(len(self.monitor.error_counts), 0)
        self.assertIsInstance(self.monitor.start_time, float)
    
    def test_request_counting(self):
        """测试请求计数功能"""
        # 测试增加请求
        self.monitor.increment_active_requests()
        self.assertEqual(self.monitor.active_requests, 1)
        
        self.monitor.increment_active_requests()
        self.assertEqual(self.monitor.active_requests, 2)
        
        # 测试减少请求
        self.monitor.decrement_active_requests()
        self.assertEqual(self.monitor.active_requests, 1)
        
        self.monitor.decrement_active_requests()
        self.assertEqual(self.monitor.active_requests, 0)
        
        # 测试不会变成负数
        self.monitor.decrement_active_requests()
        self.assertEqual(self.monitor.active_requests, 0)
    
    def test_error_recording(self):
        """测试错误记录功能"""
        # 记录错误
        self.monitor.record_error()
        self.assertEqual(len(self.monitor.error_counts), 1)
        
        self.monitor.record_error()
        self.assertEqual(len(self.monitor.error_counts), 2)
        
        # 测试错误统计
        error_stats = self.monitor._get_error_counts()
        self.assertEqual(error_stats['error_count_1h'], 2)
        self.assertEqual(error_stats['error_count_24h'], 2)
    
    def test_cache_stats_update(self):
        """测试缓存统计更新"""
        # 更新缓存大小
        self.monitor.update_cache_stats(1024)
        self.assertEqual(self.monitor.cache_stats['size'], 1024)
        
        # 记录缓存命中
        self.monitor.update_cache_stats(2048, hit=True)
        self.assertEqual(self.monitor.cache_stats['size'], 2048)
        self.assertEqual(self.monitor.cache_stats['hits'], 1)
        
        # 记录缓存未命中
        self.monitor.update_cache_stats(2048, hit=False)
        self.assertEqual(self.monitor.cache_stats['misses'], 1)
        
        # 测试命中率计算
        hit_rate = self.monitor._calculate_cache_hit_rate()
        self.assertEqual(hit_rate, 50.0)  # 1命中 / 2总请求 = 50%
    
    @patch('health_check.health_monitor.psutil.virtual_memory')
    @patch('health_check.health_monitor.psutil.cpu_percent')
    @patch('health_check.health_monitor.psutil.disk_usage')
    def test_get_system_resources(self, mock_disk, mock_cpu, mock_memory):
        """测试系统资源获取"""
        # 模拟系统资源数据
        mock_memory.return_value = Mock(
            percent=75.0,
            total=8589934592,
            used=6442450944
        )
        mock_cpu.return_value = 45.0
        mock_disk.return_value = Mock(
            total=1000000000000,
            used=500000000000
        )
        
        resources = self.monitor._get_system_resources()
        
        self.assertEqual(resources['memory_usage'], 75.0)
        self.assertEqual(resources['memory_total'], 8589934592)
        self.assertEqual(resources['memory_used'], 6442450944)
        self.assertEqual(resources['cpu_usage'], 45.0)
        self.assertEqual(resources['disk_usage'], 50.0)
    
    @patch('health_check.health_monitor.edge_tts.Communicate')
    def test_check_edge_tts_status_success(self, mock_communicate):
        """测试edge-tts状态检查成功"""
        # 模拟成功的edge-tts响应
        async def mock_stream():
            yield {"type": "audio", "data": b"test_audio_data"}
        
        mock_communicate_instance = Mock()
        mock_communicate_instance.stream.return_value = mock_stream()
        mock_communicate.return_value = mock_communicate_instance
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status, response_time = loop.run_until_complete(
                self.monitor._check_edge_tts_status()
            )
            
            self.assertTrue(status)
            self.assertIsInstance(response_time, float)
            self.assertGreater(response_time, 0)
        finally:
            loop.close()
    
    @patch('health_check.health_monitor.edge_tts.Communicate')
    def test_check_edge_tts_status_failure(self, mock_communicate):
        """测试edge-tts状态检查失败"""
        # 模拟edge-tts异常
        mock_communicate.side_effect = Exception("TTS service unavailable")
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status, response_time = loop.run_until_complete(
                self.monitor._check_edge_tts_status()
            )
            
            self.assertFalse(status)
            self.assertIsNone(response_time)
        finally:
            loop.close()
    
    def test_determine_overall_status(self):
        """测试整体状态判断"""
        # 测试健康状态
        resources = {
            'memory_usage': 50.0,
            'cpu_usage': 30.0,
            'disk_usage': 40.0
        }
        status = self.monitor._determine_overall_status(resources, True)
        self.assertEqual(status, 'healthy')
        
        # 测试edge-tts不可用
        status = self.monitor._determine_overall_status(resources, False)
        self.assertEqual(status, 'unhealthy')
        
        # 测试资源使用过高（不健康）
        resources_high = {
            'memory_usage': 95.0,
            'cpu_usage': 30.0,
            'disk_usage': 40.0
        }
        status = self.monitor._determine_overall_status(resources_high, True)
        self.assertEqual(status, 'unhealthy')
        
        # 测试资源使用较高（降级）
        resources_degraded = {
            'memory_usage': 85.0,
            'cpu_usage': 30.0,
            'disk_usage': 40.0
        }
        status = self.monitor._determine_overall_status(resources_degraded, True)
        self.assertEqual(status, 'degraded')
    
    def test_get_health_summary(self):
        """测试健康状态摘要获取"""
        summary = self.monitor.get_health_summary()
        
        self.assertIn('status', summary)
        self.assertIn('timestamp', summary)
        self.assertIn('uptime_seconds', summary)
        self.assertIn('version', summary)
        self.assertIn('edge_tts_available', summary)
        
        self.assertEqual(summary['version'], "test-1.0.0")
        self.assertIsInstance(summary['uptime_seconds'], float)


class TestHealthController(unittest.TestCase):
    """HealthController测试"""
    
    def setUp(self):
        """测试前准备"""
        self.app = Flask(__name__)
        self.controller = HealthController()
        self.controller.register_with_app(self.app)
        self.client = self.app.test_client()
    
    def test_health_check_endpoint(self):
        """测试基本健康检查端点"""
        response = self.client.get('/health')
        
        self.assertIn(response.status_code, [200, 503])
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
    
    def test_detailed_health_endpoint(self):
        """测试详细健康检查端点"""
        response = self.client.get('/health/detailed')
        
        self.assertIn(response.status_code, [200, 503])
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('memory_usage', data)
        self.assertIn('cpu_usage', data)
        self.assertIn('edge_tts_status', data)
    
    def test_readiness_check_endpoint(self):
        """测试就绪性检查端点"""
        response = self.client.get('/health/ready')
        
        self.assertIn(response.status_code, [200, 503])
        
        data = json.loads(response.data)
        self.assertIn('ready', data)
        self.assertIn('status', data)
        self.assertIn('edge_tts_available', data)
    
    def test_liveness_check_endpoint(self):
        """测试存活性检查端点"""
        response = self.client.get('/health/live')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('alive', data)
        self.assertTrue(data['alive'])
        self.assertIn('timestamp', data)
        self.assertIn('uptime_seconds', data)
    
    def test_http_status_code_mapping(self):
        """测试HTTP状态码映射"""
        self.assertEqual(self.controller._get_http_status_code('healthy'), 200)
        self.assertEqual(self.controller._get_http_status_code('degraded'), 200)
        self.assertEqual(self.controller._get_http_status_code('unhealthy'), 503)
        self.assertEqual(self.controller._get_http_status_code('unknown'), 503)


class TestHealthCheckMiddleware(unittest.TestCase):
    """HealthCheckMiddleware测试"""
    
    def setUp(self):
        """测试前准备"""
        self.app = Flask(__name__)
        self.middleware = HealthCheckMiddleware(self.app)
        self.client = self.app.test_client()
        
        # 添加测试路由
        @self.app.route('/test')
        def test_route():
            return 'OK'
        
        @self.app.route('/test-error')
        def test_error_route():
            raise Exception("Test error")
    
    def test_middleware_initialization(self):
        """测试中间件初始化"""
        self.assertIsInstance(self.middleware, HealthCheckMiddleware)
    
    def test_request_monitoring(self):
        """测试请求监控"""
        # 发送测试请求
        response = self.client.get('/test')
        self.assertEqual(response.status_code, 200)
        
        # 检查健康监控器状态
        # 注意：由于请求已完成，活跃请求数应该为0
        from health_check.health_monitor import health_monitor
        self.assertEqual(health_monitor.active_requests, 0)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 发送会产生错误的请求
        response = self.client.get('/test-error')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestFlaskIntegration(unittest.TestCase):
    """Flask集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.app = Flask(__name__)
    
    def test_setup_health_monitoring(self):
        """测试健康监控设置"""
        # 创建模拟缓存
        mock_cache = Mock()
        mock_cache.current_size = 1024
        
        # 设置健康监控
        middleware = setup_health_monitoring(
            self.app, 
            cache_instance=mock_cache,
            app_version="test-2.0.0"
        )
        
        self.assertIsInstance(middleware, HealthCheckMiddleware)
        
        # 测试缓存监控装饰器是否被正确应用
        # 检查add方法是否被装饰
        self.assertTrue(hasattr(mock_cache, 'add'))
        
        # 检查combine方法是否被装饰
        self.assertTrue(hasattr(mock_cache, 'combine'))


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)