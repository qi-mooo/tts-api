"""
数据库管理器

提供 SQLite 数据库的连接管理、表创建和基本操作
"""

import sqlite3
import os
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from logger.structured_logger import get_logger


class DatabaseManager:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path: str = "data/tts_api.db"):
        self.db_path = db_path
        self.logger = get_logger('database')
        self._local = threading.local()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取线程本地的数据库连接"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # 启用 WAL 模式以提高并发性能
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_cursor() as cursor:
            # 请求日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    text_length INTEGER,
                    processing_time_ms REAL,
                    voice_narration TEXT,
                    voice_dialogue TEXT,
                    speed REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    client_ip TEXT,
                    user_agent TEXT,
                    audio_duration_ms INTEGER,
                    cache_hit BOOLEAN DEFAULT FALSE
                )
            """)
            
            # 缓存条目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    text_hash TEXT NOT NULL,
                    voice_config TEXT NOT NULL,
                    audio_size_bytes INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    expires_at DATETIME
                )
            """)
            
            # 系统指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    additional_data TEXT
                )
            """)
            
            # 用户会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_request_logs_success ON request_logs(success)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_entries_expires ON cache_entries(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_entries_accessed ON cache_entries(last_accessed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)")
            
        self.logger.info("数据库初始化完成")
    
    def log_request(self, request_data: Dict[str, Any]) -> bool:
        """记录请求日志"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO request_logs (
                        request_id, text_length, processing_time_ms,
                        voice_narration, voice_dialogue, speed, success,
                        error_message, client_ip, user_agent,
                        audio_duration_ms, cache_hit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_data.get('request_id'),
                    request_data.get('text_length'),
                    request_data.get('processing_time_ms'),
                    request_data.get('voice_narration'),
                    request_data.get('voice_dialogue'),
                    request_data.get('speed'),
                    request_data.get('success', True),
                    request_data.get('error_message'),
                    request_data.get('client_ip'),
                    request_data.get('user_agent'),
                    request_data.get('audio_duration_ms'),
                    request_data.get('cache_hit', False)
                ))
            return True
        except Exception as e:
            self.logger.error(f"记录请求日志失败: {e}")
            return False
    
    def get_request_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取请求统计信息"""
        try:
            with self.get_cursor() as cursor:
                since = datetime.now() - timedelta(hours=hours)
                
                # 总请求数
                cursor.execute(
                    "SELECT COUNT(*) as total FROM request_logs WHERE timestamp > ?",
                    (since,)
                )
                total_requests = cursor.fetchone()['total']
                
                # 成功请求数
                cursor.execute(
                    "SELECT COUNT(*) as success FROM request_logs WHERE timestamp > ? AND success = 1",
                    (since,)
                )
                success_requests = cursor.fetchone()['success']
                
                # 平均处理时间
                cursor.execute(
                    "SELECT AVG(processing_time_ms) as avg_time FROM request_logs WHERE timestamp > ? AND success = 1",
                    (since,)
                )
                avg_processing_time = cursor.fetchone()['avg_time'] or 0
                
                # 缓存命中率
                cursor.execute(
                    "SELECT COUNT(*) as cache_hits FROM request_logs WHERE timestamp > ? AND cache_hit = 1",
                    (since,)
                )
                cache_hits = cursor.fetchone()['cache_hits']
                
                # 错误统计
                cursor.execute("""
                    SELECT error_message, COUNT(*) as count 
                    FROM request_logs 
                    WHERE timestamp > ? AND success = 0 
                    GROUP BY error_message 
                    ORDER BY count DESC 
                    LIMIT 5
                """, (since,))
                error_stats = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'total_requests': total_requests,
                    'success_requests': success_requests,
                    'success_rate': success_requests / total_requests if total_requests > 0 else 0,
                    'avg_processing_time_ms': round(avg_processing_time, 2),
                    'cache_hit_rate': cache_hits / total_requests if total_requests > 0 else 0,
                    'error_stats': error_stats,
                    'period_hours': hours
                }
        except Exception as e:
            self.logger.error(f"获取请求统计失败: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """清理旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleanup_stats = {}
            
            with self.get_cursor() as cursor:
                # 清理旧的请求日志
                cursor.execute(
                    "DELETE FROM request_logs WHERE timestamp < ?",
                    (cutoff_date,)
                )
                cleanup_stats['request_logs'] = cursor.rowcount
                
                # 清理过期的缓存条目
                cursor.execute(
                    "DELETE FROM cache_entries WHERE expires_at < ?",
                    (datetime.now(),)
                )
                cleanup_stats['cache_entries'] = cursor.rowcount
                
                # 清理旧的系统指标
                cursor.execute(
                    "DELETE FROM system_metrics WHERE timestamp < ?",
                    (cutoff_date,)
                )
                cleanup_stats['system_metrics'] = cursor.rowcount
                
                # 清理过期的用户会话
                cursor.execute(
                    "DELETE FROM user_sessions WHERE expires_at < ? OR is_active = 0",
                    (datetime.now(),)
                )
                cleanup_stats['user_sessions'] = cursor.rowcount
            
            self.logger.info(f"数据清理完成: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"数据清理失败: {e}")
            return {}
    
    def record_metric(self, name: str, value: float, unit: str = None, 
                     additional_data: Dict[str, Any] = None) -> bool:
        """记录系统指标"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO system_metrics (metric_name, metric_value, metric_unit, additional_data)
                    VALUES (?, ?, ?, ?)
                """, (
                    name,
                    value,
                    unit,
                    json.dumps(additional_data) if additional_data else None
                ))
            return True
        except Exception as e:
            self.logger.error(f"记录系统指标失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            with self.get_cursor() as cursor:
                # 数据库文件大小
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # 表统计
                tables_info = {}
                tables = ['request_logs', 'cache_entries', 'system_metrics', 'user_sessions']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    tables_info[table] = cursor.fetchone()['count']
                
                return {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'tables': tables_info
                }
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {}
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')


# 全局数据库管理器实例
db_manager = DatabaseManager()