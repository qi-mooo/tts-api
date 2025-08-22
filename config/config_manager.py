"""
配置管理器 - 集中管理所有配置参数
支持环境变量、配置文件和热重载功能
"""

import json
import os
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging


@dataclass
class TTSConfig:
    """TTS相关配置"""
    narration_voice: str = "zh-CN-YunjianNeural"
    dialogue_voice: str = "zh-CN-XiaoyiNeural"
    default_speed: float = 1.2
    cache_size_limit: int = 10485760  # 10MB
    cache_time_limit: int = 1200  # 20分钟


@dataclass
class LoggingConfig:
    """日志相关配置"""
    level: str = "INFO"
    file: str = "logs/app.log"
    max_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class AdminConfig:
    """管理控制台配置"""
    username: str = "admin"
    password_hash: str = ""  # 需要在初始化时设置
    session_timeout: int = 3600  # 1小时
    secret_key: str = ""  # Flask session密钥


@dataclass
class DictionaryConfig:
    """字典服务配置"""
    enabled: bool = True
    rules_file: str = "dictionary/rules.json"


@dataclass
class SystemConfig:
    """系统配置"""
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    max_workers: int = 10


class ConfigManager:
    """配置管理器 - 提供集中的配置管理功能"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self._lock = threading.RLock()
        self._config_data = {}
        self._watchers = []
        
        # 初始化配置对象
        self.tts = TTSConfig()
        self.logging = LoggingConfig()
        self.admin = AdminConfig()
        self.dictionary = DictionaryConfig()
        self.system = SystemConfig()
        
        # 加载配置
        self._load_config()
        self._load_env_variables()
        
    def _load_config(self) -> None:
        """从配置文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                    self._apply_config()
            else:
                # 创建默认配置文件
                self._create_default_config()
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        default_config = {
            "tts": asdict(self.tts),
            "logging": asdict(self.logging),
            "admin": asdict(self.admin),
            "dictionary": asdict(self.dictionary),
            "system": asdict(self.system)
        }
        
        # 确保目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self._config_data = default_config
    
    def _apply_config(self) -> None:
        """应用配置数据到配置对象"""
        if "tts" in self._config_data:
            for key, value in self._config_data["tts"].items():
                if hasattr(self.tts, key):
                    setattr(self.tts, key, value)
        
        if "logging" in self._config_data:
            for key, value in self._config_data["logging"].items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        
        if "admin" in self._config_data:
            for key, value in self._config_data["admin"].items():
                if hasattr(self.admin, key):
                    setattr(self.admin, key, value)
        
        if "dictionary" in self._config_data:
            for key, value in self._config_data["dictionary"].items():
                if hasattr(self.dictionary, key):
                    setattr(self.dictionary, key, value)
        
        if "system" in self._config_data:
            for key, value in self._config_data["system"].items():
                if hasattr(self.system, key):
                    setattr(self.system, key, value)
    
    def _load_env_variables(self) -> None:
        """从环境变量加载配置（优先级高于配置文件）"""
        # TTS配置
        if os.getenv("TTS_NARRATION_VOICE"):
            self.tts.narration_voice = os.getenv("TTS_NARRATION_VOICE")
        if os.getenv("TTS_DIALOGUE_VOICE"):
            self.tts.dialogue_voice = os.getenv("TTS_DIALOGUE_VOICE")
        if os.getenv("TTS_DEFAULT_SPEED"):
            self.tts.default_speed = float(os.getenv("TTS_DEFAULT_SPEED"))
        if os.getenv("TTS_CACHE_SIZE_LIMIT"):
            self.tts.cache_size_limit = int(os.getenv("TTS_CACHE_SIZE_LIMIT"))
        if os.getenv("TTS_CACHE_TIME_LIMIT"):
            self.tts.cache_time_limit = int(os.getenv("TTS_CACHE_TIME_LIMIT"))
        
        # 日志配置
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_FILE"):
            self.logging.file = os.getenv("LOG_FILE")
        
        # 管理员配置
        if os.getenv("ADMIN_USERNAME"):
            self.admin.username = os.getenv("ADMIN_USERNAME")
        if os.getenv("ADMIN_PASSWORD_HASH"):
            self.admin.password_hash = os.getenv("ADMIN_PASSWORD_HASH")
        if os.getenv("ADMIN_SECRET_KEY"):
            self.admin.secret_key = os.getenv("ADMIN_SECRET_KEY")
        
        # 系统配置
        if os.getenv("SYSTEM_DEBUG"):
            self.system.debug = os.getenv("SYSTEM_DEBUG").lower() == "true"
        if os.getenv("SYSTEM_HOST"):
            self.system.host = os.getenv("SYSTEM_HOST")
        if os.getenv("SYSTEM_PORT"):
            self.system.port = int(os.getenv("SYSTEM_PORT"))
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        with self._lock:
            keys = key.split('.')
            value = self._config_data
            
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的嵌套键"""
        with self._lock:
            keys = key.split('.')
            config = self._config_data
            
            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
            # 重新应用配置
            self._apply_config()
            
            # 通知观察者
            self._notify_watchers(key, value)
    
    def reload(self) -> None:
        """重新加载配置文件"""
        with self._lock:
            self._load_config()
            self._load_env_variables()
            logging.info("配置已重新加载")
    
    def save(self) -> None:
        """保存当前配置到文件"""
        with self._lock:
            # 更新配置数据
            self._config_data.update({
                "tts": asdict(self.tts),
                "logging": asdict(self.logging),
                "admin": asdict(self.admin),
                "dictionary": asdict(self.dictionary),
                "system": asdict(self.system)
            })
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        try:
            # 验证TTS配置
            if not isinstance(self.tts.default_speed, (int, float)) or self.tts.default_speed <= 0:
                raise ValueError("TTS语速必须是正数")
            
            if not isinstance(self.tts.cache_size_limit, int) or self.tts.cache_size_limit <= 0:
                raise ValueError("缓存大小限制必须是正整数")
            
            if not isinstance(self.tts.cache_time_limit, int) or self.tts.cache_time_limit <= 0:
                raise ValueError("缓存时间限制必须是正整数")
            
            # 验证日志配置
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if self.logging.level not in valid_log_levels:
                raise ValueError(f"日志级别必须是: {valid_log_levels}")
            
            # 验证系统配置
            if not isinstance(self.system.port, int) or not (1 <= self.system.port <= 65535):
                raise ValueError("端口号必须是1-65535之间的整数")
            
            if not isinstance(self.system.max_workers, int) or self.system.max_workers <= 0:
                raise ValueError("最大工作线程数必须是正整数")
            
            return True
            
        except ValueError as e:
            logging.error(f"配置验证失败: {e}")
            return False
    
    def add_watcher(self, callback) -> None:
        """添加配置变更观察者"""
        self._watchers.append(callback)
    
    def remove_watcher(self, callback) -> None:
        """移除配置变更观察者"""
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def _notify_watchers(self, key: str, value: Any) -> None:
        """通知所有观察者配置已变更"""
        for watcher in self._watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logging.error(f"通知配置观察者失败: {e}")
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取完整的配置字典"""
        with self._lock:
            return {
                "tts": asdict(self.tts),
                "logging": asdict(self.logging),
                "admin": asdict(self.admin),
                "dictionary": asdict(self.dictionary),
                "system": asdict(self.system)
            }


# 全局配置管理器实例
config_manager = ConfigManager()