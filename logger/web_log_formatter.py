"""
Web 日志格式化器 - 专门用于 Web 界面显示的日志格式化

提供更友好的日志显示格式，包括颜色标识、图标和结构化信息
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class WebLogFormatter:
    """Web 日志格式化器"""
    
    # 日志级别对应的图标和颜色
    LEVEL_ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    LEVEL_COLORS = {
        'DEBUG': 'text-muted',
        'INFO': 'text-info',
        'WARNING': 'text-warning',
        'ERROR': 'text-danger',
        'CRITICAL': 'text-danger'
    }
    
    # HTTP 状态码对应的颜色
    STATUS_COLORS = {
        200: 'text-success',
        201: 'text-success',
        204: 'text-success',
        301: 'text-info',
        302: 'text-info',
        304: 'text-info',
        400: 'text-warning',
        401: 'text-warning',
        403: 'text-warning',
        404: 'text-warning',
        500: 'text-danger',
        502: 'text-danger',
        503: 'text-danger'
    }
    
    def __init__(self):
        self.request_pattern = re.compile(r'→|←')
        self.json_pattern = re.compile(r'^\{.*\}$')
    
    def format_log_entry(self, log_line: str) -> Dict[str, Any]:
        """
        格式化单条日志条目为 Web 显示格式
        
        Args:
            log_line: 原始日志行
            
        Returns:
            格式化后的日志数据字典
        """
        try:
            # 尝试解析结构化日志
            if self.json_pattern.match(log_line.strip()):
                return self._format_json_log(log_line)
            else:
                return self._format_text_log(log_line)
        except Exception as e:
            return self._create_error_entry(log_line, str(e))
    
    def _format_json_log(self, log_line: str) -> Dict[str, Any]:
        """格式化 JSON 格式的日志"""
        try:
            log_data = json.loads(log_line)
            
            # 基础信息
            entry = {
                'timestamp': self._format_timestamp(log_data.get('timestamp')),
                'level': log_data.get('level', 'INFO'),
                'module': log_data.get('module', 'unknown'),
                'message': log_data.get('message', ''),
                'request_id': log_data.get('request_id'),
                'type': self._determine_log_type(log_data),
                'icon': self.LEVEL_ICONS.get(log_data.get('level', 'INFO'), 'ℹ️'),
                'level_color': self.LEVEL_COLORS.get(log_data.get('level', 'INFO'), 'text-info'),
                'raw_data': log_data
            }
            
            # HTTP 请求相关信息
            if 'method' in log_data and 'path' in log_data:
                entry.update(self._format_http_info(log_data))
            
            # 性能信息
            if 'duration_ms' in log_data:
                entry.update(self._format_performance_info(log_data))
            
            # 错误信息
            if 'error_type' in log_data:
                entry.update(self._format_error_info(log_data))
            
            # 审计信息
            if log_data.get('log_type') == 'audit':
                entry.update(self._format_audit_info(log_data))
            
            return entry
            
        except json.JSONDecodeError:
            return self._format_text_log(log_line)
    
    def _format_text_log(self, log_line: str) -> Dict[str, Any]:
        """格式化文本格式的日志"""
        # 尝试解析标准日志格式
        parts = log_line.strip().split(' ', 4)
        
        if len(parts) >= 4:
            timestamp = parts[0].strip('[]')
            level = parts[1]
            module = parts[2].strip('[]')
            message = ' '.join(parts[3:]) if len(parts) > 3 else ''
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            level = 'INFO'
            module = 'unknown'
            message = log_line.strip()
        
        return {
            'timestamp': timestamp,
            'level': level,
            'module': module,
            'message': message,
            'type': 'text',
            'icon': self.LEVEL_ICONS.get(level, 'ℹ️'),
            'level_color': self.LEVEL_COLORS.get(level, 'text-info'),
            'raw_data': {'original_line': log_line}
        }
    
    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        """格式化时间戳"""
        if not timestamp:
            return datetime.now().strftime('%H:%M:%S')
        
        try:
            # 解析 ISO 格式时间戳
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%H:%M:%S')
        except:
            # 如果解析失败，尝试提取时间部分
            if len(timestamp) >= 8:
                return timestamp[-8:]
            return timestamp
    
    def _determine_log_type(self, log_data: Dict[str, Any]) -> str:
        """确定日志类型"""
        if log_data.get('log_type'):
            return log_data['log_type']
        elif 'method' in log_data and 'path' in log_data:
            return 'http'
        elif 'duration_ms' in log_data:
            return 'performance'
        elif 'error_type' in log_data:
            return 'error'
        else:
            return 'general'
    
    def _format_http_info(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化 HTTP 请求信息"""
        info = {
            'http_method': log_data.get('method'),
            'http_path': log_data.get('path'),
            'remote_addr': log_data.get('remote_addr'),
            'user_agent': self._simplify_user_agent(log_data.get('user_agent')),
        }
        
        # 状态码信息
        if 'status_code' in log_data:
            status_code = log_data['status_code']
            info['status_code'] = status_code
            info['status_color'] = self._get_status_color(status_code)
            info['status_text'] = self._get_status_text(status_code)
        
        # 查询参数
        if 'query_string' in log_data and log_data['query_string']:
            info['query_string'] = log_data['query_string']
        
        # 请求大小
        if 'content_length' in log_data and log_data['content_length']:
            info['request_size'] = self._format_size(log_data['content_length'])
        
        # 响应大小
        if 'response_size_bytes' in log_data and log_data['response_size_bytes']:
            info['response_size'] = self._format_size(log_data['response_size_bytes'])
        
        return info
    
    def _format_performance_info(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化性能信息"""
        duration_ms = log_data.get('duration_ms', 0)
        
        info = {
            'duration_ms': duration_ms,
            'duration_display': f"{duration_ms}ms",
            'performance_level': self._get_performance_level(duration_ms)
        }
        
        if 'operation' in log_data:
            info['operation'] = log_data['operation']
        
        return info
    
    def _format_error_info(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化错误信息"""
        return {
            'error_type': log_data.get('error_type'),
            'error_message': log_data.get('error_message'),
            'has_traceback': bool(log_data.get('traceback'))
        }
    
    def _format_audit_info(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化审计信息"""
        return {
            'audit_action': log_data.get('action'),
            'audit_user': log_data.get('user'),
            'audit_details': {k: v for k, v in log_data.items() 
                            if k not in ['timestamp', 'level', 'module', 'message', 'log_type', 'action', 'user']}
        }
    
    def _simplify_user_agent(self, user_agent: Optional[str]) -> Optional[str]:
        """简化用户代理字符串"""
        if not user_agent:
            return None
        
        ua_lower = user_agent.lower()
        
        if 'curl' in ua_lower:
            return 'curl'
        elif 'postman' in ua_lower:
            return 'Postman'
        elif 'python' in ua_lower:
            return 'Python'
        elif 'chrome' in ua_lower:
            return 'Chrome'
        elif 'firefox' in ua_lower:
            return 'Firefox'
        elif 'safari' in ua_lower:
            return 'Safari'
        elif 'edge' in ua_lower:
            return 'Edge'
        else:
            # 截断过长的用户代理字符串
            return user_agent[:50] + '...' if len(user_agent) > 50 else user_agent
    
    def _get_status_color(self, status_code: int) -> str:
        """获取状态码对应的颜色"""
        if status_code in self.STATUS_COLORS:
            return self.STATUS_COLORS[status_code]
        elif 200 <= status_code < 300:
            return 'text-success'
        elif 300 <= status_code < 400:
            return 'text-info'
        elif 400 <= status_code < 500:
            return 'text-warning'
        else:
            return 'text-danger'
    
    def _get_status_text(self, status_code: int) -> str:
        """获取状态码对应的文本描述"""
        status_texts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        }
        return status_texts.get(status_code, 'Unknown')
    
    def _get_performance_level(self, duration_ms: float) -> str:
        """获取性能级别"""
        if duration_ms < 100:
            return 'fast'
        elif duration_ms < 500:
            return 'normal'
        elif duration_ms < 1000:
            return 'slow'
        else:
            return 'very_slow'
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
    
    def _create_error_entry(self, log_line: str, error: str) -> Dict[str, Any]:
        """创建错误日志条目"""
        return {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'ERROR',
            'module': 'log_formatter',
            'message': f"日志解析失败: {error}",
            'type': 'error',
            'icon': '❌',
            'level_color': 'text-danger',
            'raw_data': {'original_line': log_line, 'parse_error': error}
        }
    
    def format_log_list(self, log_lines: List[str], limit: int = 100) -> List[Dict[str, Any]]:
        """
        格式化日志列表
        
        Args:
            log_lines: 日志行列表
            limit: 最大返回条数
            
        Returns:
            格式化后的日志条目列表
        """
        formatted_logs = []
        
        for line in log_lines[-limit:]:  # 只取最新的 limit 条
            if line.strip():  # 跳过空行
                formatted_logs.append(self.format_log_entry(line))
        
        return formatted_logs
    
    def filter_logs(self, log_entries: List[Dict[str, Any]], 
                   level: Optional[str] = None,
                   log_type: Optional[str] = None,
                   search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        过滤日志条目
        
        Args:
            log_entries: 日志条目列表
            level: 日志级别过滤
            log_type: 日志类型过滤
            search: 搜索关键词
            
        Returns:
            过滤后的日志条目列表
        """
        filtered = log_entries
        
        # 按级别过滤
        if level:
            filtered = [entry for entry in filtered if entry.get('level') == level]
        
        # 按类型过滤
        if log_type:
            filtered = [entry for entry in filtered if entry.get('type') == log_type]
        
        # 按关键词搜索
        if search:
            search_lower = search.lower()
            filtered = [
                entry for entry in filtered
                if search_lower in entry.get('message', '').lower() or
                   search_lower in entry.get('module', '').lower() or
                   search_lower in str(entry.get('raw_data', {})).lower()
            ]
        
        return filtered


# 全局实例
web_log_formatter = WebLogFormatter()