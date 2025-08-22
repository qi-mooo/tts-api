"""
音频缓存系统单元测试
测试优化的音频缓存功能，包括统计监控和内存管理
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# 模拟 AudioSegment
class MockAudioSegment:
    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data
    
    def __len__(self):
        return len(self.raw_data)
    
    def __add__(self, other):
        return MockAudioSegment(self.raw_data + other.raw_data)


class TestOptimizedAudioCache(unittest.TestCase):
    """优化音频缓存测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.write('''{
            "tts": {
                "cache_size_limit": 1024,
                "cache_time_limit": 60
            }
        }''')
        self.temp_config.close()
        
        # 模拟配置管理器
        with patch('audio_cache.audio_cache.config_manager') as mock_config:
            mock_config.tts.cache_size_limit = 1024
            mock_config.tts.cache_time_limit = 60
            mock_config.add_watcher = Mock()
            mock_config.remove_watcher = Mock()
            
            # 模拟日志
            with patch('audio_cache.audio_cache.get_logger') as mock_logger:
                mock_logger.return_value = Mock()
                
                from audio_cache.audio_cache import OptimizedAudioCache
                self.cache = OptimizedAudioCache()
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'temp_config'):
            os.unlink(self.temp_config.name)
    
    def _create_mock_audio(self, size: int) -> MockAudioSegment:
        """创建指定大小的模拟音频"""
        return MockAudioSegment(b'x' * size)
    
    def test_cache_initialization(self):
        """测试缓存初始化"""
        self.assertEqual(self.cache.size_limit, 1024)
        self.assertEqual(self.cache.time_limit, 60)
        self.assertEqual(len(self.cache), 0)
        self.assertEqual(self.cache._current_size, 0)
    
    def test_put_and_get_audio(self):
        """测试音频存储和获取"""
        audio = self._create_mock_audio(100)
        
        # 存储音频
        self.cache.put("hello", "voice1", 1.0, audio)
        
        # 获取音频
        retrieved = self.cache.get("hello", "voice1", 1.0)
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved.raw_data), 100)
        
        # 验证统计信息
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['entry_count'], 1)
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        result = self.cache.get("nonexistent", "voice1", 1.0)
        self.assertIsNone(result)
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['total_requests'], 1)
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        audio1 = self._create_mock_audio(50)
        audio2 = self._create_mock_audio(50)
        
        # 相同参数应该使用相同的键
        self.cache.put("text", "voice", 1.0, audio1)
        retrieved = self.cache.get("text", "voice", 1.0)
        self.assertIsNotNone(retrieved)
        
        # 不同参数应该使用不同的键
        self.cache.put("text", "voice", 1.5, audio2)
        self.assertEqual(len(self.cache), 2)
    
    def test_size_limit_enforcement(self):
        """测试大小限制强制执行"""
        # 添加音频直到超过限制
        audio1 = self._create_mock_audio(400)
        audio2 = self._create_mock_audio(400)
        audio3 = self._create_mock_audio(400)
        
        self.cache.put("text1", "voice", 1.0, audio1)
        self.cache.put("text2", "voice", 1.0, audio2)
        self.cache.put("text3", "voice", 1.0, audio3)  # 这应该触发LRU清理
        
        # 验证最旧的条目被移除
        self.assertIsNone(self.cache.get("text1", "voice", 1.0))
        self.assertIsNotNone(self.cache.get("text2", "voice", 1.0))
        self.assertIsNotNone(self.cache.get("text3", "voice", 1.0))
        
        stats = self.cache.get_stats()
        self.assertGreater(stats['evictions'], 0)
    
    def test_time_limit_enforcement(self):
        """测试时间限制强制执行"""
        # 使用较短的时间限制进行测试
        with patch('audio_cache.audio_cache.config_manager') as mock_config:
            mock_config.tts.cache_size_limit = 1024
            mock_config.tts.cache_time_limit = 1  # 1秒过期
            mock_config.add_watcher = Mock()
            mock_config.remove_watcher = Mock()
            
            with patch('audio_cache.audio_cache.get_logger') as mock_logger:
                mock_logger.return_value = Mock()
                
                from audio_cache.audio_cache import OptimizedAudioCache
                short_cache = OptimizedAudioCache()
        
        audio = self._create_mock_audio(100)
        short_cache.put("text", "voice", 1.0, audio)
        
        # 立即获取应该成功
        self.assertIsNotNone(short_cache.get("text", "voice", 1.0))
        
        # 等待过期
        time.sleep(1.1)
        
        # 现在应该返回None（过期）
        self.assertIsNone(short_cache.get("text", "voice", 1.0))
    
    def test_lru_eviction_order(self):
        """测试LRU淘汰顺序"""
        # 使用更小的缓存限制确保淘汰发生
        with patch('audio_cache.audio_cache.config_manager') as mock_config:
            mock_config.tts.cache_size_limit = 700  # 只能容纳2个300字节的条目
            mock_config.tts.cache_time_limit = 60
            mock_config.add_watcher = Mock()
            mock_config.remove_watcher = Mock()
            
            with patch('audio_cache.audio_cache.get_logger') as mock_logger:
                mock_logger.return_value = Mock()
                
                from audio_cache.audio_cache import OptimizedAudioCache
                small_cache = OptimizedAudioCache()
        
        audio1 = self._create_mock_audio(300)
        audio2 = self._create_mock_audio(300)
        audio3 = self._create_mock_audio(300)
        
        # 添加两个条目（应该刚好填满缓存）
        small_cache.put("text1", "voice", 1.0, audio1)
        small_cache.put("text2", "voice", 1.0, audio2)
        
        # 访问第一个条目（使其变为最近使用）
        small_cache.get("text1", "voice", 1.0)
        
        # 添加第三个条目，应该淘汰text2（最少使用）
        small_cache.put("text3", "voice", 1.0, audio3)
        
        self.assertIsNotNone(small_cache.get("text1", "voice", 1.0))
        self.assertIsNone(small_cache.get("text2", "voice", 1.0))
        self.assertIsNotNone(small_cache.get("text3", "voice", 1.0))
    
    def test_cache_update_existing_entry(self):
        """测试更新现有缓存条目"""
        audio1 = self._create_mock_audio(100)
        audio2 = self._create_mock_audio(200)
        
        # 添加初始条目
        self.cache.put("text", "voice", 1.0, audio1)
        initial_stats = self.cache.get_stats()
        
        # 更新相同键的条目
        self.cache.put("text", "voice", 1.0, audio2)
        
        # 验证条目被更新而不是添加新条目
        self.assertEqual(len(self.cache), 1)
        retrieved = self.cache.get("text", "voice", 1.0)
        self.assertEqual(len(retrieved.raw_data), 200)
    
    def test_cache_statistics(self):
        """测试缓存统计功能"""
        audio = self._create_mock_audio(100)
        
        # 执行一些操作
        self.cache.put("text1", "voice", 1.0, audio)
        self.cache.get("text1", "voice", 1.0)  # 命中
        self.cache.get("text2", "voice", 1.0)  # 未命中
        
        stats = self.cache.get_stats()
        
        # 验证基本统计
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['total_requests'], 2)
        self.assertEqual(stats['entry_count'], 1)
        self.assertEqual(stats['total_size_bytes'], 100)
        
        # 验证计算的统计
        self.assertAlmostEqual(stats['hit_rate'], 0.5)
        self.assertGreater(stats['memory_usage_percent'], 0)
        self.assertEqual(stats['average_entry_size'], 100)
    
    def test_cache_entries_info(self):
        """测试缓存条目信息获取"""
        audio = self._create_mock_audio(100)
        self.cache.put("text", "voice", 1.0, audio)
        
        entries_info = self.cache.get_cache_entries_info()
        self.assertEqual(len(entries_info), 1)
        
        entry_info = entries_info[0]
        self.assertIn('cache_key', entry_info)
        self.assertEqual(entry_info['size_bytes'], 100)
        self.assertAlmostEqual(entry_info['size_kb'], 0.1, places=1)
        self.assertGreaterEqual(entry_info['age_seconds'], 0)
        self.assertEqual(entry_info['access_count'], 1)
        self.assertFalse(entry_info['is_expired'])
    
    def test_cache_clear(self):
        """测试缓存清空功能"""
        audio = self._create_mock_audio(100)
        self.cache.put("text", "voice", 1.0, audio)
        
        # 验证缓存有内容
        self.assertEqual(len(self.cache), 1)
        self.assertGreater(self.cache._current_size, 0)
        
        # 清空缓存
        self.cache.clear()
        
        # 验证缓存已清空
        self.assertEqual(len(self.cache), 0)
        self.assertEqual(self.cache._current_size, 0)
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['entry_count'], 0)
        self.assertEqual(stats['total_size_bytes'], 0)
    
    def test_cache_optimization(self):
        """测试缓存优化功能"""
        # 添加一些条目
        for i in range(5):
            audio = self._create_mock_audio(100)
            self.cache.put(f"text{i}", "voice", 1.0, audio)
        
        initial_count = len(self.cache)
        
        # 执行优化
        result = self.cache.optimize()
        
        # 验证优化结果
        self.assertIn('entries_removed', result)
        self.assertIn('bytes_freed', result)
        self.assertIn('memory_usage_before', result)
        self.assertIn('memory_usage_after', result)
    
    def test_thread_safety(self):
        """测试线程安全性"""
        def worker(thread_id):
            for i in range(10):
                audio = self._create_mock_audio(50)
                self.cache.put(f"text{thread_id}_{i}", "voice", 1.0, audio)
                self.cache.get(f"text{thread_id}_{i}", "voice", 1.0)
        
        # 创建多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证缓存状态一致性
        stats = self.cache.get_stats()
        self.assertGreaterEqual(stats['total_requests'], 30)  # 至少30个请求
    
    def test_config_change_handling(self):
        """测试配置变更处理"""
        # 模拟配置变更
        self.cache._on_config_change("tts.cache_size_limit", 2048)
        self.assertEqual(self.cache.size_limit, 2048)
        
        self.cache._on_config_change("tts.cache_time_limit", 120)
        self.assertEqual(self.cache.time_limit, 120)
    
    def test_invalid_audio_handling(self):
        """测试无效音频处理"""
        # 测试None音频
        self.cache.put("text", "voice", 1.0, None)
        self.assertEqual(len(self.cache), 0)
        
        # 测试无raw_data属性的对象
        invalid_audio = Mock()
        del invalid_audio.raw_data
        self.cache.put("text", "voice", 1.0, invalid_audio)
        self.assertEqual(len(self.cache), 0)
    
    def test_cache_contains_and_len(self):
        """测试缓存包含检查和长度"""
        audio = self._create_mock_audio(100)
        cache_key = self.cache._generate_cache_key("text", "voice", 1.0)
        
        # 初始状态
        self.assertEqual(len(self.cache), 0)
        self.assertNotIn(cache_key, self.cache)
        
        # 添加条目后
        self.cache.put("text", "voice", 1.0, audio)
        self.assertEqual(len(self.cache), 1)
        self.assertIn(cache_key, self.cache)


class TestCacheDataClasses(unittest.TestCase):
    """测试缓存数据类"""
    
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        from audio_cache.audio_cache import CacheEntry
        
        audio = MockAudioSegment(b'test')
        entry = CacheEntry(
            audio_segment=audio,
            timestamp=time.time(),
            size_bytes=100,
            access_count=1,
            last_access=time.time(),
            cache_key="test_key"
        )
        
        self.assertEqual(entry.size_bytes, 100)
        self.assertEqual(entry.access_count, 1)
        self.assertEqual(entry.cache_key, "test_key")
    
    def test_cache_stats_creation(self):
        """测试缓存统计创建"""
        from audio_cache.audio_cache import CacheStats
        
        stats = CacheStats()
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)
        self.assertEqual(stats.hit_rate, 0.0)
        
        # 测试带参数创建
        stats = CacheStats(hits=10, misses=5, total_requests=15)
        self.assertEqual(stats.hits, 10)
        self.assertEqual(stats.misses, 5)
        self.assertEqual(stats.total_requests, 15)


if __name__ == '__main__':
    unittest.main()