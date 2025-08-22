"""
错误处理模块单元测试

测试自定义异常类和错误处理器的功能。
"""

import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request

# 导入被测试的模块
from error_handler import (
    ErrorHandler, RetryConfig, error_handler_middleware,
    TTSError, ServiceUnavailableError, AudioGenerationError,
    ValidationError, SystemResourceError, ConfigurationError,
    DictionaryError, CacheError, AuthenticationError, AuthorizationError
)


class TestTTSExceptions(unittest.TestCase):
    """测试自定义异常类"""
    
    def test_tts_error_basic(self):
        """测试基础 TTSError 异常"""
        error = TTSError("测试错误", "TEST_001", {"key": "value"})
        
        self.assertEqual(error.message, "测试错误")
        self.assertEqual(error.error_code, "TEST_001")
        self.assertEqual(error.details["key"], "value")
        self.assertEqual(str(error), "[TEST_001] 测试错误")
    
    def test_tts_error_to_dict(self):
        """测试 TTSError 转换为字典"""
        error = TTSError("测试错误", "TEST_001", {"key": "value"})
        error_dict = error.to_dict()
        
        self.assertEqual(error_dict["error_type"], "TTSError")
        self.assertEqual(error_dict["error_code"], "TEST_001")
        self.assertEqual(error_dict["message"], "测试错误")
        self.assertEqual(error_dict["details"]["key"], "value")
        self.assertIn("traceback", error_dict)
    
    def test_service_unavailable_error(self):
        """测试服务不可用异常"""
        error = ServiceUnavailableError("edge-tts")
        
        self.assertEqual(error.error_code, "TTS_001")
        self.assertEqual(error.details["service_name"], "edge-tts")
        self.assertIn("edge-tts", error.message)
    
    def test_audio_generation_error(self):
        """测试音频生成异常"""
        error = AudioGenerationError("生成失败", {"voice": "test-voice"})
        
        self.assertEqual(error.error_code, "TTS_002")
        self.assertEqual(error.message, "生成失败")
        self.assertEqual(error.details["voice"], "test-voice")
    
    def test_validation_error(self):
        """测试参数验证异常"""
        error = ValidationError("text", "文本不能为空")
        
        self.assertEqual(error.error_code, "VAL_001")
        self.assertEqual(error.details["field_name"], "text")
        self.assertIn("文本不能为空", error.message)
    
    def test_system_resource_error(self):
        """测试系统资源异常"""
        error = SystemResourceError("memory")
        
        self.assertEqual(error.error_code, "SYS_001")
        self.assertEqual(error.details["resource_type"], "memory")
        self.assertIn("memory", error.message)
    
    def test_configuration_error(self):
        """测试配置错误异常"""
        error = ConfigurationError("tts.voice", "语音配置无效")
        
        self.assertEqual(error.error_code, "CFG_001")
        self.assertEqual(error.details["config_key"], "tts.voice")
        self.assertIn("语音配置无效", error.message)
    
    def test_authentication_error(self):
        """测试认证失败异常"""
        error = AuthenticationError("用户名或密码错误")
        
        self.assertEqual(error.error_code, "AUTH_001")
        self.assertEqual(error.message, "用户名或密码错误")
    
    def test_authorization_error(self):
        """测试授权失败异常"""
        error = AuthorizationError("restart_system")
        
        self.assertEqual(error.error_code, "AUTH_002")
        self.assertEqual(error.details["action"], "restart_system")
        self.assertIn("restart_system", error.message)


class TestRetryConfig(unittest.TestCase):
    """测试重试配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RetryConfig()
        
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.base_delay, 1.0)
        self.assertEqual(config.max_delay, 60.0)
        self.assertEqual(config.backoff_factor, 2.0)
        self.assertTrue(config.jitter)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            backoff_factor=1.5,
            jitter=False
        )
        
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.base_delay, 0.5)
        self.assertEqual(config.max_delay, 30.0)
        self.assertEqual(config.backoff_factor, 1.5)
        self.assertFalse(config.jitter)


class TestErrorHandler(unittest.TestCase):
    """测试错误处理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_logger = Mock()
        self.error_handler = ErrorHandler(self.mock_logger)
        
        # 创建 Flask 应用上下文
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
    
    def test_handle_tts_error(self):
        """测试处理 TTS 错误"""
        error = ServiceUnavailableError("edge-tts")
        
        with self.app.test_request_context('/api/tts'):
            response, status_code = self.error_handler.handle_error(error)
            
            self.assertEqual(status_code, 503)
            response_data = json.loads(response.data)
            self.assertFalse(response_data["success"])
            self.assertEqual(response_data["error"]["error_code"], "TTS_001")
    
    def test_handle_validation_error(self):
        """测试处理验证错误"""
        error = ValueError("参数无效")
        
        with self.app.test_request_context('/api/tts'):
            response, status_code = self.error_handler.handle_error(error)
            
            self.assertEqual(status_code, 400)
            response_data = json.loads(response.data)
            self.assertFalse(response_data["success"])
            self.assertEqual(response_data["error"]["error_code"], "VAL_001")
    
    def test_handle_connection_error(self):
        """测试处理连接错误"""
        error = ConnectionError("连接失败")
        
        with self.app.test_request_context('/api/tts'):
            response, status_code = self.error_handler.handle_error(error)
            
            self.assertEqual(status_code, 503)
            response_data = json.loads(response.data)
            self.assertEqual(response_data["error"]["error_code"], "TTS_001")
    
    def test_handle_unknown_error(self):
        """测试处理未知错误"""
        error = RuntimeError("未知错误")
        
        with self.app.test_request_context('/api/tts'):
            response, status_code = self.error_handler.handle_error(error)
            
            self.assertEqual(status_code, 500)
            response_data = json.loads(response.data)
            self.assertEqual(response_data["error"]["error_code"], "UNKNOWN_001")
    
    @patch('time.sleep')
    def test_retry_with_backoff_success(self, mock_sleep):
        """测试重试机制成功场景"""
        mock_func = Mock()
        mock_func.side_effect = [Exception("失败"), Exception("失败"), "成功"]
        mock_func.__name__ = "test_function"  # 添加 __name__ 属性
        
        result = self.error_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "成功")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('time.sleep')
    def test_retry_with_backoff_failure(self, mock_sleep):
        """测试重试机制失败场景"""
        mock_func = Mock()
        mock_func.side_effect = Exception("持续失败")
        mock_func.__name__ = "test_function"  # 添加 __name__ 属性
        
        with self.assertRaises(Exception):
            self.error_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(mock_func.call_count, 4)  # 1 + 3 retries
        self.assertEqual(mock_sleep.call_count, 3)
    
    def test_retry_with_custom_config(self):
        """测试自定义重试配置"""
        config = RetryConfig(max_retries=1, base_delay=0.1)
        mock_func = Mock()
        mock_func.side_effect = Exception("失败")
        mock_func.__name__ = "test_function"  # 添加 __name__ 属性
        
        with patch('time.sleep') as mock_sleep:
            with self.assertRaises(Exception):
                self.error_handler.retry_with_backoff(mock_func, retry_config=config)
            
            self.assertEqual(mock_func.call_count, 2)  # 1 + 1 retry
            self.assertEqual(mock_sleep.call_count, 1)
    
    def test_fallback_voice_success_with_original(self):
        """测试降级语音 - 原始语音成功"""
        mock_func = Mock(return_value="成功")
        
        result = self.error_handler.with_fallback_voice(
            "zh-CN-YunjianNeural", mock_func, voice="zh-CN-YunjianNeural"
        )
        
        self.assertEqual(result, "成功")
        self.assertEqual(mock_func.call_count, 1)
    
    def test_fallback_voice_success_with_fallback(self):
        """测试降级语音 - 降级语音成功"""
        mock_func = Mock()
        mock_func.side_effect = [Exception("原始失败"), "降级成功"]
        
        result = self.error_handler.with_fallback_voice(
            "zh-CN-YunjianNeural", mock_func, voice="zh-CN-YunjianNeural"
        )
        
        self.assertEqual(result, "降级成功")
        self.assertEqual(mock_func.call_count, 2)
    
    def test_fallback_voice_all_fail(self):
        """测试降级语音 - 全部失败"""
        mock_func = Mock()
        mock_func.side_effect = Exception("全部失败")
        
        with self.assertRaises(Exception):
            self.error_handler.with_fallback_voice(
                "zh-CN-YunjianNeural", mock_func, voice="zh-CN-YunjianNeural"
            )
    
    def test_circuit_breaker_normal_operation(self):
        """测试熔断器正常操作"""
        @self.error_handler.circuit_breaker(failure_threshold=2, recovery_timeout=1)
        def test_func():
            return "成功"
        
        result = test_func()
        self.assertEqual(result, "成功")
    
    def test_circuit_breaker_opens_after_failures(self):
        """测试熔断器在失败后开启"""
        @self.error_handler.circuit_breaker(failure_threshold=2, recovery_timeout=1)
        def test_func():
            raise Exception("失败")
        
        # 触发失败次数达到阈值
        with self.assertRaises(Exception):
            test_func()
        with self.assertRaises(Exception):
            test_func()
        
        # 熔断器应该开启
        with self.assertRaises(ServiceUnavailableError):
            test_func()
    
    @patch('time.time')
    def test_circuit_breaker_recovery(self, mock_time):
        """测试熔断器恢复"""
        # 模拟时间流逝：失败时间0，恢复检查时间70（超过60秒恢复时间）
        mock_time.side_effect = [0, 70]
        
        call_count = 0
        
        @self.error_handler.circuit_breaker(failure_threshold=1, recovery_timeout=60)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("失败")
            return "恢复成功"
        
        # 触发熔断
        with self.assertRaises(Exception):
            test_func()
        
        # 时间过去，熔断器应该尝试恢复并成功
        result = test_func()
        self.assertEqual(result, "恢复成功")


class TestErrorHandlerMiddleware(unittest.TestCase):
    """测试错误处理中间件"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_logger = Mock()
        self.error_handler = ErrorHandler(self.mock_logger)
        self.middleware = error_handler_middleware(self.error_handler)
        
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
    
    def test_middleware_handles_exception(self):
        """测试中间件处理异常"""
        error = TTSError("测试错误", "TEST_001")
        
        with self.app.test_request_context('/api/test'):
            response = self.middleware(error)
            
            self.assertIsNotNone(response)
            # 验证返回的是 tuple (response, status_code)
            self.assertIsInstance(response, tuple)
            self.assertEqual(len(response), 2)


if __name__ == '__main__':
    unittest.main()