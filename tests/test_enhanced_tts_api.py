"""
增强版 TTS API 集成测试

测试增强版 API 的错误处理、参数验证、字典服务集成等功能。
"""

import unittest
import json
import time
import tempfile
import os
from unittest.mock import patch, MagicMock
from flask import Flask
from io import BytesIO

# 导入测试目标
from enhanced_tts_api import (
    RequestValidator, EnhancedSpeechRule, EnhancedAudioCache, 
    EnhancedTTSService, enhanced_tts_service
)
from app_enhanced import create_enhanced_app
from error_handler.exceptions import ValidationError, AudioGenerationError
from pydub import AudioSegment


class TestRequestValidator(unittest.TestCase):
    """请求参数验证器测试"""
    
    def setUp(self):
        self.validator = RequestValidator()
    
    def test_valid_request(self):
        """测试有效请求参数"""
        args = {
            'text': '这是一个测试文本',
            'speed': '1.2',
            'narr': 'zh-CN-YunjianNeural',
            'dlg': 'zh-CN-XiaoyiNeural'
        }
        
        result = self.validator.validate_tts_request(args)
        
        self.assertEqual(result['text'], '这是一个测试文本')
        self.assertEqual(result['speed'], 1.2)
        self.assertEqual(result['narr_voice'], 'zh-CN-YunjianNeural')
        self.assertEqual(result['dlg_voice'], 'zh-CN-XiaoyiNeural')
    
    def test_empty_text(self):
        """测试空文本参数"""
        args = {'text': ''}
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_tts_request(args)
        
        self.assertEqual(context.exception.error_code, 'VAL_001')
        self.assertIn('文本参数不能为空', context.exception.message)
    
    def test_text_too_long(self):
        """测试文本过长"""
        args = {'text': 'a' * 5001}
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_tts_request(args)
        
        self.assertIn('文本长度不能超过5000个字符', context.exception.message)
    
    def test_invalid_speed(self):
        """测试无效语速"""
        args = {'text': '测试', 'speed': '5.0'}
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_tts_request(args)
        
        self.assertIn('语速必须在0.1到3.0之间', context.exception.message)
    
    def test_invalid_voice_format(self):
        """测试无效语音格式"""
        args = {'text': '测试', 'narr': 'invalid-voice'}
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_tts_request(args)
        
        self.assertIn('旁白语音名称格式无效', context.exception.message)
    
    def test_default_values(self):
        """测试默认值"""
        args = {'text': '测试文本'}
        
        result = self.validator.validate_tts_request(args)
        
        self.assertEqual(result['text'], '测试文本')
        self.assertIsInstance(result['speed'], float)
        self.assertIsNotNone(result['narr_voice'])
        self.assertIsNotNone(result['dlg_voice'])


class TestEnhancedSpeechRule(unittest.TestCase):
    """增强版语音规则测试"""
    
    def setUp(self):
        self.speech_rule = EnhancedSpeechRule()
    
    def test_narration_only(self):
        """测试纯旁白文本"""
        text = "这是一段旁白文本。"
        result = self.speech_rule.handle_text(text)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], text)
        self.assertEqual(result[0]['tag'], 'narration')
    
    def test_dialogue_only(self):
        """测试纯对话文本"""
        text = '"这是一段对话文本。"'
        result = self.speech_rule.handle_text(text)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], '这是一段对话文本。')
        self.assertEqual(result[0]['tag'], 'dialogue')
    
    def test_mixed_content(self):
        """测试混合内容"""
        text = '旁白开始"对话内容"旁白结束'
        result = self.speech_rule.handle_text(text)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['tag'], 'narration')
        self.assertEqual(result[1]['tag'], 'dialogue')
        self.assertEqual(result[2]['tag'], 'narration')
    
    def test_empty_segments(self):
        """测试空段落处理"""
        text = '""'
        result = self.speech_rule.handle_text(text)
        
        # 空段落应该被过滤掉
        self.assertEqual(len(result), 0)


class TestEnhancedAudioCache(unittest.TestCase):
    """增强版音频缓存测试"""
    
    def setUp(self):
        # 创建小容量缓存用于测试
        self.cache = EnhancedAudioCache(size_limit=1024, time_limit=60)
    
    def create_mock_audio_segment(self, size_bytes=100):
        """创建模拟音频段"""
        mock_segment = MagicMock(spec=AudioSegment)
        mock_segment.raw_data = b'x' * size_bytes
        return mock_segment
    
    def test_add_and_combine(self):
        """测试添加和组合音频"""
        segment1 = self.create_mock_audio_segment(100)
        segment2 = self.create_mock_audio_segment(100)
        
        self.cache.add(segment1)
        self.cache.add(segment2)
        
        # 模拟 sum() 操作
        with patch('builtins.sum') as mock_sum:
            mock_sum.return_value = MagicMock()
            result = self.cache.combine()
            
            self.assertIsNotNone(result)
            mock_sum.assert_called_once()
    
    def test_size_limit_eviction(self):
        """测试大小限制驱逐"""
        # 添加超过限制的音频段
        for i in range(15):  # 15 * 100 = 1500 > 1024
            segment = self.create_mock_audio_segment(100)
            self.cache.add(segment)
        
        # 缓存大小应该不超过限制
        self.assertLessEqual(self.cache.current_size, self.cache.size_limit)
        self.assertGreater(self.cache.stats['evictions'], 0)
    
    def test_time_limit_cleanup(self):
        """测试时间限制清理"""
        # 创建短时间限制的缓存
        short_cache = EnhancedAudioCache(size_limit=1024, time_limit=1)
        
        segment = self.create_mock_audio_segment(100)
        short_cache.add(segment)
        
        # 等待超过时间限制
        time.sleep(1.1)
        
        # 添加新段落应该清理过期的
        new_segment = self.create_mock_audio_segment(100)
        short_cache.add(new_segment)
        
        # 检查统计信息
        stats = short_cache.get_stats()
        self.assertGreaterEqual(stats['stats']['evictions'], 0)
    
    def test_cache_stats(self):
        """测试缓存统计"""
        segment = self.create_mock_audio_segment(100)
        self.cache.add(segment)
        
        # 测试命中
        with patch('builtins.sum') as mock_sum:
            mock_sum.return_value = MagicMock()
            self.cache.combine()
        
        # 测试未命中
        empty_cache = EnhancedAudioCache()
        empty_cache.combine()
        
        stats = self.cache.get_stats()
        self.assertIn('hit_rate', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('stats', stats)


class TestEnhancedTTSService(unittest.TestCase):
    """增强版 TTS 服务测试"""
    
    def setUp(self):
        # 使用临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        
        # 创建测试用的 TTS 服务
        with patch('config.config_manager.config_manager') as mock_config:
            mock_config.tts.cache_size_limit = 1024
            mock_config.tts.cache_time_limit = 60
            mock_config.system.max_workers = 2
            self.service = EnhancedTTSService()
    
    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('enhanced_tts_api.edge_tts')
    def test_fetch_audio_success(self, mock_edge_tts):
        """测试音频生成成功"""
        # 模拟 edge-tts 响应
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate
        
        # 模拟音频数据流
        async def mock_stream():
            yield {"type": "audio", "data": b"fake_audio_data"}
        
        mock_communicate.stream.return_value = mock_stream()
        
        # 模拟 AudioSegment
        with patch('enhanced_tts_api.AudioSegment') as mock_audio_segment:
            mock_segment = MagicMock()
            mock_audio_segment.from_file.return_value = mock_segment
            
            segment = {"text": "测试文本", "tag": "narration"}
            result = self.service._fetch_audio(segment, 1.2, "zh-CN-YunjianNeural")
            
            self.assertEqual(result, mock_segment)
    
    @patch('enhanced_tts_api.edge_tts')
    def test_fetch_audio_failure(self, mock_edge_tts):
        """测试音频生成失败"""
        # 模拟 edge-tts 抛出异常
        mock_edge_tts.Communicate.side_effect = Exception("Network error")
        
        segment = {"text": "测试文本", "tag": "narration"}
        
        with self.assertRaises(AudioGenerationError):
            self.service._fetch_audio(segment, 1.2, "zh-CN-YunjianNeural")
    
    def test_get_voice_for_segment(self):
        """测试段落语音选择"""
        params = {
            'narr_voice': 'narr-voice',
            'dlg_voice': 'dlg-voice',
            'all_voice': None
        }
        
        # 测试旁白
        narr_segment = {'tag': 'narration'}
        voice = self.service._get_voice_for_segment(narr_segment, params)
        self.assertEqual(voice, 'narr-voice')
        
        # 测试对话
        dlg_segment = {'tag': 'dialogue'}
        voice = self.service._get_voice_for_segment(dlg_segment, params)
        self.assertEqual(voice, 'dlg-voice')
        
        # 测试统一语音
        params['all_voice'] = 'all-voice'
        voice = self.service._get_voice_for_segment(narr_segment, params)
        self.assertEqual(voice, 'all-voice')


class TestEnhancedFlaskApp(unittest.TestCase):
    """增强版 Flask 应用集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = create_enhanced_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_index_endpoint(self):
        """测试根路径端点"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['service'], 'Enhanced TTS API')
        self.assertIn('endpoints', data)
    
    def test_api_status_endpoint(self):
        """测试 API 状态端点"""
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('cache_stats', data)
        self.assertIn('config', data)
    
    def test_dictionary_rules_endpoint(self):
        """测试字典规则端点"""
        # 获取规则
        response = self.client.get('/api/dictionary/rules')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('rules', data)
    
    def test_dictionary_test_endpoint(self):
        """测试字典测试端点"""
        test_data = {'text': '这是测试文本'}
        
        response = self.client.post(
            '/api/dictionary/test',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('original_text', data)
        self.assertIn('processed_text', data)
    
    def test_config_endpoint(self):
        """测试配置端点"""
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('config', data)
        
        # 确保敏感信息被隐藏
        if 'admin' in data['config']:
            self.assertNotIn('password_hash', data['config']['admin'])
            self.assertNotIn('secret_key', data['config']['admin'])
    
    @patch('enhanced_tts_api.enhanced_tts_service')
    def test_api_endpoint_validation_error(self, mock_service):
        """测试 API 端点参数验证错误"""
        # 模拟验证错误
        mock_service.process_request.side_effect = ValidationError(
            field_name='text',
            message='文本参数不能为空'
        )
        
        response = self.client.get('/api?text=')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    @patch('enhanced_tts_api.enhanced_tts_service')
    def test_api_endpoint_success(self, mock_service):
        """测试 API 端点成功响应"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.mimetype = 'audio/webm'
        mock_service.process_request.return_value = mock_response
        
        response = self.client.get('/api?text=测试文本')
        
        # 验证服务被调用
        mock_service.process_request.assert_called_once()
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        # 应该返回 JSON 响应
        data = json.loads(response.data)
        self.assertIn('status', data)
    
    def test_request_headers(self):
        """测试请求头处理"""
        response = self.client.get('/')
        
        # 检查响应头
        self.assertIn('X-Request-ID', response.headers)
        self.assertIn('X-Processing-Time', response.headers)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 访问不存在的端点
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """设置集成测试环境"""
        self.app = create_enhanced_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('enhanced_tts_api.edge_tts')
    @patch('enhanced_tts_api.AudioSegment')
    def test_full_tts_pipeline(self, mock_audio_segment, mock_edge_tts):
        """测试完整的 TTS 处理流程"""
        # 模拟 edge-tts
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate
        
        async def mock_stream():
            yield {"type": "audio", "data": b"fake_audio_data"}
        
        mock_communicate.stream.return_value = mock_stream()
        
        # 模拟 AudioSegment
        mock_segment = MagicMock()
        mock_segment.raw_data = b"fake_raw_data"
        mock_audio_segment.from_file.return_value = mock_segment
        
        # 模拟音频合成
        mock_combined = MagicMock()
        mock_combined.__len__ = lambda x: 1000
        
        with patch('builtins.sum', return_value=mock_combined):
            # 发送请求
            response = self.client.get('/api?text=这是一个"测试文本"&speed=1.2')
            
            # 验证响应
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'audio/webm')
            self.assertIn('X-Request-ID', response.headers)
    
    def test_dictionary_integration(self):
        """测试字典服务集成"""
        # 添加字典规则
        rule_data = {
            'pattern': 'test',
            'replacement': '测试',
            'type': 'pronunciation'
        }
        
        response = self.client.post(
            '/api/dictionary/rules',
            data=json.dumps(rule_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 测试字典处理
        test_data = {'text': 'This is a test'}
        
        response = self.client.post(
            '/api/dictionary/test',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])


if __name__ == '__main__':
    unittest.main(verbosity=2)