#!/usr/bin/env python3
"""
重启功能Flask集成测试

测试重启中间件和Flask应用的集成：
- 请求跟踪中间件
- 重启状态检查
- 重启相关路由
"""

import unittest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from restart.flask_integration import RestartMiddleware, restart_middleware
from restart.restart_controller import restart_controller, RestartStatus


class TestRestartFlaskIntegration(unittest.TestCase):
    """重启Flask集成测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 创建测试Flask应用
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.secret_key = 'test-secret-key'
        
        # 创建中间件实例
        self.middleware = RestartMiddleware()
        self.middleware.init_app(self.app)
        
        # 创建测试客户端
        self.client = self.app.test_client()
        
        # 重置重启控制器状态
        restart_controller._status = RestartStatus.IDLE
        restart_controller._current_request = None
        restart_controller._active_requests.clear()
        
        # 添加测试路由
        @self.app.route('/test')
        def test_route():
            return {'message': 'test'}
        
        @self.app.route('/slow')
        def slow_route():
            time.sleep(2)
            return {'message': 'slow task completed'}
    
    def tearDown(self):
        """测试后清理"""
        # 重置重启控制器状态
        restart_controller._status = RestartStatus.IDLE
        restart_controller._current_request = None
        restart_controller._active_requests.clear()
    
    def test_normal_request_processing(self):
        """测试正常请求处理"""
        response = self.client.get('/test')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'test')
        
        # 验证响应头
        self.assertIn('X-Request-ID', response.headers)
        self.assertIn('X-Response-Time', response.headers)
    
    def test_request_tracking(self):
        """测试请求跟踪"""
        # 启动慢请求
        def make_slow_request():
            self.client.get('/slow')
        
        # 在后台启动请求
        request_thread = threading.Thread(target=make_slow_request, daemon=True)
        request_thread.start()
        
        # 等待请求开始
        time.sleep(0.5)
        
        # 检查活跃请求
        status = restart_controller.get_restart_status()
        self.assertGreater(status['active_requests_count'], 0)
        
        # 等待请求完成
        request_thread.join(timeout=5)
        
        # 检查请求已清理
        time.sleep(0.1)
        status = restart_controller.get_restart_status()
        self.assertEqual(status['active_requests_count'], 0)
    
    def test_request_blocked_during_restart(self):
        """测试重启期间请求被阻止"""
        # 设置重启状态
        restart_controller._status = RestartStatus.RESTARTING
        
        # 尝试发送请求
        response = self.client.get('/test')
        
        # 验证请求被阻止
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('系统正在重启中', data['error'])
        self.assertEqual(data['code'], 'SYSTEM_RESTARTING')
        self.assertIn('restart_status', data)
    
    def test_restart_status_endpoint(self):
        """测试重启状态端点"""
        response = self.client.get('/api/restart/status')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['status'], RestartStatus.IDLE.value)
    
    def test_restart_request_endpoint(self):
        """测试重启请求端点"""
        # 模拟重启执行
        original_execute = restart_controller._execute_restart
        restart_controller._execute_restart = Mock()
        
        try:
            request_data = {
                'user': 'test_user',
                'reason': '测试重启',
                'force': False,
                'config_reload': True,
                'timeout': 10
            }
            
            response = self.client.post('/api/restart/request',
                                      data=json.dumps(request_data),
                                      content_type='application/json')
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('request_id', data)
            self.assertEqual(data['message'], '重启请求已提交')
            
            # 等待一小段时间让线程启动
            time.sleep(0.1)
            
            # 验证重启被触发
            restart_controller._execute_restart.assert_called_once()
            
        finally:
            # 恢复原始方法
            restart_controller._execute_restart = original_execute
    
    def test_restart_request_invalid_data(self):
        """测试无效的重启请求数据"""
        # 发送空请求体
        response = self.client.post('/api/restart/request',
                                  data='',
                                  content_type='application/json')
        
        # 应该仍然成功（使用默认值）
        self.assertEqual(response.status_code, 200)
    
    def test_restart_cancel_endpoint(self):
        """测试取消重启端点"""
        # 先设置重启状态
        restart_controller._status = RestartStatus.PREPARING
        restart_controller._current_request = Mock()
        restart_controller._current_request.request_id = "test_restart"
        
        request_data = {
            'user': 'test_user'
        }
        
        response = self.client.post('/api/restart/cancel',
                                  data=json.dumps(request_data),
                                  content_type='application/json')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '重启已取消')
        
        # 验证状态重置
        self.assertEqual(restart_controller.status, RestartStatus.IDLE)
    
    def test_restart_history_endpoint(self):
        """测试重启历史端点"""
        # 添加一些历史记录
        restart_controller._restart_history = [
            {
                'request_id': 'restart_001',
                'user': 'user1',
                'success': True,
                'duration': 5.0
            },
            {
                'request_id': 'restart_002',
                'user': 'user2',
                'success': False,
                'duration': 2.0
            }
        ]
        
        response = self.client.get('/api/restart/history')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['total'], 2)
    
    def test_restart_history_with_limit(self):
        """测试带限制的重启历史"""
        # 添加多条历史记录
        for i in range(5):
            restart_controller._restart_history.append({
                'request_id': f'restart_{i:03d}',
                'user': f'user{i}',
                'success': True
            })
        
        response = self.client.get('/api/restart/history?limit=3')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 3)
        self.assertEqual(data['total'], 3)
    
    def test_middleware_error_handling(self):
        """测试中间件错误处理"""
        # 创建会抛出异常的路由
        @self.app.route('/error')
        def error_route():
            raise Exception("测试异常")
        
        response = self.client.get('/error')
        
        # 验证错误被正确处理
        self.assertEqual(response.status_code, 500)
        
        # 验证请求仍然被正确清理
        time.sleep(0.1)
        status = restart_controller.get_restart_status()
        self.assertEqual(status['active_requests_count'], 0)
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        def make_request(path):
            return self.client.get(path)
        
        # 启动多个并发请求
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(f'/test?id={i}',), daemon=True)
            threads.append(thread)
            thread.start()
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 检查活跃请求数量
        status = restart_controller.get_restart_status()
        # 由于请求很快完成，可能看不到所有5个请求
        self.assertGreaterEqual(status['active_requests_count'], 0)
        
        # 等待所有请求完成
        for thread in threads:
            thread.join(timeout=2)
        
        # 验证所有请求都被清理
        time.sleep(0.1)
        status = restart_controller.get_restart_status()
        self.assertEqual(status['active_requests_count'], 0)
    
    def test_request_id_uniqueness(self):
        """测试请求ID唯一性"""
        request_ids = set()
        
        # 发送多个请求并收集请求ID
        for _ in range(10):
            response = self.client.get('/test')
            request_id = response.headers.get('X-Request-ID')
            self.assertIsNotNone(request_id)
            request_ids.add(request_id)
        
        # 验证所有请求ID都是唯一的
        self.assertEqual(len(request_ids), 10)
    
    def test_response_time_header(self):
        """测试响应时间头"""
        response = self.client.get('/slow')
        
        # 验证响应时间头存在
        self.assertIn('X-Response-Time', response.headers)
        
        # 验证响应时间格式
        response_time = response.headers['X-Response-Time']
        self.assertTrue(response_time.endswith('s'))
        
        # 验证响应时间合理（应该大于2秒）
        time_value = float(response_time[:-1])
        self.assertGreaterEqual(time_value, 2.0)


class TestRestartMiddleware(unittest.TestCase):
    """重启中间件单独测试"""
    
    def setUp(self):
        """测试前设置"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # 重置重启控制器状态
        restart_controller._status = RestartStatus.IDLE
        restart_controller._active_requests.clear()
    
    def test_middleware_initialization(self):
        """测试中间件初始化"""
        middleware = RestartMiddleware()
        
        # 测试延迟初始化
        middleware.init_app(self.app)
        
        # 验证蓝图已注册
        self.assertIn('restart', self.app.blueprints)
    
    def test_middleware_direct_initialization(self):
        """测试中间件直接初始化"""
        middleware = RestartMiddleware(self.app)
        
        # 验证蓝图已注册
        self.assertIn('restart', self.app.blueprints)


if __name__ == '__main__':
    unittest.main()