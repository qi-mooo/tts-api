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
        self.blueprint.route('/system/status', methods=['GET'])(self.require_auth(self.system_status))
        self.blueprint.route('/system/restart', methods=['POST'])(self.require_auth(self.system_restart))
        self.blueprint.route('/system/restart/status', methods=['GET'])(self.require_auth(self.get_restart_status))
        self.blueprint.route('/system/restart/cancel', methods=['POST'])(self.require_auth(self.cancel_restart))
        self.blueprint.route('/system/restart/history', methods=['GET'])(self.require_auth(self.get_restart_history))
        self.blueprint.route('/logs', methods=['GET'])(self.require_auth(self.get_logs))
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
        """管理控制台仪表板"""
        try:
            # 获取系统状态
            system_info = self._get_system_info()
            
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
            
            return jsonify({
                'success': True,
                'data': {
                    'system_info': system_info,
                    'config_summary': config_summary,
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
    
    def system_status(self) -> Response:
        """系统状态监控"""
        try:
            status_data = self._get_system_info()
            
            return jsonify({
                'success': True,
                'data': status_data
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
            level = request.args.get('level', 'INFO')
            
            # 读取日志文件
            log_file = config_manager.logging.file
            logs = self._read_log_file(log_file, lines, level)
            
            return jsonify({
                'success': True,
                'data': {
                    'logs': logs,
                    'total': len(logs),
                    'log_file': log_file
                }
            })
            
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
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            # 系统运行时间
            uptime = datetime.now() - self.start_time
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # Edge-TTS 服务状态（简单检查）
            edge_tts_status = self._check_edge_tts_status()
            
            return {
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_human': str(uptime).split('.')[0],
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'cpu_percent': cpu_percent,
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'edge_tts_status': edge_tts_status,
                'active_sessions': len([k for k in session.keys() if k.startswith('user_')]),
                'config_last_modified': os.path.getmtime(config_manager.config_file) if os.path.exists(config_manager.config_file) else None
            }
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {
                'error': '无法获取系统信息',
                'uptime_seconds': 0,
                'edge_tts_status': False
            }
    
    def _check_edge_tts_status(self) -> bool:
        """检查 Edge-TTS 服务状态"""
        try:
            # 这里可以实现实际的 Edge-TTS 服务检查
            # 暂时返回 True
            return True
        except Exception:
            return False
    
    def _read_log_file(self, log_file: str, lines: int, level: str) -> List[Dict[str, Any]]:
        """读取日志文件"""
        logs = []
        try:
            if not os.path.exists(log_file):
                return logs
            
            with open(log_file, 'r', encoding='utf-8') as f:
                # 读取最后 N 行
                file_lines = f.readlines()
                recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                
                for line in recent_lines:
                    try:
                        # 尝试解析 JSON 格式的日志
                        import json
                        log_data = json.loads(line.strip())
                        
                        # 过滤日志级别
                        if log_data.get('level', 'INFO') == level or level == 'ALL':
                            logs.append(log_data)
                    except json.JSONDecodeError:
                        # 如果不是 JSON 格式，作为普通文本处理
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'level': 'INFO',
                            'message': line.strip()
                        })
        
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")
        
        return logs


# 创建全局实例
admin_controller = AdminController()