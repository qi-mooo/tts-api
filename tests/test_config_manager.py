"""
ConfigManager 单元测试
测试配置管理器的各项功能
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from config.config_manager import ConfigManager, TTSConfig, LoggingConfig


class TestConfigManager(unittest.TestCase):
    """ConfigManager 测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
        
    def tearDown(self):
        """测试后清理"""
        if self.config_file.exists():
            self.config_file.unlink()
        os.rmdir(self.temp_dir)
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 验证默认配置值
        self.assertEqual(config_manager.tts.narration_voice, "zh-CN-YunjianNeural")
        self.assertEqual(config_manager.tts.dialogue_voice, "zh-CN-XiaoyiNeural")
        self.assertEqual(config_manager.tts.default_speed, 1.2)
        self.assertEqual(config_manager.logging.level, "INFO")
        self.assertEqual(config_manager.system.port, 5000)
        
        # 验证配置文件已创建
        self.assertTrue(self.config_file.exists())
    
    def test_init_with_existing_config(self):
        """测试使用现有配置文件初始化"""
        # 创建测试配置文件
        test_config = {
            "tts": {
                "narration_voice": "zh-CN-TestVoice",
                "default_speed": 1.5
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        config_manager = ConfigManager(str(self.config_file))
        
        # 验证配置已正确加载
        self.assertEqual(config_manager.tts.narration_voice, "zh-CN-TestVoice")
        self.assertEqual(config_manager.tts.default_speed, 1.5)
        self.assertEqual(config_manager.logging.level, "DEBUG")
        
        # 验证未设置的配置使用默认值
        self.assertEqual(config_manager.tts.dialogue_voice, "zh-CN-XiaoyiNeural")
    
    def test_get_config_value(self):
        """测试获取配置值"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 测试获取存在的配置
        self.assertEqual(config_manager.get("tts.narration_voice"), "zh-CN-YunjianNeural")
        self.assertEqual(config_manager.get("tts.default_speed"), 1.2)
        
        # 测试获取不存在的配置
        self.assertIsNone(config_manager.get("nonexistent.key"))
        self.assertEqual(config_manager.get("nonexistent.key", "default"), "default")
    
    def test_set_config_value(self):
        """测试设置配置值"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 设置配置值
        config_manager.set("tts.narration_voice", "zh-CN-NewVoice")
        config_manager.set("tts.default_speed", 1.8)
        
        # 验证配置已更新
        self.assertEqual(config_manager.tts.narration_voice, "zh-CN-NewVoice")
        self.assertEqual(config_manager.tts.default_speed, 1.8)
        self.assertEqual(config_manager.get("tts.narration_voice"), "zh-CN-NewVoice")
    
    def test_config_validation(self):
        """测试配置验证"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 测试有效配置
        self.assertTrue(config_manager.validate())
        
        # 测试无效的语速
        config_manager.tts.default_speed = -1
        self.assertFalse(config_manager.validate())
        
        # 恢复有效值
        config_manager.tts.default_speed = 1.2
        self.assertTrue(config_manager.validate())
        
        # 测试无效的日志级别
        config_manager.logging.level = "INVALID"
        self.assertFalse(config_manager.validate())
        
        # 恢复有效值
        config_manager.logging.level = "INFO"
        self.assertTrue(config_manager.validate())
        
        # 测试无效的端口号
        config_manager.system.port = 70000
        self.assertFalse(config_manager.validate())
    
    def test_save_config(self):
        """测试保存配置"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 修改配置
        config_manager.tts.narration_voice = "zh-CN-SavedVoice"
        config_manager.logging.level = "DEBUG"
        
        # 保存配置
        config_manager.save()
        
        # 验证文件内容
        with open(self.config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config["tts"]["narration_voice"], "zh-CN-SavedVoice")
        self.assertEqual(saved_config["logging"]["level"], "DEBUG")
    
    def test_reload_config(self):
        """测试重新加载配置"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 修改内存中的配置
        config_manager.tts.narration_voice = "zh-CN-MemoryVoice"
        
        # 直接修改配置文件
        new_config = {
            "tts": {
                "narration_voice": "zh-CN-FileVoice",
                "default_speed": 2.0
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f)
        
        # 重新加载配置
        config_manager.reload()
        
        # 验证配置已从文件重新加载
        self.assertEqual(config_manager.tts.narration_voice, "zh-CN-FileVoice")
        self.assertEqual(config_manager.tts.default_speed, 2.0)
    
    @patch.dict(os.environ, {
        'TTS_NARRATION_VOICE': 'zh-CN-EnvVoice',
        'TTS_DEFAULT_SPEED': '1.8',
        'LOG_LEVEL': 'DEBUG',
        'SYSTEM_PORT': '8080'
    })
    def test_env_variables_override(self):
        """测试环境变量覆盖配置文件"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 验证环境变量已覆盖默认配置
        self.assertEqual(config_manager.tts.narration_voice, "zh-CN-EnvVoice")
        self.assertEqual(config_manager.tts.default_speed, 1.8)
        self.assertEqual(config_manager.logging.level, "DEBUG")
        self.assertEqual(config_manager.system.port, 8080)
    
    def test_config_watcher(self):
        """测试配置变更观察者"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 记录观察者调用
        watcher_calls = []
        
        def test_watcher(key, value):
            watcher_calls.append((key, value))
        
        # 添加观察者
        config_manager.add_watcher(test_watcher)
        
        # 修改配置
        config_manager.set("tts.narration_voice", "zh-CN-WatchedVoice")
        
        # 验证观察者被调用
        self.assertEqual(len(watcher_calls), 1)
        self.assertEqual(watcher_calls[0], ("tts.narration_voice", "zh-CN-WatchedVoice"))
        
        # 移除观察者
        config_manager.remove_watcher(test_watcher)
        
        # 再次修改配置
        config_manager.set("tts.default_speed", 2.5)
        
        # 验证观察者未被调用
        self.assertEqual(len(watcher_calls), 1)
    
    def test_get_config_dict(self):
        """测试获取完整配置字典"""
        config_manager = ConfigManager(str(self.config_file))
        
        config_dict = config_manager.get_config_dict()
        
        # 验证返回的字典包含所有配置部分
        self.assertIn("tts", config_dict)
        self.assertIn("logging", config_dict)
        self.assertIn("admin", config_dict)
        self.assertIn("dictionary", config_dict)
        self.assertIn("system", config_dict)
        
        # 验证配置值正确
        self.assertEqual(config_dict["tts"]["narration_voice"], "zh-CN-YunjianNeural")
        self.assertEqual(config_dict["logging"]["level"], "INFO")
    
    def test_thread_safety(self):
        """测试线程安全性"""
        import threading
        import time
        
        config_manager = ConfigManager(str(self.config_file))
        results = []
        
        def worker():
            for i in range(10):
                config_manager.set(f"test.key{i}", f"value{i}")
                value = config_manager.get(f"test.key{i}")
                results.append(value)
                time.sleep(0.001)  # 模拟并发
        
        # 创建多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有数据竞争问题
        self.assertEqual(len(results), 50)  # 5个线程 * 10次操作


if __name__ == '__main__':
    unittest.main()