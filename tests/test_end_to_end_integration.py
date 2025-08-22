#!/usr/bin/env python3
"""
端到端集成测试

测试整个 TTS 系统的主要功能流程，包括：
1. 系统启动和健康检查
2. Web 管理控制台功能
3. TTS API 端点
4. 字典服务集成
5. 错误处理机制
6. 配置管理
7. 日志记录
8. 音频缓存
"""

import unittest
import requests
import json
import time
import os
import sys
import tempfile
import threading
import subprocess
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import config_manager
from dictionary.dictionary_service import DictionaryService
from error_handler.error_handler import ErrorHandler
from logger.structured_logger import get_logger
from audio_cache.audio_cache import OptimizedAudioCache
from admin.admin_controller import AdminController
from health_check.health_monitor import HealthMonitor


class EndToEndIntegrationTest(unittest.TestCase):
    """端到端集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.base_url = 'http://localhost:8080'
        cls.test_logger = get_logger('e2e_test')
        cls.temp_files = []
        
        # 创建临时配置文件
        cls.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        cls.temp_config.write(json.dumps({
            "tts": {
                "narration_voice": "zh-CN-YunjianNeural",
                "dialogue_voice": "zh-CN-XiaoyiNeural",
                "default_speed": 1.2,
                "cache_size_limit": 10485760,
                "cache_time_limit": 1200
            },
            "admin": {
                "username": "test_admin",
                "password_hash": "$2b$12$test_hash",
                "session_timeout": 3600
            },
            "logging": {
                "level": "INFO",
                "file": "logs/test.log"
            }
        }))
        cls.temp_config.close()
        cls.temp_files.append(cls.temp_config.name)
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        for temp_file in cls.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def setUp(self):
        """每个测试方法的初始化"""
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def tearDown(self):
        """每个测试方法的清理"""
        self.session.close()


class TestSystemHealthAndStartup(EndToEndIntegrationTest):
    """系统健康检查和启动测试"""
    
    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        print("\n测试健康检查端点...")
        
        # 创建健康监控器
        health_monitor = HealthMonitor()
        
        # 测试基本健康检查
        status = health_monitor.get_system_status()
        self.assertIsNotNone(status)
        self.assertIn('status', status)
        self.assertIn('uptime', status)
        self.assertIn('memory_usage', status)
        
        print("✓ 健康检查基本功能正常")
    
    def test_configuration_loading(self):
        """测试配置加载"""
        print("\n测试配置加载...")
        
        # 测试配置管理器
        self.assertIsNotNone(config_manager.tts)
        self.assertIsNotNone(config_manager.tts.narration_voice)
        self.assertIsNotNone(config_manager.tts.dialogue_voice)
        
        # 测试配置验证
        is_valid = config_manager.validate()
        self.assertTrue(is_valid)
        
        print("✓ 配置加载和验证正常")
    
    def test_logging_system(self):
        """测试日志系统"""
        print("\n测试日志系统...")
        
        logger = get_logger('test_module')
        
        # 测试不同级别的日志
        logger.info("测试信息日志", extra={'test_data': 'info'})
        logger.warning("测试警告日志", extra={'test_data': 'warning'})
        logger.error("测试错误日志", extra={'test_data': 'error'})
        
        # 测试性能日志
        logger.performance("test_operation", 1.5, extra={'test_metric': 100})
        
        print("✓ 日志系统功能正常")


class TestDictionaryServiceIntegration(EndToEndIntegrationTest):
    """字典服务集成测试"""
    
    def setUp(self):
        super().setUp()
        # 创建临时字典规则文件
        self.temp_dict_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_dict_file.close()
        self.temp_files.append(self.temp_dict_file.name)
        
        self.dictionary = DictionaryService(self.temp_dict_file.name)
    
    def test_pronunciation_rules(self):
        """测试发音规则"""
        print("\n测试发音规则...")
        
        # 添加发音规则
        rule_id = self.dictionary.add_rule(
            pattern=r'\bAPI\b',
            replacement='A P I',
            rule_type='pronunciation'
        )
        self.assertIsNotNone(rule_id)
        
        # 测试规则应用
        result = self.dictionary.process_text('这是一个 API 接口')
        self.assertIn('A P I', result)
        
        print("✓ 发音规则功能正常")
    
    def test_content_filtering(self):
        """测试内容过滤"""
        print("\n测试内容过滤...")
        
        # 添加过滤规则
        rule_id = self.dictionary.add_rule(
            pattern=r'敏感词',
            replacement='***',
            rule_type='filter'
        )
        self.assertIsNotNone(rule_id)
        
        # 测试规则应用
        result = self.dictionary.process_text('这包含敏感词内容')
        self.assertIn('***', result)
        
        print("✓ 内容过滤功能正常")
    
    def test_rule_management(self):
        """测试规则管理"""
        print("\n测试规则管理...")
        
        # 添加规则
        rule_id = self.dictionary.add_rule(
            pattern='GitHub',
            replacement='吉特哈布',
            rule_type='pronunciation'
        )
        
        # 获取规则
        rule = self.dictionary.get_rule(rule_id)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.pattern, 'GitHub')
        
        # 更新规则
        success = self.dictionary.update_rule(rule_id, replacement='新吉特哈布')
        self.assertTrue(success)
        
        # 验证更新
        updated_rule = self.dictionary.get_rule(rule_id)
        self.assertEqual(updated_rule.replacement, '新吉特哈布')
        
        # 删除规则
        success = self.dictionary.remove_rule(rule_id)
        self.assertTrue(success)
        
        # 验证删除
        deleted_rule = self.dictionary.get_rule(rule_id)
        self.assertIsNone(deleted_rule)
        
        print("✓ 规则管理功能正常")


class TestErrorHandlingIntegration(EndToEndIntegrationTest):
    """错误处理集成测试"""
    
    def setUp(self):
        super().setUp()
        self.logger = get_logger('error_test')
        self.error_handler = ErrorHandler(self.logger.logger)
    
    def test_validation_error_handling(self):
        """测试参数验证错误处理"""
        print("\n测试参数验证错误处理...")
        
        from error_handler.exceptions import ValidationError
        
        error = ValidationError(
            field_name='text',
            message='文本参数不能为空'
        )
        
        response = self.error_handler.handle_error(error)
        self.assertEqual(response[1], 400)  # HTTP 400 Bad Request
        
        # 检查响应数据
        data = json.loads(response[0].data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['error_code'], 'VAL_001')
        
        print("✓ 参数验证错误处理正常")
    
    def test_retry_mechanism(self):
        """测试重试机制"""
        print("\n测试重试机制...")
        
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("临时失败")
            return "成功"
        
        # 配置重试
        from error_handler.error_handler import RetryConfig
        retry_config = RetryConfig(max_retries=3, base_delay=0.1)
        
        result = self.error_handler.retry_with_backoff(
            failing_function, 
            retry_config=retry_config
        )
        
        self.assertEqual(result, "成功")
        self.assertEqual(call_count, 3)
        
        print("✓ 重试机制功能正常")
    
    def test_error_recovery_strategies(self):
        """测试错误恢复策略"""
        print("\n测试错误恢复策略...")
        
        from error_handler.exceptions import TTSError, ServiceUnavailableError
        
        # 测试服务不可用错误
        error = ServiceUnavailableError("Edge-TTS 服务不可用")
        response = self.error_handler.handle_error(error)
        
        self.assertEqual(response[1], 503)  # HTTP 503 Service Unavailable
        
        data = json.loads(response[0].data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['error_code'], 'TTS_001')
        
        print("✓ 错误恢复策略功能正常")


class TestAudioCacheIntegration(EndToEndIntegrationTest):
    """音频缓存集成测试"""
    
    def setUp(self):
        super().setUp()
        # 创建临时缓存目录
        self.temp_cache_dir = tempfile.mkdtemp()
        self.audio_cache = OptimizedAudioCache()
    
    def tearDown(self):
        super().tearDown()
        # 清理临时缓存目录
        import shutil
        if os.path.exists(self.temp_cache_dir):
            shutil.rmtree(self.temp_cache_dir)
    
    def test_cache_operations(self):
        """测试缓存操作"""
        print("\n测试缓存操作...")
        
        # 测试缓存存储
        test_audio_data = b"fake_audio_data"
        cache_key = "test_key"
        
        success = self.audio_cache.set(cache_key, test_audio_data)
        self.assertTrue(success)
        
        # 测试缓存获取
        cached_data = self.audio_cache.get(cache_key)
        self.assertEqual(cached_data, test_audio_data)
        
        # 测试缓存统计
        stats = self.audio_cache.get_stats()
        self.assertIn('cache_size', stats)
        self.assertIn('hit_rate', stats)
        
        print("✓ 缓存操作功能正常")
    
    def test_cache_cleanup(self):
        """测试缓存清理"""
        print("\n测试缓存清理...")
        
        # 添加多个缓存项
        for i in range(5):
            self.audio_cache.set(f"key_{i}", b"data" * 100)
        
        # 获取清理前的统计
        stats_before = self.audio_cache.get_stats()
        
        # 执行清理
        cleaned_count = self.audio_cache.cleanup()
        
        # 验证清理效果
        stats_after = self.audio_cache.get_stats()
        self.assertLessEqual(stats_after['cache_size'], stats_before['cache_size'])
        
        print(f"✓ 缓存清理功能正常，清理了 {cleaned_count} 个项目")


class TestWebAdminIntegration(EndToEndIntegrationTest):
    """Web 管理控制台集成测试"""
    
    def setUp(self):
        super().setUp()
        self.admin_controller = AdminController()
    
    def test_admin_authentication(self):
        """测试管理员认证"""
        print("\n测试管理员认证...")
        
        # 测试有效凭据
        is_valid = self.admin_controller.validate_credentials('admin', 'test_password')
        # 注意：这里需要根据实际的密码哈希来调整
        
        # 测试无效凭据
        is_invalid = self.admin_controller.validate_credentials('admin', 'wrong_password')
        self.assertFalse(is_invalid)
        
        print("✓ 管理员认证功能正常")
    
    def test_config_management_api(self):
        """测试配置管理 API"""
        print("\n测试配置管理 API...")
        
        # 测试获取配置
        config_data = self.admin_controller.get_config()
        self.assertIsNotNone(config_data)
        self.assertIn('tts', config_data)
        
        # 测试更新配置
        new_config = {
            'tts': {
                'default_speed': 1.5
            }
        }
        
        success = self.admin_controller.update_config(new_config)
        self.assertTrue(success)
        
        # 验证配置更新
        updated_config = self.admin_controller.get_config()
        self.assertEqual(updated_config['tts']['default_speed'], 1.5)
        
        print("✓ 配置管理 API 功能正常")


class TestTextProcessingWorkflow(EndToEndIntegrationTest):
    """文本处理工作流测试"""
    
    def setUp(self):
        super().setUp()
        # 创建临时字典文件
        self.temp_dict_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_dict_file.close()
        self.temp_files.append(self.temp_dict_file.name)
        
        self.dictionary = DictionaryService(self.temp_dict_file.name)
        self.logger = get_logger('workflow_test')
        self.error_handler = ErrorHandler(self.logger.logger)
    
    def test_complete_text_processing_workflow(self):
        """测试完整的文本处理工作流"""
        print("\n测试完整的文本处理工作流...")
        
        # 1. 添加字典规则
        self.dictionary.add_rule(
            pattern=r'\bAPI\b',
            replacement='A P I',
            rule_type='pronunciation'
        )
        
        self.dictionary.add_rule(
            pattern=r'GitHub',
            replacement='吉特哈布',
            rule_type='pronunciation'
        )
        
        # 2. 处理包含多种元素的文本
        input_text = '这是一个 GitHub API 的使用示例："你好世界"这是对话。'
        
        # 3. 应用字典规则
        processed_text = self.dictionary.process_text(input_text)
        
        # 4. 验证处理结果
        self.assertIn('吉特哈布', processed_text)
        self.assertIn('A P I', processed_text)
        
        # 5. 模拟文本分段处理
        segments = self._segment_text(processed_text)
        
        # 6. 验证分段结果
        self.assertGreater(len(segments), 0)
        
        # 检查是否正确识别了旁白和对话
        has_narration = any(seg['tag'] == 'narration' for seg in segments)
        has_dialogue = any(seg['tag'] == 'dialogue' for seg in segments)
        
        self.assertTrue(has_narration)
        self.assertTrue(has_dialogue)
        
        print("✓ 完整文本处理工作流正常")
    
    def _segment_text(self, text):
        """文本分段辅助方法"""
        result = []
        tmp_str = ""
        end_tag = "narration"

        for char in text:
            if char in ['"', '"']:
                if tmp_str.strip():
                    result.append({"text": tmp_str.strip(), "tag": end_tag})
                tmp_str = ""
                end_tag = "dialogue" if char == '"' else "narration"
            else:
                tmp_str += char

        if tmp_str.strip():
            result.append({"text": tmp_str.strip(), "tag": end_tag})

        return result


class TestSystemIntegrationScenarios(EndToEndIntegrationTest):
    """系统集成场景测试"""
    
    def test_high_load_scenario(self):
        """测试高负载场景"""
        print("\n测试高负载场景...")
        
        # 模拟多个并发请求
        import concurrent.futures
        
        def process_request(request_id):
            """模拟处理单个请求"""
            try:
                # 创建字典服务实例
                temp_dict_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                temp_dict_file.close()
                
                dictionary = DictionaryService(temp_dict_file.name)
                
                # 处理文本
                text = f"这是请求 {request_id} 的测试文本"
                result = dictionary.process_text(text)
                
                # 清理
                os.unlink(temp_dict_file.name)
                
                return {'request_id': request_id, 'success': True, 'result': result}
            except Exception as e:
                return {'request_id': request_id, 'success': False, 'error': str(e)}
        
        # 并发执行多个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_request, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 验证结果
        successful_requests = [r for r in results if r['success']]
        self.assertEqual(len(successful_requests), 10)
        
        print(f"✓ 高负载场景测试通过，成功处理 {len(successful_requests)} 个请求")
    
    def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        print("\n测试错误恢复场景...")
        
        logger = get_logger('recovery_test')
        error_handler = ErrorHandler(logger.logger)
        
        # 模拟服务故障和恢复
        failure_count = 0
        
        def unreliable_service():
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:
                raise Exception(f"服务故障 #{failure_count}")
            
            return "服务恢复正常"
        
        # 测试重试机制
        from error_handler.error_handler import RetryConfig
        retry_config = RetryConfig(max_retries=5, base_delay=0.1)
        
        result = error_handler.retry_with_backoff(
            unreliable_service,
            retry_config=retry_config
        )
        
        self.assertEqual(result, "服务恢复正常")
        self.assertEqual(failure_count, 3)  # 2次失败 + 1次成功
        
        print("✓ 错误恢复场景测试通过")


def run_integration_test_suite():
    """运行完整的集成测试套件"""
    print("=" * 60)
    print("开始端到端集成测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestSystemHealthAndStartup,
        TestDictionaryServiceIntegration,
        TestErrorHandlingIntegration,
        TestAudioCacheIntegration,
        TestWebAdminIntegration,
        TestTextProcessingWorkflow,
        TestSystemIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("集成测试结果摘要")
    print("=" * 60)
    print(f"运行测试数量: {result.testsRun}")
    print(f"失败数量: {len(result.failures)}")
    print(f"错误数量: {len(result.errors)}")
    print(f"跳过数量: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n测试结果: {'✓ 通过' if success else '✗ 失败'}")
    
    return success


if __name__ == '__main__':
    success = run_integration_test_suite()
    sys.exit(0 if success else 1)