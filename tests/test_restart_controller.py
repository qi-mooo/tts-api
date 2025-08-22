#!/usr/bin/env python3
"""
重启控制器单元测试

测试重启控制器的各项功能：
- 重启请求处理
- 活跃请求跟踪
- 配置重载
- 权限控制
- 回滚机制
"""

import unittest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from restart.restart_controller import RestartController, RestartStatus, RestartRequest
from error_handler.exceptions import SystemError, AuthorizationError


class TestRestartController(unittest.TestCase):
    """重启控制器测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.controller = RestartController()
        # 清理状态
        self.controller._status = RestartStatus.IDLE
        self.controller._current_request = None
        self.controller._active_requests.clear()
        self.controller._restart_history.clear()
    
    def tearDown(self):
        """测试后清理"""
        # 确保重置状态
        self.controller._status = RestartStatus.IDLE
        self.controller._current_request = None
        self.controller._active_requests.clear()
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(self.controller.status, RestartStatus.IDLE)
        self.assertFalse(self.controller.is_restarting)
        self.assertEqual(len(self.controller._active_requests), 0)
    
    def test_register_unregister_request(self):
        """测试请求注册和注销"""
        request_id = "test_request_001"
        endpoint = "/api/test"
        remote_addr = "127.0.0.1"
        
        # 注册请求
        self.controller.register_request(request_id, endpoint, remote_addr)
        
        # 验证请求已注册
        self.assertIn(request_id, self.controller._active_requests)
        self.assertEqual(self.controller._active_requests[request_id].endpoint, endpoint)
        self.assertEqual(self.controller._active_requests[request_id].remote_addr, remote_addr)
        
        # 注销请求
        self.controller.unregister_request(request_id)
        
        # 验证请求已注销
        self.assertNotIn(request_id, self.controller._active_requests)
    
    def test_multiple_active_requests(self):
        """测试多个活跃请求"""
        request_ids = ["req_001", "req_002", "req_003"]
        
        # 注册多个请求
        for req_id in request_ids:
            self.controller.register_request(req_id, f"/api/{req_id}", "127.0.0.1")
        
        # 验证所有请求都已注册
        self.assertEqual(len(self.controller._active_requests), 3)
        for req_id in request_ids:
            self.assertIn(req_id, self.controller._active_requests)
        
        # 注销部分请求
        self.controller.unregister_request("req_002")
        self.assertEqual(len(self.controller._active_requests), 2)
        self.assertNotIn("req_002", self.controller._active_requests)
        
        # 注销剩余请求
        for req_id in ["req_001", "req_003"]:
            self.controller.unregister_request(req_id)
        
        self.assertEqual(len(self.controller._active_requests), 0)
    
    @patch('restart.restart_controller.config_manager')
    def test_request_restart_success(self, mock_config_manager):
        """测试成功的重启请求"""
        mock_config_manager.validate.return_value = True
        
        # 模拟重启执行
        original_execute = self.controller._execute_restart
        self.controller._execute_restart = Mock()
        
        try:
            result = self.controller.request_restart(
                user="test_user",
                reason="测试重启",
                force=False,
                config_reload=True,
                timeout=5
            )
            
            # 验证返回结果
            self.assertTrue(result['success'])
            self.assertIn('request_id', result)
            self.assertEqual(result['message'], '重启请求已提交')
            
            # 验证状态变更
            self.assertEqual(self.controller.status, RestartStatus.PREPARING)
            self.assertIsNotNone(self.controller._current_request)
            
            # 等待一小段时间让线程启动
            time.sleep(0.1)
            
            # 验证执行函数被调用
            self.controller._execute_restart.assert_called_once()
            
        finally:
            # 恢复原始方法
            self.controller._execute_restart = original_execute
    
    def test_request_restart_while_restarting(self):
        """测试重启过程中的重启请求"""
        # 设置为重启状态
        self.controller._status = RestartStatus.RESTARTING
        
        # 尝试请求重启
        with self.assertRaises(SystemError) as context:
            self.controller.request_restart("test_user", "测试重启")
        
        # 验证异常信息
        self.assertEqual(context.exception.error_code, "RESTART_001")
        self.assertIn("系统正在重启中", str(context.exception))
    
    def test_cancel_restart_success(self):
        """测试成功取消重启"""
        # 设置为准备状态
        self.controller._status = RestartStatus.PREPARING
        self.controller._current_request = RestartRequest(
            request_id="test_restart",
            user="test_user",
            timestamp=datetime.now(),
            reason="测试重启"
        )
        
        # 取消重启
        result = self.controller.cancel_restart("admin_user")
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '重启已取消')
        
        # 验证状态重置
        self.assertEqual(self.controller.status, RestartStatus.IDLE)
        self.assertIsNone(self.controller._current_request)
    
    def test_cancel_restart_invalid_status(self):
        """测试无效状态下的取消重启"""
        # 设置为重启状态
        self.controller._status = RestartStatus.RESTARTING
        
        # 尝试取消重启
        with self.assertRaises(SystemError) as context:
            self.controller.cancel_restart("admin_user")
        
        # 验证异常信息
        self.assertEqual(context.exception.error_code, "RESTART_002")
        self.assertIn("无法取消重启", str(context.exception))
    
    def test_get_restart_status(self):
        """测试获取重启状态"""
        # 测试空闲状态
        status = self.controller.get_restart_status()
        self.assertEqual(status['status'], RestartStatus.IDLE.value)
        self.assertFalse(status['is_restarting'])
        self.assertEqual(status['active_requests_count'], 0)
        
        # 添加活跃请求
        self.controller.register_request("req_001", "/api/test", "127.0.0.1")
        
        # 设置重启请求
        self.controller._status = RestartStatus.PREPARING
        self.controller._current_request = RestartRequest(
            request_id="restart_001",
            user="test_user",
            timestamp=datetime.now(),
            reason="测试重启"
        )
        
        # 再次获取状态
        status = self.controller.get_restart_status()
        self.assertEqual(status['status'], RestartStatus.PREPARING.value)
        self.assertTrue(status['is_restarting'])
        self.assertEqual(status['active_requests_count'], 1)
        self.assertIn('current_request', status)
        self.assertIn('active_requests', status)
    
    def test_wait_for_active_requests_no_requests(self):
        """测试等待活跃请求（无请求）"""
        start_time = time.time()
        
        # 等待活跃请求完成
        self.controller._wait_for_active_requests(timeout=5)
        
        end_time = time.time()
        
        # 验证立即返回
        self.assertLess(end_time - start_time, 1)
    
    def test_wait_for_active_requests_with_timeout(self):
        """测试等待活跃请求超时"""
        # 添加活跃请求
        self.controller.register_request("req_001", "/api/test", "127.0.0.1")
        
        start_time = time.time()
        
        # 等待活跃请求完成（会超时）
        self.controller._wait_for_active_requests(timeout=2)
        
        end_time = time.time()
        
        # 验证等待了指定的超时时间
        self.assertGreaterEqual(end_time - start_time, 2)
        self.assertLess(end_time - start_time, 3)  # 允许一些误差
    
    def test_wait_for_active_requests_completion(self):
        """测试等待活跃请求完成"""
        # 添加活跃请求
        self.controller.register_request("req_001", "/api/test", "127.0.0.1")
        
        # 启动线程在1秒后注销请求
        def unregister_later():
            time.sleep(1)
            self.controller.unregister_request("req_001")
        
        threading.Thread(target=unregister_later, daemon=True).start()
        
        start_time = time.time()
        
        # 等待活跃请求完成
        self.controller._wait_for_active_requests(timeout=5)
        
        end_time = time.time()
        
        # 验证在超时前完成
        self.assertGreaterEqual(end_time - start_time, 1)
        self.assertLess(end_time - start_time, 2)
    
    @patch('restart.restart_controller.config_manager')
    def test_backup_config(self, mock_config_manager):
        """测试配置备份"""
        mock_config_data = {
            'tts': {'voice': 'test'},
            'system': {'port': 5000}
        }
        mock_config_manager.get_config_dict.return_value = mock_config_data
        
        # 执行配置备份
        self.controller._backup_config()
        
        # 验证备份数据
        self.assertEqual(self.controller._config_backup, mock_config_data)
        mock_config_manager.get_config_dict.assert_called_once()
    
    @patch('restart.restart_controller.config_manager')
    def test_perform_restart_with_config_reload(self, mock_config_manager):
        """测试执行重启（包含配置重载）"""
        mock_config_manager.validate.return_value = True
        
        restart_request = RestartRequest(
            request_id="test_restart",
            user="test_user",
            timestamp=datetime.now(),
            reason="测试重启",
            config_reload=True
        )
        
        # 执行重启
        self.controller._perform_restart(restart_request)
        
        # 验证配置重载被调用
        mock_config_manager.reload.assert_called_once()
        mock_config_manager.validate.assert_called_once()
    
    @patch('restart.restart_controller.config_manager')
    def test_perform_restart_config_validation_failure(self, mock_config_manager):
        """测试重启时配置验证失败"""
        mock_config_manager.validate.return_value = False
        
        restart_request = RestartRequest(
            request_id="test_restart",
            user="test_user",
            timestamp=datetime.now(),
            reason="测试重启",
            config_reload=True
        )
        
        # 执行重启应该失败
        with self.assertRaises(SystemError) as context:
            self.controller._perform_restart(restart_request)
        
        # 验证异常信息
        self.assertEqual(context.exception.error_code, "RESTART_004")
        self.assertIn("配置验证失败", str(context.exception))
    
    def test_restart_callbacks(self):
        """测试重启回调函数"""
        pre_callback_called = False
        post_callback_called = False
        
        def pre_callback():
            nonlocal pre_callback_called
            pre_callback_called = True
        
        def post_callback():
            nonlocal post_callback_called
            post_callback_called = True
        
        # 注册回调函数
        self.controller.add_pre_restart_callback(pre_callback)
        self.controller.add_post_restart_callback(post_callback)
        
        # 执行回调
        self.controller._execute_pre_restart_callbacks()
        self.controller._execute_post_restart_callbacks()
        
        # 验证回调被调用
        self.assertTrue(pre_callback_called)
        self.assertTrue(post_callback_called)
    
    def test_restart_callbacks_with_exception(self):
        """测试回调函数异常处理"""
        def failing_callback():
            raise Exception("回调函数异常")
        
        def normal_callback():
            pass
        
        # 注册回调函数（包含会失败的）
        self.controller.add_pre_restart_callback(failing_callback)
        self.controller.add_pre_restart_callback(normal_callback)
        
        # 执行回调不应该抛出异常
        try:
            self.controller._execute_pre_restart_callbacks()
        except Exception:
            self.fail("回调异常不应该传播")
    
    def test_restart_history(self):
        """测试重启历史记录"""
        # 初始历史应该为空
        history = self.controller.get_restart_history()
        self.assertEqual(len(history), 0)
        
        # 添加历史记录
        history_entry = {
            'request_id': 'restart_001',
            'user': 'test_user',
            'reason': '测试重启',
            'success': True,
            'duration': 5.0
        }
        
        self.controller._restart_history.append(history_entry)
        
        # 获取历史记录
        history = self.controller.get_restart_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['request_id'], 'restart_001')
    
    def test_restart_history_limit(self):
        """测试重启历史记录数量限制"""
        # 添加多条历史记录
        for i in range(15):
            history_entry = {
                'request_id': f'restart_{i:03d}',
                'user': 'test_user',
                'success': True
            }
            self.controller._restart_history.append(history_entry)
        
        # 获取限制数量的历史记录
        history = self.controller.get_restart_history(limit=5)
        self.assertEqual(len(history), 5)
        
        # 验证返回的是最新的记录
        self.assertEqual(history[-1]['request_id'], 'restart_014')
        self.assertEqual(history[0]['request_id'], 'restart_010')


class TestRestartRequest(unittest.TestCase):
    """重启请求数据类测试"""
    
    def test_restart_request_creation(self):
        """测试重启请求创建"""
        timestamp = datetime.now()
        
        request = RestartRequest(
            request_id="test_001",
            user="test_user",
            timestamp=timestamp,
            reason="测试重启",
            force=True,
            config_reload=False,
            timeout=60
        )
        
        self.assertEqual(request.request_id, "test_001")
        self.assertEqual(request.user, "test_user")
        self.assertEqual(request.timestamp, timestamp)
        self.assertEqual(request.reason, "测试重启")
        self.assertTrue(request.force)
        self.assertFalse(request.config_reload)
        self.assertEqual(request.timeout, 60)
    
    def test_restart_request_defaults(self):
        """测试重启请求默认值"""
        timestamp = datetime.now()
        
        request = RestartRequest(
            request_id="test_001",
            user="test_user",
            timestamp=timestamp,
            reason="测试重启"
        )
        
        # 验证默认值
        self.assertFalse(request.force)
        self.assertTrue(request.config_reload)
        self.assertEqual(request.timeout, 30)


if __name__ == '__main__':
    unittest.main()