"""
数据库模型定义

定义数据库表对应的数据模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class RequestLog:
    """请求日志模型"""
    id: Optional[int] = None
    request_id: str = ""
    timestamp: Optional[datetime] = None
    text_length: int = 0
    processing_time_ms: float = 0.0
    voice_narration: str = ""
    voice_dialogue: str = ""
    speed: float = 1.0
    success: bool = True
    error_message: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    audio_duration_ms: Optional[int] = None
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'text_length': self.text_length,
            'processing_time_ms': self.processing_time_ms,
            'voice_narration': self.voice_narration,
            'voice_dialogue': self.voice_dialogue,
            'speed': self.speed,
            'success': self.success,
            'error_message': self.error_message,
            'client_ip': self.client_ip,
            'user_agent': self.user_agent,
            'audio_duration_ms': self.audio_duration_ms,
            'cache_hit': self.cache_hit
        }


@dataclass
class CacheEntry:
    """缓存条目模型"""
    id: Optional[int] = None
    cache_key: str = ""
    text_hash: str = ""
    voice_config: str = ""
    audio_size_bytes: int = 0
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 1
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'text_hash': self.text_hash,
            'voice_config': self.voice_config,
            'audio_size_bytes': self.audio_size_bytes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class SystemMetrics:
    """系统指标模型"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    metric_name: str = ""
    metric_value: float = 0.0
    metric_unit: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'additional_data': self.additional_data
        }


@dataclass
class UserSession:
    """用户会话模型"""
    id: Optional[int] = None
    session_id: str = ""
    username: str = ""
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }