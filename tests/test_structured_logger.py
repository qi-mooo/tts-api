"""
结构化日志系统单元测试
"""

import unittest
import tempfile
import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from logger.structured_logger import (
    StructuredLogger, 
    LoggerManager, 
    get_logger, 
    performance_timer,
    PerformanceTimer
)
from logger.config import LoggingConfig


class TestStructuredLogger(unittest.TestCase):
    """结构化日志记录器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test.log')
        
        self.config = {
            'level': 'DEBUG',
            'file': self.log_file,
            'max_size': '1MB',
            'backup_count': 3
        }
        
        self.logger = StructuredLogger('test_logger', self.config)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_initialization(self):
        """测试日志记录器初始化"""
        self.assertEqual(self.logger.name, 'test_logger')
        self.assertEqual(self.logger.config, self.config)
        self.assertIsNotNone(self.logger.logger)
    
    def test_log_levels(self):
        """测试不同日志级别"""
        # 测试各种日志级别
        self.logger.debug("Debug message", extra_field="debug_value")
        self.logger.info("Info message", extra_field="info_value")
        self.logger.warning("Warning message", extra_field="warning_value")
        self.logger.error("Error message", extra_field="error_value")
        self.logger.critical("Critical message", extra_field="critical_value")
        
        # 验证日志文件存在
        self.assertTrue(os.path.exists(self.log_file))
        
        # 读取并验证日志内容
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        self.assertGreater(len(log_lines), 0)
        
        # 验证日志格式
        for line in log_lines:
            if line.strip():
                log_data = json.loads(line.strip())
                self.assertIn('timestamp', log_data)
                self.assertIn('level', log_data)
                self.assertIn('module', log_data)
                self.assertIn('message', log_data)
                self.assertIn('request_id', log_data)
    
    def test_error_logging_with_exception(self):
        """测试异常错误日志"""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            self.logger.error("Error occurred", error=e, context="test")
        
        # 验证错误日志包含异常信息
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        self.assertIn('error_type', log_content)
        self.assertIn('error_message', log_content)
        self.assertIn('traceback', log_content)
        self.assertIn('ValueError', log_content)
    
    def test_performance_logging(self):
        """测试性能日志"""
        self.logger.performance("test_operation", 1.5, param1="value1")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # 找到性能日志
        perf_log = None
        for line in log_lines:
            if line.strip():
                log_data = json.loads(line.strip())
                if log_data.get('log_type') == 'performance':
                    perf_log = log_data
                    break
        
        self.assertIsNotNone(perf_log)
        self.assertEqual(perf_log['operation'], 'test_operation')
        self.assertEqual(perf_log['duration_ms'], 1500.0)
        self.assertEqual(perf_log['param1'], 'value1')
    
    def test_audit_logging(self):
        """测试审计日志"""
        self.logger.audit("user_login", "test_user", ip="127.0.0.1")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # 找到审计日志
        audit_log = None
        for line in log_lines:
            if line.strip():
                log_data = json.loads(line.strip())
                if log_data.get('log_type') == 'audit':
                    audit_log = log_data
                    break
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log['action'], 'user_login')
        self.assertEqual(audit_log['user'], 'test_user')
        self.assertEqual(audit_log['ip'], '127.0.0.1')
    
    def test_request_id_handling(self):
        """测试请求ID处理"""
        # 设置请求ID
        test_request_id = "test_req_123"
        self.logger.set_request_id(test_request_id)
        
        self.logger.info("Test message with request ID")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        log_data = json.loads(log_lines[-1].strip())
        self.assertEqual(log_data['request_id'], test_request_id)
    
    def test_size_parsing(self):
        """测试大小解析"""
        # 测试不同大小格式
        self.assertEqual(self.logger._parse_size('1024'), 1024)
        self.assertEqual(self.logger._parse_size('1KB'), 1024)
        self.assertEqual(self.logger._parse_size('1MB'), 1024 * 1024)
        self.assertEqual(self.logger._parse_size('1GB'), 1024 * 1024 * 1024)


class TestPerformanceTimer(unittest.TestCase):
    """性能计时器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'perf_test.log')
        
        config = {
            'level': 'DEBUG',
            'file': self.log_file,
            'max_size': '1MB',
            'backup_count': 3
        }
        
        self.logger = StructuredLogger('perf_test', config)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_performance_timer_context_manager(self):
        """测试性能计时器上下文管理器"""
        with performance_timer(self.logger, "test_operation", param="value"):
            time.sleep(0.1)  # 模拟操作
        
        # 验证性能日志被记录
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        self.assertIn('Performance: test_operation', log_content)
        self.assertIn('duration_ms', log_content)
        self.assertIn('param', log_content)
    
    def test_performance_timer_direct_usage(self):
        """测试直接使用性能计时器"""
        timer = PerformanceTimer(self.logger, "direct_test", test_param="test_value")
        
        with timer:
            time.sleep(0.05)
        
        # 验证日志记录
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        perf_log = None
        for line in log_lines:
            if line.strip():
                log_data = json.loads(line.strip())
                if 'duration_ms' in log_data:
                    perf_log = log_data
                    break
        
        self.assertIsNotNone(perf_log)
        self.assertGreater(perf_log['duration_ms'], 40)  # 至少50ms
        self.assertEqual(perf_log['test_param'], 'test_value')


class TestLoggerManager(unittest.TestCase):
    """日志管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例实例
        LoggerManager._instance = None
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        
        self.assertIs(manager1, manager2)
    
    def test_get_logger(self):
        """测试获取日志记录器"""
        manager = LoggerManager()
        
        logger1 = manager.get_logger('test1')
        logger2 = manager.get_logger('test1')  # 相同名称
        logger3 = manager.get_logger('test2')  # 不同名称
        
        # 相同名称应该返回同一个实例
        self.assertIs(logger1, logger2)
        # 不同名称应该返回不同实例
        self.assertIsNot(logger1, logger3)
    
    def test_update_config(self):
        """测试更新配置"""
        manager = LoggerManager()
        
        # 创建一个日志记录器
        logger = manager.get_logger('test_config')
        original_level = logger.config['level']
        
        # 更新配置
        new_config = {'level': 'ERROR'}
        manager.update_config(new_config)
        
        # 验证配置已更新
        self.assertEqual(logger.config['level'], 'ERROR')
        self.assertNotEqual(logger.config['level'], original_level)


class TestLoggingConfig(unittest.TestCase):
    """日志配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = LoggingConfig.DEFAULT_CONFIG
        
        self.assertIn('level', config)
        self.assertIn('file', config)
        self.assertIn('max_size', config)
        self.assertIn('backup_count', config)
    
    def test_from_env(self):
        """测试从环境变量加载配置"""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'ERROR',
            'LOG_FILE': '/tmp/test.log',
            'LOG_MAX_SIZE': '5MB',
            'LOG_BACKUP_COUNT': '10'
        }):
            config = LoggingConfig.from_env()
            
            self.assertEqual(config['level'], 'ERROR')
            self.assertEqual(config['file'], '/tmp/test.log')
            self.assertEqual(config['max_size'], '5MB')
            self.assertEqual(config['backup_count'], 10)
    
    def test_from_dict(self):
        """测试从字典加载配置"""
        input_config = {
            'level': 'WARNING',
            'file': 'custom.log'
        }
        
        config = LoggingConfig.from_dict(input_config)
        
        self.assertEqual(config['level'], 'WARNING')
        self.assertEqual(config['file'], 'custom.log')
        # 应该保留默认值
        self.assertIn('max_size', config)
        self.assertIn('backup_count', config)
    
    def test_validate_config(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            'level': 'INFO',
            'file': 'test.log',
            'max_size': '10MB',
            'backup_count': 5
        }
        self.assertTrue(LoggingConfig.validate_config(valid_config))
        
        # 无效配置 - 缺少必需键
        invalid_config1 = {
            'level': 'INFO',
            'file': 'test.log'
            # 缺少 max_size 和 backup_count
        }
        self.assertFalse(LoggingConfig.validate_config(invalid_config1))
        
        # 无效配置 - 无效日志级别
        invalid_config2 = {
            'level': 'INVALID_LEVEL',
            'file': 'test.log',
            'max_size': '10MB',
            'backup_count': 5
        }
        self.assertFalse(LoggingConfig.validate_config(invalid_config2))
        
        # 无效配置 - 无效备份数量
        invalid_config3 = {
            'level': 'INFO',
            'file': 'test.log',
            'max_size': '10MB',
            'backup_count': -1
        }
        self.assertFalse(LoggingConfig.validate_config(invalid_config3))


class TestGetLogger(unittest.TestCase):
    """测试便捷函数"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例实例
        LoggerManager._instance = None
    
    def test_get_logger_function(self):
        """测试 get_logger 便捷函数"""
        logger = get_logger('test_convenience')
        
        self.assertIsInstance(logger, StructuredLogger)
        self.assertEqual(logger.name, 'test_convenience')
    
    def test_get_logger_with_config(self):
        """测试带配置的 get_logger 函数"""
        custom_config = {
            'level': 'ERROR',
            'file': 'custom_test.log'
        }
        
        logger = get_logger('test_custom', custom_config)
        
        self.assertEqual(logger.config['level'], 'ERROR')
        self.assertEqual(logger.config['file'], 'custom_test.log')


if __name__ == '__main__':
    unittest.main()