"""
用户个人设置服务模块

提供用户个人偏好设置的管理功能，包括默认语音、语速偏好等
"""

import json
import os
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging


@dataclass
class UserSettings:
    """用户设置数据模型"""
    user_id: str
    default_narration_voice: Optional[str] = None
    default_dialogue_voice: Optional[str] = None
    default_speed: float = 1.0
    preferred_format: str = "webm"
    auto_play: bool = False
    show_advanced_options: bool = False
    theme: str = "light"  # light, dark, auto
    language: str = "zh-CN"
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """从字典创建设置对象"""
        return cls(**data)


class UserSettingsService:
    """
    用户设置服务类
    
    提供用户个人偏好设置的管理功能
    """
    
    def __init__(self, settings_dir: str = "user_settings/data"):
        """
        初始化用户设置服务
        
        Args:
            settings_dir: 设置文件存储目录
        """
        self.settings_dir = settings_dir
        self.logger = logging.getLogger(__name__)
        
        # 确保设置目录存在
        os.makedirs(settings_dir, exist_ok=True)
        
        # 缓存已加载的设置
        self._settings_cache: Dict[str, UserSettings] = {}
    
    def get_user_id_from_request(self, request_info: Dict[str, Any]) -> str:
        """
        从请求信息生成用户ID
        
        Args:
            request_info: 包含IP地址、User-Agent等信息的字典
            
        Returns:
            用户ID
        """
        # 使用IP地址和User-Agent生成用户ID
        ip = request_info.get('ip', 'unknown')
        user_agent = request_info.get('user_agent', 'unknown')
        
        # 创建唯一标识符
        identifier = f"{ip}:{user_agent}"
        user_id = hashlib.md5(identifier.encode('utf-8')).hexdigest()[:16]
        
        return user_id
    
    def get_settings_file_path(self, user_id: str) -> str:
        """获取用户设置文件路径"""
        return os.path.join(self.settings_dir, f"{user_id}.json")
    
    def load_user_settings(self, user_id: str) -> UserSettings:
        """
        加载用户设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户设置对象
        """
        # 检查缓存
        if user_id in self._settings_cache:
            return self._settings_cache[user_id]
        
        settings_file = self.get_settings_file_path(user_id)
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                settings = UserSettings.from_dict(data)
                self._settings_cache[user_id] = settings
                
                self.logger.debug(f"加载用户设置: {user_id}")
                return settings
            else:
                # 创建默认设置
                settings = UserSettings(user_id=user_id)
                self.save_user_settings(settings)
                
                self.logger.info(f"创建默认用户设置: {user_id}")
                return settings
                
        except Exception as e:
            self.logger.error(f"加载用户设置失败 {user_id}: {e}")
            # 返回默认设置
            return UserSettings(user_id=user_id)
    
    def save_user_settings(self, settings: UserSettings) -> bool:
        """
        保存用户设置
        
        Args:
            settings: 用户设置对象
            
        Returns:
            是否保存成功
        """
        try:
            settings.updated_at = datetime.now().isoformat()
            settings_file = self.get_settings_file_path(settings.user_id)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新缓存
            self._settings_cache[settings.user_id] = settings
            
            self.logger.info(f"保存用户设置: {settings.user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存用户设置失败 {settings.user_id}: {e}")
            return False
    
    def update_user_settings(self, user_id: str, **kwargs) -> bool:
        """
        更新用户设置
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的设置字段
            
        Returns:
            是否更新成功
        """
        try:
            settings = self.load_user_settings(user_id)
            
            # 验证和更新字段
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    # 特殊验证
                    if key == 'default_speed':
                        value = max(0.5, min(3.0, float(value)))
                    elif key == 'theme' and value not in ['light', 'dark', 'auto']:
                        continue
                    elif key == 'preferred_format' and value not in ['webm', 'mp3', 'wav']:
                        continue
                    
                    setattr(settings, key, value)
            
            return self.save_user_settings(settings)
            
        except Exception as e:
            self.logger.error(f"更新用户设置失败 {user_id}: {e}")
            return False
    
    def export_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        导出用户设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            设置数据字典
        """
        settings = self.load_user_settings(user_id)
        
        export_data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'settings': settings.to_dict()
        }
        
        return export_data
    
    def import_user_settings(self, user_id: str, import_data: Dict[str, Any]) -> bool:
        """
        导入用户设置
        
        Args:
            user_id: 用户ID
            import_data: 导入的设置数据
            
        Returns:
            是否导入成功
        """
        try:
            # 验证导入数据格式
            if 'settings' not in import_data:
                raise ValueError("导入数据格式错误：缺少 settings 字段")
            
            settings_data = import_data['settings']
            settings_data['user_id'] = user_id  # 确保用户ID正确
            
            # 创建设置对象
            settings = UserSettings.from_dict(settings_data)
            
            # 保存设置
            return self.save_user_settings(settings)
            
        except Exception as e:
            self.logger.error(f"导入用户设置失败 {user_id}: {e}")
            return False
    
    def reset_user_settings(self, user_id: str) -> bool:
        """
        重置用户设置为默认值
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否重置成功
        """
        try:
            # 创建默认设置
            default_settings = UserSettings(user_id=user_id)
            
            # 保存默认设置
            return self.save_user_settings(default_settings)
            
        except Exception as e:
            self.logger.error(f"重置用户设置失败 {user_id}: {e}")
            return False
    
    def backup_user_settings(self, user_id: str) -> Optional[str]:
        """
        备份用户设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            备份文件路径，失败时返回None
        """
        try:
            settings = self.load_user_settings(user_id)
            
            # 创建备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{user_id}_backup_{timestamp}.json"
            backup_path = os.path.join(self.settings_dir, 'backups', backup_filename)
            
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 保存备份
            backup_data = {
                'version': '1.0',
                'backup_time': datetime.now().isoformat(),
                'user_id': user_id,
                'settings': settings.to_dict()
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"备份用户设置: {user_id} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"备份用户设置失败 {user_id}: {e}")
            return None
    
    def get_user_backups(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的备份列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            备份信息列表
        """
        backups = []
        backup_dir = os.path.join(self.settings_dir, 'backups')
        
        if not os.path.exists(backup_dir):
            return backups
        
        try:
            for filename in os.listdir(backup_dir):
                if filename.startswith(f"{user_id}_backup_") and filename.endswith('.json'):
                    backup_path = os.path.join(backup_dir, filename)
                    
                    # 获取文件信息
                    stat = os.stat(backup_path)
                    
                    backups.append({
                        'filename': filename,
                        'path': backup_path,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"获取用户备份列表失败 {user_id}: {e}")
        
        return backups
    
    def restore_from_backup(self, user_id: str, backup_path: str) -> bool:
        """
        从备份恢复用户设置
        
        Args:
            user_id: 用户ID
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 验证备份数据
            if backup_data.get('user_id') != user_id:
                raise ValueError("备份文件用户ID不匹配")
            
            # 恢复设置
            return self.import_user_settings(user_id, backup_data)
            
        except Exception as e:
            self.logger.error(f"从备份恢复设置失败 {user_id}: {e}")
            return False
    
    def get_all_users(self) -> List[str]:
        """
        获取所有用户ID列表
        
        Returns:
            用户ID列表
        """
        users = []
        
        try:
            if os.path.exists(self.settings_dir):
                for filename in os.listdir(self.settings_dir):
                    if filename.endswith('.json') and not filename.startswith('.'):
                        user_id = filename[:-5]  # 移除 .json 后缀
                        users.append(user_id)
        
        except Exception as e:
            self.logger.error(f"获取用户列表失败: {e}")
        
        return users
    
    def cleanup_old_settings(self, days: int = 30) -> int:
        """
        清理旧的设置文件
        
        Args:
            days: 保留天数
            
        Returns:
            清理的文件数量
        """
        cleaned_count = 0
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        try:
            if os.path.exists(self.settings_dir):
                for filename in os.listdir(self.settings_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.settings_dir, filename)
                        
                        # 检查文件修改时间
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
                            self.logger.info(f"清理旧设置文件: {filename}")
        
        except Exception as e:
            self.logger.error(f"清理旧设置文件失败: {e}")
        
        return cleaned_count


# 创建全局实例
user_settings_service = UserSettingsService()