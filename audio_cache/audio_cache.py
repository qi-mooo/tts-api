"""
优化的音频缓存系统
集成配置管理、统计监控和内存优化功能
"""

import time
import threading
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from collections import OrderedDict
import logging

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

from config.config_manager import config_manager
from logger.structured_logger import get_logger


@dataclass
class CacheEntry:
    """缓存条目数据类"""
    audio_segment: Any  # AudioSegment
    timestamp: float
    size_bytes: int
    access_count: int
    last_access: float
    cache_key: str


@dataclass
class CacheStats:
    """缓存统计信息数据类"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    memory_usage_percent: float = 0.0
    average_entry_size: float = 0.0
    oldest_entry_age: float = 0.0


class OptimizedAudioCache:
    """
    优化的音频缓存系统
    
    特性:
    - 集成配置管理系统
    - LRU (Least Recently Used) 缓存策略
    - 详细的统计和监控功能
    - 内存使用优化
    - 线程安全
    - 缓存命中率统计
    - 自动清理过期条目
    """
    
    def __init__(self, size_limit: Optional[int] = None, time_limit: Optional[int] = None):
        """
        初始化音频缓存
        
        Args:
            size_limit: 缓存大小限制（字节），None则使用配置文件值
            time_limit: 缓存时间限制（秒），None则使用配置文件值
        """
        self._lock = threading.RLock()
        self.logger = get_logger('audio_cache')
        
        # 从配置管理器获取配置
        self.size_limit = size_limit or config_manager.tts.cache_size_limit
        self.time_limit = time_limit or config_manager.tts.cache_time_limit
        
        # 使用 OrderedDict 实现 LRU 缓存
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._current_size = 0
        
        # 统计信息
        self._stats = CacheStats()
        
        # 配置变更监听
        config_manager.add_watcher(self._on_config_change)
        
        self.logger.info(
            f"音频缓存初始化完成 - 大小限制: {self.size_limit} 字节, "
            f"时间限制: {self.time_limit} 秒"
        )
    
    def _on_config_change(self, key: str, value: Any) -> None:
        """配置变更回调"""
        if key == "tts.cache_size_limit":
            with self._lock:
                old_limit = self.size_limit
                self.size_limit = value
                self.logger.info(f"缓存大小限制已更新: {old_limit} -> {value}")
                # 如果新限制更小，需要清理缓存
                if self._current_size > self.size_limit:
                    self._make_space(0)
        elif key == "tts.cache_time_limit":
            with self._lock:
                old_limit = self.time_limit
                self.time_limit = value
                self.logger.info(f"缓存时间限制已更新: {old_limit} -> {value}")
                self._cleanup_expired()
    
    def _generate_cache_key(self, text: str, voice: str, speed: float) -> str:
        """生成缓存键"""
        key_string = f"{text}:{voice}:{speed}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, text: str, voice: str, speed: float) -> Optional[Any]:
        """
        从缓存获取音频
        
        Args:
            text: 文本内容
            voice: 语音类型
            speed: 语速
            
        Returns:
            AudioSegment对象或None
        """
        cache_key = self._generate_cache_key(text, voice, speed)
        
        with self._lock:
            self._stats.total_requests += 1
            
            # 清理过期条目
            self._cleanup_expired()
            
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                
                # 更新访问信息
                entry.access_count += 1
                entry.last_access = time.time()
                
                # 移动到末尾（LRU策略）
                self._cache.move_to_end(cache_key)
                
                self._stats.hits += 1
                self.logger.debug(f"缓存命中: {cache_key[:8]}...")
                
                return entry.audio_segment
            else:
                self._stats.misses += 1
                self.logger.debug(f"缓存未命中: {cache_key[:8]}...")
                return None
    
    def put(self, text: str, voice: str, speed: float, audio_segment: Any) -> None:
        """
        将音频添加到缓存
        
        Args:
            text: 文本内容
            voice: 语音类型
            speed: 语速
            audio_segment: AudioSegment对象
        """
        if not audio_segment:
            return
        
        cache_key = self._generate_cache_key(text, voice, speed)
        current_time = time.time()
        
        try:
            audio_size = len(audio_segment.raw_data)
        except AttributeError:
            self.logger.warning("无效的音频段对象")
            return
        
        with self._lock:
            # 检查是否已存在
            if cache_key in self._cache:
                # 更新现有条目
                old_entry = self._cache[cache_key]
                self._current_size -= old_entry.size_bytes
                
                old_entry.audio_segment = audio_segment
                old_entry.timestamp = current_time
                old_entry.last_access = current_time
                old_entry.size_bytes = audio_size
                old_entry.access_count += 1
                
                self._current_size += audio_size
                self._cache.move_to_end(cache_key)
                
                self.logger.debug(f"更新缓存条目: {cache_key[:8]}...")
            else:
                # 确保有足够空间
                self._make_space(audio_size)
                
                # 创建新条目
                entry = CacheEntry(
                    audio_segment=audio_segment,
                    timestamp=current_time,
                    size_bytes=audio_size,
                    access_count=1,
                    last_access=current_time,
                    cache_key=cache_key
                )
                
                self._cache[cache_key] = entry
                self._current_size += audio_size
                
                self.logger.debug(f"添加新缓存条目: {cache_key[:8]}..., 大小: {audio_size} 字节")
            
            # 更新统计信息
            self._update_stats()
    
    def _make_space(self, required_size: int) -> None:
        """为新条目腾出空间"""
        # 清理过期条目
        self._cleanup_expired()
        
        # 如果仍然需要空间，使用LRU淘汰
        while (self._current_size + required_size > self.size_limit and 
               len(self._cache) > 0):
            self._evict_lru()
    
    def _evict_lru(self) -> None:
        """移除最少使用的条目"""
        if not self._cache:
            return
        
        # OrderedDict的第一个元素是最少使用的
        cache_key, entry = self._cache.popitem(last=False)
        self._current_size -= entry.size_bytes
        self._stats.evictions += 1
        
        self.logger.debug(f"移除LRU条目: {cache_key[:8]}..., 释放: {entry.size_bytes} 字节")
    
    def _cleanup_expired(self) -> None:
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, entry in self._cache.items():
            if (current_time - entry.timestamp) > self.time_limit:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            entry = self._cache.pop(cache_key)
            self._current_size -= entry.size_bytes
            self._stats.evictions += 1
        
        if expired_keys:
            self.logger.debug(f"清理 {len(expired_keys)} 个过期缓存条目")
    
    def _update_stats(self) -> None:
        """更新统计信息"""
        self._stats.total_size_bytes = self._current_size
        self._stats.entry_count = len(self._cache)
        
        if self._stats.total_requests > 0:
            self._stats.hit_rate = self._stats.hits / self._stats.total_requests
        
        if self.size_limit > 0:
            self._stats.memory_usage_percent = (self._current_size / self.size_limit) * 100
        
        if self._stats.entry_count > 0:
            self._stats.average_entry_size = self._current_size / self._stats.entry_count
            
            # 计算最旧条目的年龄
            current_time = time.time()
            oldest_timestamp = min(entry.timestamp for entry in self._cache.values())
            self._stats.oldest_entry_age = current_time - oldest_timestamp
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取详细的缓存统计信息
        
        Returns:
            包含统计信息的字典
        """
        with self._lock:
            self._update_stats()
            
            stats_dict = asdict(self._stats)
            stats_dict.update({
                'size_limit_bytes': self.size_limit,
                'time_limit_seconds': self.time_limit,
                'current_time': time.time(),
                'cache_efficiency': {
                    'hit_rate_percent': round(self._stats.hit_rate * 100, 2),
                    'memory_utilization_percent': round(self._stats.memory_usage_percent, 2),
                    'average_entry_size_kb': round(self._stats.average_entry_size / 1024, 2),
                    'entries_per_mb': round(self._stats.entry_count / (self._current_size / 1048576), 2) if self._current_size > 0 else 0
                }
            })
            
            return stats_dict
    
    def get_cache_entries_info(self) -> List[Dict[str, Any]]:
        """
        获取所有缓存条目的详细信息
        
        Returns:
            缓存条目信息列表
        """
        with self._lock:
            current_time = time.time()
            entries_info = []
            
            for cache_key, entry in self._cache.items():
                entry_info = {
                    'cache_key': cache_key,
                    'size_bytes': entry.size_bytes,
                    'size_kb': round(entry.size_bytes / 1024, 2),
                    'age_seconds': round(current_time - entry.timestamp, 2),
                    'access_count': entry.access_count,
                    'last_access_ago': round(current_time - entry.last_access, 2),
                    'is_expired': (current_time - entry.timestamp) > self.time_limit
                }
                entries_info.append(entry_info)
            
            return entries_info
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            cleared_count = len(self._cache)
            cleared_size = self._current_size
            
            self._cache.clear()
            self._current_size = 0
            
            # 重置统计信息（保留总请求数和命中率历史）
            self._stats.entry_count = 0
            self._stats.total_size_bytes = 0
            self._stats.memory_usage_percent = 0.0
            self._stats.average_entry_size = 0.0
            self._stats.oldest_entry_age = 0.0
            
            self.logger.info(f"缓存已清空 - 移除 {cleared_count} 个条目，释放 {cleared_size} 字节")
    
    def optimize(self) -> Dict[str, Any]:
        """
        优化缓存性能
        
        Returns:
            优化结果统计
        """
        with self._lock:
            initial_count = len(self._cache)
            initial_size = self._current_size
            
            # 清理过期条目
            self._cleanup_expired()
            
            # 如果内存使用率过高，主动清理一些LRU条目
            if self._stats.memory_usage_percent > 80:
                target_size = int(self.size_limit * 0.7)  # 目标使用率70%
                while self._current_size > target_size and len(self._cache) > 0:
                    self._evict_lru()
            
            final_count = len(self._cache)
            final_size = self._current_size
            
            optimization_result = {
                'entries_removed': initial_count - final_count,
                'bytes_freed': initial_size - final_size,
                'memory_usage_before': round((initial_size / self.size_limit) * 100, 2),
                'memory_usage_after': round((final_size / self.size_limit) * 100, 2),
                'optimization_time': time.time()
            }
            
            if optimization_result['entries_removed'] > 0:
                self.logger.info(
                    f"缓存优化完成 - 移除 {optimization_result['entries_removed']} 个条目，"
                    f"释放 {optimization_result['bytes_freed']} 字节"
                )
            
            return optimization_result
    
    def __len__(self) -> int:
        """返回缓存条目数量"""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """检查缓存中是否包含指定键"""
        return key in self._cache
    
    def __del__(self):
        """析构函数，移除配置监听器"""
        try:
            config_manager.remove_watcher(self._on_config_change)
        except:
            pass