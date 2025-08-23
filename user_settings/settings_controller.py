"""
用户设置API控制器

提供用户个人设置的REST API接口
"""

from flask import Blueprint, request, jsonify, Response
from typing import Dict, Any
import json

from user_settings.user_settings_service import user_settings_service
from logger.structured_logger import get_logger
from error_handler.error_handler import ErrorHandler
from error_handler.exceptions import ValidationError


class SettingsController:
    """用户设置控制器"""
    
    def __init__(self):
        """初始化设置控制器"""
        self.logger = get_logger('settings_controller')
        self.error_handler = ErrorHandler(self.logger.logger)
        self.blueprint = Blueprint('settings', __name__, url_prefix='/api/settings')
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        self.blueprint.route('', methods=['GET'])(self.get_settings)
        self.blueprint.route('', methods=['POST'])(self.update_settings)
        self.blueprint.route('/export', methods=['GET'])(self.export_settings)
        self.blueprint.route('/import', methods=['POST'])(self.import_settings)
        self.blueprint.route('/reset', methods=['POST'])(self.reset_settings)
        self.blueprint.route('/backup', methods=['POST'])(self.backup_settings)
        self.blueprint.route('/backups', methods=['GET'])(self.get_backups)
        self.blueprint.route('/restore', methods=['POST'])(self.restore_settings)
    
    def _get_user_info(self) -> Dict[str, Any]:
        """从请求中获取用户信息"""
        return {
            'ip': request.remote_addr or 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
    
    def get_settings(self) -> Response:
        """获取用户设置"""
        try:
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            settings = user_settings_service.load_user_settings(user_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'settings': settings.to_dict()
                }
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def update_settings(self) -> Response:
        """更新用户设置"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("设置数据", "请求体不能为空")
            
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            # 过滤有效的设置字段
            valid_fields = {
                'default_narration_voice', 'default_dialogue_voice', 'default_speed',
                'preferred_format', 'auto_play', 'show_advanced_options',
                'theme', 'language'
            }
            
            update_data = {k: v for k, v in data.items() if k in valid_fields}
            
            if not update_data:
                raise ValidationError("设置数据", "没有有效的设置字段")
            
            # 更新设置
            success = user_settings_service.update_user_settings(user_id, **update_data)
            
            if success:
                # 获取更新后的设置
                updated_settings = user_settings_service.load_user_settings(user_id)
                
                return jsonify({
                    'success': True,
                    'message': '设置更新成功',
                    'data': {
                        'settings': updated_settings.to_dict()
                    }
                })
            else:
                raise Exception("设置更新失败")
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def export_settings(self) -> Response:
        """导出用户设置"""
        try:
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            export_data = user_settings_service.export_user_settings(user_id)
            
            # 检查是否要下载文件
            download = request.args.get('download', 'false').lower() == 'true'
            
            if download:
                # 返回文件下载
                from datetime import datetime
                filename = f"user_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                return Response(
                    json.dumps(export_data, ensure_ascii=False, indent=2),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename="{filename}"',
                        'Content-Type': 'application/json; charset=utf-8'
                    }
                )
            else:
                # 返回JSON响应
                return jsonify({
                    'success': True,
                    'data': export_data
                })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def import_settings(self) -> Response:
        """导入用户设置"""
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("导入数据", "请求体不能为空")
            
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            # 导入设置
            success = user_settings_service.import_user_settings(user_id, data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '设置导入成功'
                })
            else:
                raise Exception("设置导入失败")
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def reset_settings(self) -> Response:
        """重置用户设置"""
        try:
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            # 重置设置
            success = user_settings_service.reset_user_settings(user_id)
            
            if success:
                # 获取重置后的设置
                reset_settings = user_settings_service.load_user_settings(user_id)
                
                return jsonify({
                    'success': True,
                    'message': '设置已重置为默认值',
                    'data': {
                        'settings': reset_settings.to_dict()
                    }
                })
            else:
                raise Exception("设置重置失败")
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def backup_settings(self) -> Response:
        """备份用户设置"""
        try:
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            # 创建备份
            backup_path = user_settings_service.backup_user_settings(user_id)
            
            if backup_path:
                return jsonify({
                    'success': True,
                    'message': '设置备份成功',
                    'data': {
                        'backup_path': backup_path
                    }
                })
            else:
                raise Exception("设置备份失败")
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def get_backups(self) -> Response:
        """获取备份列表"""
        try:
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            backups = user_settings_service.get_user_backups(user_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'backups': backups,
                    'total': len(backups)
                }
            })
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    def restore_settings(self) -> Response:
        """从备份恢复设置"""
        try:
            data = request.get_json()
            if not data or 'backup_path' not in data:
                raise ValidationError("备份路径", "请提供备份文件路径")
            
            user_info = self._get_user_info()
            user_id = user_settings_service.get_user_id_from_request(user_info)
            
            backup_path = data['backup_path']
            
            # 恢复设置
            success = user_settings_service.restore_from_backup(user_id, backup_path)
            
            if success:
                # 获取恢复后的设置
                restored_settings = user_settings_service.load_user_settings(user_id)
                
                return jsonify({
                    'success': True,
                    'message': '设置恢复成功',
                    'data': {
                        'settings': restored_settings.to_dict()
                    }
                })
            else:
                raise Exception("设置恢复失败")
            
        except Exception as e:
            return self.error_handler.handle_error(e)


# 创建全局实例
settings_controller = SettingsController()