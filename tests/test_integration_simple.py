#!/usr/bin/env python3
"""
简化的集成测试

测试 TTS 系统的核心功能
"""

import unittest
import tempfile
import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import config_manager
from dictionary.dictionary_service import DictionaryService
from error_handler.error_handler import ErrorHandler
from logger.structured_logger import get_logger
from audio_cache.audio_cache import OptimizedAudioCache
from health_check.health_monitor import HealthMonitor


class SimpleIntegrationTest(unittest.TestCase):
    """简化的集成测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.logger = get_logger('integration_test')
        self.temp_files = []
    
    def tearDown(self):
        """测试清理"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_config_manager(self):
        """测试配置管理器"""
        print("\n测试配置管理器...")
        
        # 测试配置获取
        tts_config = config_manager.tts
        self.assertIsNotNone(tts_config)
        self.assertIsNotNone(tts_config.narration_voice)
        self.assertIsNotNone(tts_config.dialogue_voice)
        
        # 测试配置验证
        is_valid = config_manager.validate()
        self.assertTrue(is_valid)
        
        print("✓ 配置管理器功能正常")
    
    def test_dictionary_service(self):
        """测试字典服务"""
        print("\n测试字典服务...")
        
        # 创建临时字典文件
        temp_dict_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_dict_file.close()
        self.temp_files.append(temp_dict_file.name)
        
        dictionary = DictionaryService(temp_dict_file.name)
        
        # 测试添加规则
        rule_id = dictionary.add_rule(
            pattern=r'\bAPI\b',
            replacement='A P I',
            rule_type='pronunciation'
        )
        self.assertIsNotNone(rule_id)
        
        # 测试规则应用
        result = dictionary.process_text('这是一个 API 接口')
        self.assertIn('A P I', result)
        
        # 测试规则管理
        rule = dictionary.get_rule(rule_id)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.pattern, r'\bAPI\b')
        
        print("✓ 字典服务功能正常")
    
    def test_error_handler(self):
        """测试错误处理"""
        print("\n测试错误处理...")
        
        logger = get_logger('error_test')
        error_handler = ErrorHandler(logger.logger)
        
        # 测试重试机制
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
        
        result = error_handler.retry_with_backoff(
            failing_function, 
            retry_config=retry_config
        )
        
        self.assertEqual(result, "成功")
        self.assertEqual(call_count, 3)
        
        print("✓ 错误处理功能正常")
    
    def test_audio_cache(self):
        """测试音频缓存"""
        print("\n测试音频缓存...")
        
        audio_cache = OptimizedAudioCache()
        
        # 测试缓存操作 - 使用正确的方法名
        # 模拟音频段对象
        class MockAudioSegment:
            def __init__(self, data):
                self.raw_data = data
                
        test_audio_segment = MockAudioSegment(b"fake_audio_data")
        
        # 使用 put 方法添加缓存
        audio_cache.put("测试文本", "zh-CN-YunjianNeural", 1.2, test_audio_segment)
        
        # 测试缓存获取
        cached_data = audio_cache.get("测试文本", "zh-CN-YunjianNeural", 1.2)
        self.assertIsNotNone(cached_data)
        
        # 测试缓存统计
        stats = audio_cache.get_stats()
        self.assertIn('hits', stats)
        self.assertIn('misses', stats)
        
        print("✓ 音频缓存功能正常")
    
    def test_health_monitor(self):
        """测试健康监控"""
        print("\n测试健康监控...")
        
        health_monitor = HealthMonitor()
        
        # 测试系统状态获取 - 使用同步方法
        import asyncio
        
        async def get_status():
            return await health_monitor.get_system_status()
        
        # 运行异步方法
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        status = loop.run_until_complete(get_status())
        
        self.assertIsNotNone(status)
        self.assertIsNotNone(status.status)
        self.assertIsNotNone(status.timestamp)
        
        print("✓ 健康监控功能正常")
    
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
    
    def test_text_processing_workflow(self):
        """测试文本处理工作流"""
        print("\n测试文本处理工作流...")
        
        # 创建临时字典文件
        temp_dict_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_dict_file.close()
        self.temp_files.append(temp_dict_file.name)
        
        dictionary = DictionaryService(temp_dict_file.name)
        
        # 添加字典规则
        dictionary.add_rule(
            pattern=r'\bAPI\b',
            replacement='A P I',
            rule_type='pronunciation'
        )
        
        dictionary.add_rule(
            pattern=r'GitHub',
            replacement='吉特哈布',
            rule_type='pronunciation'
        )
        
        # 处理包含多种元素的文本
        input_text = '这是一个 GitHub API 的使用示例："你好世界"这是对话。'
        
        # 应用字典规则
        processed_text = dictionary.process_text(input_text)
        
        # 验证处理结果
        self.assertIn('吉特哈布', processed_text)
        self.assertIn('A P I', processed_text)
        
        # 模拟文本分段处理
        segments = self._segment_text(processed_text)
        
        # 验证分段结果
        self.assertGreater(len(segments), 0)
        
        # 检查是否正确识别了旁白和对话
        has_narration = any(seg['tag'] == 'narration' for seg in segments)
        has_dialogue = any(seg['tag'] == 'dialogue' for seg in segments)
        
        self.assertTrue(has_narration)
        self.assertTrue(has_dialogue)
        
        print("✓ 文本处理工作流正常")
    
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


def run_simple_integration_tests():
    """运行简化的集成测试"""
    print("=" * 60)
    print("开始简化集成测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试方法
    test_methods = [
        'test_config_manager',
        'test_dictionary_service',
        'test_error_handler',
        'test_audio_cache',
        'test_health_monitor',
        'test_logging_system',
        'test_text_processing_workflow'
    ]
    
    for method in test_methods:
        test_suite.addTest(SimpleIntegrationTest(method))
    
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
    success = run_simple_integration_tests()
    sys.exit(0 if success else 1)