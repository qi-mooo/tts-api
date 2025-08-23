"""
Web 管理控制台后端控制器

提供用户认证、配置管理、字典规则管理和系统监控功能
"""

import os
import time
import psutil
import hashlib
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import Blueprint, request, jsonify, session, Response
from functools import wraps

from config.config_manager import config_manager
from dictionary.dictionary_service import DictionaryService
from logger.structured_logger import get_logger
from error_handler.error_handler import ErrorHandler
from error_handler.exceptions import AuthenticationError, AuthorizationError, ValidationError
from restart.restart_controller import restart_controller


class AdminController:
    """Web 管理控制台控制器"""
    
    def __init__(self):
        """初始化管理控制台控制器"""
        self.logger = get_logger('admin_controller')
        self.error_handler = ErrorHandler(self.logger.logger)
        self.dictionary_service = DictionaryService()
        self.blueprint = Blueprint('admin', __name__, url_prefix='/admin')
        self._setup_routes()
        
        # 系统启动时间
        self.start_time = datetime.now()
        
        # 确保管理员密码已设置
        self._ensure_admin_password()
    
    def _ensure_admin_password(self):
        """确保管理员密码已设置"""
        if not config_manager.admin.password_hash:
            # 生成默认密码并设置哈希
            default_password = "admin123"
            password_hash = self._hash_password(default_password)
            config_manager.admin.password_hash = password_hash
            config_manager.save()
            self.logger.warning(f"使用默认管理员密码: {default_password}，请及时修改")
        
        # 确保 session 密钥已设置
        if not config_manager.admin.secret_key:
            config_manager.admin.secret_key = secrets.token_hex(32)
            config_manager.save()
    
    def _setup_routes(self):
        """设置路由"""
        self.blueprint.route('/login', methods=['POST'])(self.login)
        self.blueprint.route('/logout', methods=['POST'])(self.logout)
        self.blueprint.route('/dashboard', methods=['GET'])(self.require_auth(self.dashboard))
        self.blueprint.route('/config', methods=['GET', 'POST'])(self.require_auth(self.config_management))
        self.blueprint.route('/dictionary', methods=['GET'])(self.require_auth(self.get_dictionary_rules))
        self.blueprint.route('/dictionary', methods=['POST'])(self.require_auth(self.add_dictionary_rule))
        self.blueprint.route('/dictionary/<rule_id>', methods=['PUT'])(self.require_auth(self.update_dictionary_rule))
        self.blueprint.route('/dictionary/<rule_id>', methods=['DELETE'])(self.require_auth(self.delete_dictionary_rule))
        self.blueprint.route('/dictionary/import', methods=['POST'])(self.require_auth(self.import_dictionary_rules))
        self.blueprint.route('/dictionary/export', methods=['GET'])(self.require_auth(self.export_dictionary_rules))
        self.blueprint.route('/voices', methods=['GET'])(self.require_auth(self.get_voices))
        self.blueprint.route('/voices/refresh', methods=['POST'])(self.require_auth(self.refresh_voices))
        self.blueprint.route('/system/status', methods=['GET'])(self.require_auth(self.system_status))
        self.blueprint.route('/system/monitoring', methods=['GET'])(self.require_auth(self.unified_monitoring))
        self.blueprint.route('/system/restart', methods=['POST'])(self.require_auth(self.system_restart))
        self.blueprint.route('/system/restart/status', methods=['GET'])(self.require_auth(self.get_restart_status))
        self.blueprint.route('/system/restart/cancel', methods=['POST'])(self.require_auth(self.cancel_restart))
        self.blueprint.route('/system/restart/history', methods=['GET'])(self.require_auth(self.get_restart_history))
        self.blueprint.route('/logs', methods=['GET'])(self.require_auth(self.get_logs))
        self.blueprint.route('/logs/stream', methods=['GET'])(self.require_auth(self.stream_logs))
        self.blueprint.route('/logs/download', methods=['GET'])(self.require_auth(self.download_logs))
        self.blueprint.route('/change-password', methods=['POST'])(self.require_auth(self.change_password))
    
    def require_auth(self, f):
        """认证装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not self._is_authenticated():
                    raise AuthenticationError("未登录或会话已过期")
                return f(*args, **kwargs)
            except Exception as e:
                return self.error_handler.handle_error(e)
        return decorated_function
    
    def _is_authenticated(self) -> bool:
        """检查用户是否已认证"""
        if 'user_id' not in session:
            return False
        
        if 'login_time' not in session:
            return False
        
        # 检查会话是否过期
        login_time = datetime.fromisoformat(session['login_time'])
        if datetime.now() - login_time > timedelta(seconds=config_manager.admin.session_timeout):
            session.clear()
            return False
        
        return True
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return False
    
    def login(self) -> Response:
        """用户登录"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("请求数据", "请求体不能为空")
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                raise ValidationError("登录参数", "用户名和密码不能为空")
            
            # 验证用户名和密码
            if (username != config_manager.admin.username or 
                not self._verify_password(password, config_manager.admin.password_hash)):
                raise AuthenticationError("用户名或密码错误")
            
            # 设置会话
            session['user_id'] = username
            session['login_time'] = datetime.now().isoformat()
            
            # 记录审计日志
            self.logger.audit('login', username, 
                            remote_addr=request.remote_addr,
                            user_agent=request.headers.get('User-Agent'))
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': username,
                'session_timeout': config_manager.admin.session_timeout
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def logout(self) -> Response:
        """用户登出"""
        try:
            username = session.get('user_id', 'unknown')
            session.clear()
            
            # 记录审计日志
            self.logger.audit('logout', username,
                            remote_addr=request.remote_addr)
            
            return jsonify({
                'success': True,
                'message': '登出成功'
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def dashboard(self) -> Response:
        """管理控制台仪表板 - 整合健康监控数据"""
        try:
            # 使用健康监控器获取系统状态
            from health_check.health_monitor import health_monitor
            import asyncio
            
            # 获取详细的系统状态
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                system_status = loop.run_until_complete(health_monitor.get_system_status())
                system_info = system_status.to_dict()
            finally:
                loop.close()
            
            # 获取配置摘要
            config_summary = {
                'tts': {
                    'narration_voice': config_manager.tts.narration_voice,
                    'dialogue_voice': config_manager.tts.dialogue_voice,
                    'default_speed': config_manager.tts.default_speed
                },
                'dictionary': {
                    'enabled': config_manager.dictionary.enabled,
                    'rules_count': len(self.dictionary_service.get_all_rules())
                }
            }
            
            # 获取服务统计信息
            service_stats = {
                'active_requests': system_info.get('active_requests', 0),
                'cache_size': system_info.get('cache_size', 0),
                'cache_hit_rate': system_info.get('cache_hit_rate', 0.0),
                'error_count_1h': system_info.get('error_count_1h', 0),
                'error_count_24h': system_info.get('error_count_24h', 0)
            }
            
            return jsonify({
                'success': True,
                'data': {
                    'system_info': system_info,
                    'config_summary': config_summary,
                    'service_stats': service_stats,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def config_management(self) -> Response:
        """配置管理"""
        try:
            if request.method == 'GET':
                # 获取配置
                config_data = config_manager.get_config_dict()
                # 移除敏感信息
                if 'admin' in config_data:
                    config_data['admin'].pop('password_hash', None)
                    config_data['admin'].pop('secret_key', None)
                
                return jsonify({
                    'success': True,
                    'data': config_data
                })
            
            elif request.method == 'POST':
                # 更新配置
                data = request.get_json()
                if not data:
                    raise ValidationError("配置数据", "请求体不能为空")
                
                # 验证配置数据
                self._validate_config_data(data)
                
                # 更新配置
                for section, values in data.items():
                    if section == 'admin':
                        # 跳过敏感字段
                        continue
                    
                    for key, value in values.items():
                        config_key = f"{section}.{key}"
                        config_manager.set(config_key, value)
                
                # 保存配置
                config_manager.save()
                
                # 记录审计日志
                self.logger.audit('config_update', session.get('user_id', 'unknown'),
                                config_sections=list(data.keys()))
                
                return jsonify({
                    'success': True,
                    'message': '配置更新成功'
                })
                
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def get_dictionary_rules(self) -> Response:
        """获取字典规则"""
        try:
            rule_type = request.args.get('type')  # 可选的类型过滤
            
            if rule_type:
                rules = self.dictionary_service.get_rules_by_type(rule_type)
            else:
                rules = self.dictionary_service.get_all_rules()
            
            rules_data = [rule.to_dict() for rule in rules]
            
            return jsonify({
                'success': True,
                'data': rules_data,
                'total': len(rules_data)
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def add_dictionary_rule(self) -> Response:
        """添加字典规则"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("规则数据", "请求体不能为空")
            
            # 验证必需字段
            required_fields = ['pattern', 'replacement', 'type']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(field, f"缺少必需字段: {field}")
            
            # 添加规则
            rule_id = self.dictionary_service.add_rule(
                pattern=data['pattern'],
                replacement=data['replacement'],
                rule_type=data['type'],
                rule_id=data.get('id')
            )
            
            # 记录审计日志
            self.logger.audit('dictionary_rule_add', session.get('user_id', 'unknown'),
                            rule_id=rule_id, rule_type=data['type'])
            
            return jsonify({
                'success': True,
                'message': '规则添加成功',
                'rule_id': rule_id
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def update_dictionary_rule(self, rule_id: str) -> Response:
        """更新字典规则"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("规则数据", "请求体不能为空")
            
            # 更新规则
            success = self.dictionary_service.update_rule(rule_id, **data)
            
            if not success:
                raise ValidationError("规则ID", f"规则不存在: {rule_id}")
            
            # 记录审计日志
            self.logger.audit('dictionary_rule_update', session.get('user_id', 'unknown'),
                            rule_id=rule_id, updated_fields=list(data.keys()))
            
            return jsonify({
                'success': True,
                'message': '规则更新成功'
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def delete_dictionary_rule(self, rule_id: str) -> Response:
        """删除字典规则"""
        try:
            success = self.dictionary_service.remove_rule(rule_id)
            
            if not success:
                raise ValidationError("规则ID", f"规则不存在: {rule_id}")
            
            # 记录审计日志
            self.logger.audit('dictionary_rule_delete', session.get('user_id', 'unknown'),
                            rule_id=rule_id)
            
            return jsonify({
                'success': True,
                'message': '规则删除成功'
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def import_dictionary_rules(self) -> Response:
        """批量导入字典规则"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("导入数据", "请求体不能为空")
            
            rules_data = data.get('rules', [])
            overwrite = data.get('overwrite', False)
            
            if not isinstance(rules_data, list):
                raise ValidationError("规则数据", "规则数据必须是数组格式")
            
            if not rules_data:
                raise ValidationError("规则数据", "规则数据不能为空")
            
            # 执行导入
            result = self.dictionary_service.import_rules(rules_data, overwrite)
            
            # 记录审计日志
            self.logger.audit('dictionary_rules_import', session.get('user_id', 'unknown'),
                            total_rules=len(rules_data),
                            success_count=result['success_count'],
                            error_count=result['error_count'],
                            overwrite=overwrite)
            
            return jsonify({
                'success': True,
                'message': f"导入完成: 成功 {result['success_count']} 条，失败 {result['error_count']} 条，跳过 {result['skipped_count']} 条",
                'data': result
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def export_dictionary_rules(self) -> Response:
        """导出字典规则"""
        try:
            # 获取查询参数
            rule_type = request.args.get('type')
            enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
            format_type = request.args.get('format', 'json')  # json 或 csv
            
            # 导出规则
            rules_data = self.dictionary_service.export_rules(rule_type, enabled_only)
            
            if format_type == 'csv':
                # CSV 格式导出
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=['id', 'type', 'pattern', 'replacement', 'enabled', 'created_at', 'updated_at'])
                writer.writeheader()
                writer.writerows(rules_data)
                
                csv_content = output.getvalue()
                output.close()
                
                filename = f"dictionary_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                return Response(
                    csv_content,
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename="{filename}"',
                        'Content-Type': 'text/csv; charset=utf-8'
                    }
                )
            else:
                # JSON 格式导出
                export_data = {
                    'version': '2.0',
                    'exported_at': datetime.now().isoformat(),
                    'filters': {
                        'type': rule_type,
                        'enabled_only': enabled_only
                    },
                    'rules': rules_data,
                    'metadata': {
                        'total_rules': len(rules_data),
                        'type_counts': {}
                    }
                }
                
                # 统计类型
                for rule in rules_data:
                    rule_type_key = rule['type']
                    export_data['metadata']['type_counts'][rule_type_key] = export_data['metadata']['type_counts'].get(rule_type_key, 0) + 1
                
                # 记录审计日志
                self.logger.audit('dictionary_rules_export', session.get('user_id', 'unknown'),
                                total_rules=len(rules_data),
                                format=format_type,
                                filters={'type': rule_type, 'enabled_only': enabled_only})
                
                return jsonify({
                    'success': True,
                    'data': export_data
                })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def system_status(self) -> Response:
        """系统状态监控 - 使用统一的健康监控数据"""
        try:
            # 使用健康监控器获取完整的系统状态
            from health_check.health_monitor import health_monitor
            import asyncio
            
            # 获取详细的系统状态
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                system_status = loop.run_until_complete(health_monitor.get_system_status(force_refresh=True))
                status_data = system_status.to_dict()
            finally:
                loop.close()
            
            # 添加额外的管理信息
            status_data['management_info'] = {
                'admin_session_active': True,
                'last_config_update': getattr(config_manager, '_last_update', None),
                'dictionary_rules_count': len(self.dictionary_service.get_all_rules()),
                'system_start_time': self.start_time.isoformat()
            }
            
            return jsonify({
                'success': True,
                'data': status_data
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def unified_monitoring(self) -> Response:
        """统一监控数据接口 - 整合系统监控和仪表盘数据"""
        try:
            # 使用健康监控器获取完整的系统状态
            from health_check.health_monitor import health_monitor
            import asyncio
            
            # 获取详细的系统状态
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                system_status = loop.run_until_complete(health_monitor.get_system_status(force_refresh=True))
                system_info = system_status.to_dict()
            finally:
                loop.close()
            
            # 获取配置摘要
            config_summary = {
                'tts': {
                    'narration_voice': config_manager.tts.narration_voice,
                    'dialogue_voice': config_manager.tts.dialogue_voice,
                    'default_speed': config_manager.tts.default_speed,
                    'cache_size_limit': getattr(config_manager.tts, 'cache_size_limit', 0),
                    'cache_time_limit': getattr(config_manager.tts, 'cache_time_limit', 0)
                },
                'dictionary': {
                    'enabled': config_manager.dictionary.enabled,
                    'rules_count': len(self.dictionary_service.get_all_rules()),
                    'rules_file': config_manager.dictionary.rules_file
                },
                'system': {
                    'host': config_manager.system.host,
                    'port': config_manager.system.port,
                    'debug': config_manager.system.debug,
                    'max_workers': getattr(config_manager.system, 'max_workers', 5)
                }
            }
            
            # 获取服务统计信息
            service_stats = {
                'active_requests': system_info.get('active_requests', 0),
                'cache_size': system_info.get('cache_size', 0),
                'cache_hit_rate': system_info.get('cache_hit_rate', 0.0),
                'error_count_1h': system_info.get('error_count_1h', 0),
                'error_count_24h': system_info.get('error_count_24h', 0)
            }
            
            # 获取管理信息
            management_info = {
                'admin_session_active': True,
                'current_user': session.get('user_id', 'unknown'),
                'session_timeout': config_manager.admin.session_timeout,
                'last_config_update': getattr(config_manager, '_last_update', None),
                'dictionary_rules_count': len(self.dictionary_service.get_all_rules()),
                'system_start_time': self.start_time.isoformat(),
                'login_time': session.get('login_time')
            }
            
            # 获取性能指标
            performance_metrics = {
                'uptime_seconds': system_info.get('uptime', 0),
                'memory_usage_percent': system_info.get('memory_usage', 0),
                'cpu_usage_percent': system_info.get('cpu_usage', 0),
                'disk_usage_percent': system_info.get('disk_usage', 0),
                'edge_tts_status': system_info.get('edge_tts_status', False),
                'edge_tts_response_time': system_info.get('edge_tts_response_time', None)
            }
            
            return jsonify({
                'success': True,
                'data': {
                    'system_info': system_info,
                    'config_summary': config_summary,
                    'service_stats': service_stats,
                    'management_info': management_info,
                    'performance_metrics': performance_metrics,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def system_restart(self) -> Response:
        """系统重启"""
        try:
            data = request.get_json() or {}
            user = session.get('user_id', 'unknown')
            
            # 获取重启参数
            reason = data.get('reason', '管理员手动重启')
            force = data.get('force', False)
            config_reload = data.get('config_reload', True)
            timeout = data.get('timeout', 30)
            
            # 记录审计日志
            self.logger.audit('system_restart_request', user,
                            remote_addr=request.remote_addr,
                            reason=reason,
                            force=force,
                            config_reload=config_reload)
            
            # 请求重启
            result = restart_controller.request_restart(
                user=user,
                reason=reason,
                force=force,
                config_reload=config_reload,
                timeout=timeout
            )
            
            return jsonify(result)
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def get_restart_status(self) -> Response:
        """获取重启状态"""
        try:
            status = restart_controller.get_restart_status()
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def cancel_restart(self) -> Response:
        """取消重启"""
        try:
            user = session.get('user_id', 'unknown')
            
            # 记录审计日志
            self.logger.audit('system_restart_cancel', user,
                            remote_addr=request.remote_addr)
            
            result = restart_controller.cancel_restart(user)
            
            return jsonify(result)
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def get_restart_history(self) -> Response:
        """获取重启历史"""
        try:
            limit = request.args.get('limit', 10, type=int)
            history = restart_controller.get_restart_history(limit)
            
            return jsonify({
                'success': True,
                'data': history,
                'total': len(history)
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def get_logs(self) -> Response:
        """获取日志"""
        try:
            # 获取查询参数
            lines = request.args.get('lines', 100, type=int)
            level = request.args.get('level')  # None 表示所有级别
            log_type = request.args.get('type', 'audio')  # 默认只显示音频相关日志
            search = request.args.get('search')  # 搜索关键词
            start_time = request.args.get('start_time')  # 开始时间
            end_time = request.args.get('end_time')  # 结束时间
            
            # 读取日志文件
            log_file = config_manager.logging.file
            raw_logs = self._read_log_file_raw(log_file, lines * 2)  # 读取更多行用于过滤
            
            # 使用 web 日志格式化器
            from logger.web_log_formatter import web_log_formatter
            
            # 格式化日志
            formatted_logs = web_log_formatter.format_log_list(raw_logs, limit=lines * 2)
            
            # 应用过滤器
            filtered_logs = web_log_formatter.filter_logs(
                formatted_logs, 
                level=level, 
                log_type=log_type, 
                search=search,
                start_time=start_time,
                end_time=end_time
            )
            
            # 限制返回数量
            final_logs = filtered_logs[-lines:] if len(filtered_logs) > lines else filtered_logs
            
            # 统计信息
            stats = {
                'total_lines': len(raw_logs),
                'formatted_entries': len(formatted_logs),
                'filtered_entries': len(filtered_logs),
                'returned_entries': len(final_logs)
            }
            
            # 按类型统计
            type_stats = {}
            level_stats = {}
            for log in formatted_logs:
                log_type_key = log.get('type', 'unknown')
                log_level_key = log.get('level', 'INFO')
                type_stats[log_type_key] = type_stats.get(log_type_key, 0) + 1
                level_stats[log_level_key] = level_stats.get(log_level_key, 0) + 1
            
            return jsonify({
                'success': True,
                'data': {
                    'logs': final_logs,
                    'stats': stats,
                    'type_stats': type_stats,
                    'level_stats': level_stats,
                    'log_file': log_file,
                    'filters': {
                        'level': level,
                        'type': log_type,
                        'search': search,
                        'lines': lines,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                }
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def stream_logs(self) -> Response:
        """实时日志流"""
        try:
            def generate_log_stream():
                """生成日志流"""
                import time
                import os
                
                log_file = config_manager.logging.file
                if not os.path.exists(log_file):
                    yield f"data: {json.dumps({'error': '日志文件不存在'})}\n\n"
                    return
                
                # 获取文件初始大小
                last_size = os.path.getsize(log_file)
                
                while True:
                    try:
                        current_size = os.path.getsize(log_file)
                        
                        if current_size > last_size:
                            # 文件有新内容
                            with open(log_file, 'r', encoding='utf-8') as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                                
                                for line in new_lines:
                                    if line.strip():
                                        from logger.web_log_formatter import web_log_formatter
                                        formatted_log = web_log_formatter.format_log_entry(line.strip())
                                        yield f"data: {json.dumps(formatted_log, ensure_ascii=False)}\n\n"
                                
                                last_size = current_size
                        
                        time.sleep(1)  # 每秒检查一次
                        
                    except Exception as e:
                        yield f"data: {json.dumps({'error': f'读取日志失败: {str(e)}'})}\n\n"
                        break
            
            return Response(
                generate_log_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def download_logs(self) -> Response:
        """下载日志文件"""
        try:
            log_file = config_manager.logging.file
            
            if not os.path.exists(log_file):
                return jsonify({
                    'success': False,
                    'error': '日志文件不存在'
                }), 404
            
            # 获取查询参数
            lines = request.args.get('lines', type=int)  # 如果指定行数，只下载最后N行
            level = request.args.get('level')
            log_type = request.args.get('type')
            
            if lines or level or log_type:
                # 过滤后下载
                raw_logs = self._read_log_file_raw(log_file, lines or 10000)
                
                from logger.web_log_formatter import web_log_formatter
                formatted_logs = web_log_formatter.format_log_list(raw_logs)
                filtered_logs = web_log_formatter.filter_logs(formatted_logs, level=level, log_type=log_type)
                
                # 转换回文本格式
                content = '\n'.join([
                    f"[{log.get('timestamp', '')}] {log.get('level', 'INFO')} [{log.get('module', 'unknown')}] {log.get('message', '')}"
                    for log in filtered_logs
                ])
                
                filename = f"filtered_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            else:
                # 下载完整文件
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                filename = f"app_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            return Response(
                content,
                mimetype='text/plain',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'text/plain; charset=utf-8'
                }
            )
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def change_password(self) -> Response:
        """修改密码"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("密码数据", "请求体不能为空")
            
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            
            if not old_password or not new_password:
                raise ValidationError("密码", "旧密码和新密码不能为空")
            
            # 验证旧密码
            if not self._verify_password(old_password, config_manager.admin.password_hash):
                raise AuthenticationError("旧密码错误")
            
            # 验证新密码强度
            if len(new_password) < 6:
                raise ValidationError("新密码", "密码长度至少6位")
            
            # 更新密码
            new_password_hash = self._hash_password(new_password)
            config_manager.admin.password_hash = new_password_hash
            config_manager.save()
            
            # 记录审计日志
            self.logger.audit('password_change', session.get('user_id', 'unknown'),
                            remote_addr=request.remote_addr)
            
            return jsonify({
                'success': True,
                'message': '密码修改成功'
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def _validate_config_data(self, data: Dict[str, Any]) -> None:
        """验证配置数据"""
        if 'tts' in data:
            tts_config = data['tts']
            if 'default_speed' in tts_config:
                speed = tts_config['default_speed']
                if not isinstance(speed, (int, float)) or speed <= 0:
                    raise ValidationError("TTS语速", "语速必须是正数")
            
            if 'cache_size_limit' in tts_config:
                cache_size = tts_config['cache_size_limit']
                if not isinstance(cache_size, int) or cache_size <= 0:
                    raise ValidationError("缓存大小", "缓存大小必须是正整数")
        
        if 'system' in data:
            system_config = data['system']
            if 'port' in system_config:
                port = system_config['port']
                if not isinstance(port, int) or not (1 <= port <= 65535):
                    raise ValidationError("端口号", "端口号必须是1-65535之间的整数")
    
    # 移除重复的系统信息获取方法，现在使用健康监控器统一提供
    # _get_system_info 和 _check_edge_tts_status 方法已被健康监控器替代
    
    def _read_log_file_raw(self, log_file: str, lines: int) -> List[str]:
        """读取原始日志文件行"""
        try:
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                # 读取最后 N 行
                file_lines = f.readlines()
                recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                
                # 过滤空行
                return [line.strip() for line in recent_lines if line.strip()]
        
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")
            return []
    
    def get_voices(self) -> Response:
        """获取可用语音列表"""
        try:
            from enhanced_tts_api import EnhancedVoiceSelector
            
            voice_selector = EnhancedVoiceSelector()
            
            # 获取可用语音
            available_voices = voice_selector.get_available_voices()
            
            # 获取缓存信息
            cache_info = voice_selector.get_voice_cache_info()
            
            # 按语言分组
            voice_groups = {}
            for voice in available_voices:
                if 'zh-CN' in voice:
                    lang = 'zh-CN'
                elif 'en-US' in voice:
                    lang = 'en-US'
                elif 'ja-JP' in voice:
                    lang = 'ja-JP'
                elif 'ko-KR' in voice:
                    lang = 'ko-KR'
                else:
                    lang = 'other'
                
                if lang not in voice_groups:
                    voice_groups[lang] = []
                voice_groups[lang].append(voice)
            
            return jsonify({
                'success': True,
                'data': {
                    'voices': available_voices,
                    'voice_groups': voice_groups,
                    'total_count': len(available_voices),
                    'cache_info': cache_info
                }
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def refresh_voices(self) -> Response:
        """刷新语音缓存"""
        try:
            from enhanced_tts_api import EnhancedVoiceSelector
            
            voice_selector = EnhancedVoiceSelector()
            
            # 刷新缓存
            success = voice_selector.refresh_voice_cache()
            
            if success:
                # 获取更新后的语音列表
                available_voices = voice_selector.get_available_voices()
                cache_info = voice_selector.get_voice_cache_info()
                
                # 记录审计日志
                self.logger.audit('voices_refresh', session.get('user_id', 'unknown'),
                                voice_count=len(available_voices))
                
                return jsonify({
                    'success': True,
                    'message': f'语音缓存刷新成功，获取到 {len(available_voices)} 个语音',
                    'data': {
                        'voice_count': len(available_voices),
                        'cache_info': cache_info
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '语音缓存刷新失败'
                }), 500
            
        except Exception as e:
            return self.error_handler.handle_error(e)


# 创建全局实例
admin_controller = AdminController()