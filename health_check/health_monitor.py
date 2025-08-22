"""
系统健康监控器

监控系统资源使用情况、服务状态和性能指标
"""

import psutil
import time
import asyncio
import edge_tts
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import threading
import logging
from pathlib import Path


@dataclass
class SystemStatus:
    """系统状态数据模型"""
    # 基本信息
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: str
    uptime: float  # 运行时间（秒）
    version: str
    
    # 系统资源
    memory_usage: float  # 内存使用率（百分比）
    memory_total: int   # 总内存（字节）
    memory_used: int    # 已用内存（字节）
    cpu_usage: float    # CPU使用率（百分比）
    disk_usage: float   # 磁盘使用率（百分比）
    
    # 服务状态
    edge_tts_status: bool  # edge-tts服务状态
    edge_tts_response_time: Optional[float]  # edge-tts响应时间（毫秒）
    
    # 应用状态
    active_requests: int  # 当前活跃请求数
    cache_size: int      # 缓存大小（字节）
    cache_hit_rate: float  # 缓存命中率（百分比）
    
    # 错误统计
    error_count_1h: int   # 1小时内错误数
    error_count_24h: int  # 24小时内错误数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class HealthMonitor:
    """系统健康监控器"""
    
    def __init__(self, app_version: str = "1.0.0"):
        """
        初始化健康监控器
        
        Args:
            app_version: 应用版本号
        """
        self.app_version = app_version
        self.start_time = time.time()
        self._lock = threading.RLock()
        
        # 统计数据
        self.active_requests = 0
        self.error_counts = []  # 错误时间戳列表
        self.cache_stats = {
            'size': 0,
            'hits': 0,
            'misses': 0
        }
        
        # 缓存的系统状态
        self._cached_status = None
        self._cache_time = 0
        self._cache_ttl = 5  # 缓存5秒
        
        self.logger = logging.getLogger(__name__)
    
    def increment_active_requests(self):
        """增加活跃请求计数"""
        with self._lock:
            self.active_requests += 1
    
    def decrement_active_requests(self):
        """减少活跃请求计数"""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
    
    def record_error(self):
        """记录错误"""
        with self._lock:
            self.error_counts.append(time.time())
            # 清理24小时前的错误记录
            cutoff_time = time.time() - 24 * 3600
            self.error_counts = [t for t in self.error_counts if t > cutoff_time]
    
    def update_cache_stats(self, size: int, hit: bool = None):
        """更新缓存统计"""
        with self._lock:
            self.cache_stats['size'] = size
            if hit is True:
                self.cache_stats['hits'] += 1
            elif hit is False:
                self.cache_stats['misses'] += 1
    
    def _get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源使用情况"""
        try:
            # 内存信息
            memory = psutil.virtual_memory()
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            
            return {
                'memory_usage': memory.percent,
                'memory_total': memory.total,
                'memory_used': memory.used,
                'cpu_usage': cpu_percent,
                'disk_usage': (disk.used / disk.total) * 100
            }
        except Exception as e:
            self.logger.error(f"获取系统资源信息失败: {e}")
            return {
                'memory_usage': 0.0,
                'memory_total': 0,
                'memory_used': 0,
                'cpu_usage': 0.0,
                'disk_usage': 0.0
            }
    
    async def _check_edge_tts_status(self) -> tuple[bool, Optional[float]]:
        """检查edge-tts服务状态"""
        try:
            start_time = time.time()
            
            # 创建一个简单的测试通信
            communicate = edge_tts.Communicate("测试", "zh-CN-YunjianNeural")
            
            # 尝试获取第一个音频块
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    break
            
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            return True, response_time
            
        except Exception as e:
            self.logger.warning(f"edge-tts服务检查失败: {e}")
            return False, None
    
    def _get_error_counts(self) -> Dict[str, int]:
        """获取错误统计"""
        current_time = time.time()
        
        # 1小时内的错误
        hour_ago = current_time - 3600
        errors_1h = len([t for t in self.error_counts if t > hour_ago])
        
        # 24小时内的错误
        day_ago = current_time - 24 * 3600
        errors_24h = len([t for t in self.error_counts if t > day_ago])
        
        return {
            'error_count_1h': errors_1h,
            'error_count_24h': errors_24h
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_requests == 0:
            return 0.0
        return (self.cache_stats['hits'] / total_requests) * 100
    
    def _determine_overall_status(self, system_resources: Dict[str, Any], 
                                edge_tts_status: bool) -> str:
        """确定整体健康状态"""
        # 检查关键服务
        if not edge_tts_status:
            return 'unhealthy'
        
        # 检查系统资源
        if (system_resources['memory_usage'] > 90 or 
            system_resources['cpu_usage'] > 90 or 
            system_resources['disk_usage'] > 95):
            return 'unhealthy'
        
        # 检查错误率
        error_stats = self._get_error_counts()
        if error_stats['error_count_1h'] > 50:  # 1小时内超过50个错误
            return 'degraded'
        
        # 检查资源使用情况
        if (system_resources['memory_usage'] > 80 or 
            system_resources['cpu_usage'] > 80 or 
            system_resources['disk_usage'] > 85):
            return 'degraded'
        
        return 'healthy'
    
    async def get_system_status(self, force_refresh: bool = False) -> SystemStatus:
        """
        获取系统状态
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            SystemStatus: 系统状态对象
        """
        current_time = time.time()
        
        # 检查缓存
        if (not force_refresh and 
            self._cached_status and 
            current_time - self._cache_time < self._cache_ttl):
            return self._cached_status
        
        try:
            # 获取系统资源信息
            system_resources = self._get_system_resources()
            
            # 检查edge-tts状态
            edge_tts_status, edge_tts_response_time = await self._check_edge_tts_status()
            
            # 获取错误统计
            error_stats = self._get_error_counts()
            
            # 计算运行时间
            uptime = current_time - self.start_time
            
            # 确定整体状态
            overall_status = self._determine_overall_status(system_resources, edge_tts_status)
            
            # 创建状态对象
            status = SystemStatus(
                status=overall_status,
                timestamp=datetime.now().isoformat(),
                uptime=uptime,
                version=self.app_version,
                
                memory_usage=system_resources['memory_usage'],
                memory_total=system_resources['memory_total'],
                memory_used=system_resources['memory_used'],
                cpu_usage=system_resources['cpu_usage'],
                disk_usage=system_resources['disk_usage'],
                
                edge_tts_status=edge_tts_status,
                edge_tts_response_time=edge_tts_response_time,
                
                active_requests=self.active_requests,
                cache_size=self.cache_stats['size'],
                cache_hit_rate=self._calculate_cache_hit_rate(),
                
                error_count_1h=error_stats['error_count_1h'],
                error_count_24h=error_stats['error_count_24h']
            )
            
            # 更新缓存
            self._cached_status = status
            self._cache_time = current_time
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            # 返回错误状态
            return SystemStatus(
                status='unhealthy',
                timestamp=datetime.now().isoformat(),
                uptime=current_time - self.start_time,
                version=self.app_version,
                
                memory_usage=0.0,
                memory_total=0,
                memory_used=0,
                cpu_usage=0.0,
                disk_usage=0.0,
                
                edge_tts_status=False,
                edge_tts_response_time=None,
                
                active_requests=self.active_requests,
                cache_size=0,
                cache_hit_rate=0.0,
                
                error_count_1h=0,
                error_count_24h=0
            )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要（同步版本）"""
        try:
            # 创建新的事件循环来运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                status = loop.run_until_complete(self.get_system_status())
                return {
                    'status': status.status,
                    'timestamp': status.timestamp,
                    'uptime_seconds': status.uptime,
                    'version': status.version,
                    'edge_tts_available': status.edge_tts_status
                }
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"获取健康状态摘要失败: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': time.time() - self.start_time,
                'version': self.app_version,
                'edge_tts_available': False,
                'error': str(e)
            }


# 全局健康监控器实例
health_monitor = HealthMonitor()