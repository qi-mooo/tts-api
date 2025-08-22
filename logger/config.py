"""
日志配置模块

管理日志系统的配置和初始化
"""

import os
from typing import Dict, Any


class LoggingConfig:
    """日志配置类"""
    
    DEFAULT_CONFIG = {
        'level': 'INFO',
        'file': 'logs/app.log',
        'max_size': '10MB',
        'backup_count': 5,
        'format': 'structured'  # 'structured' 或 'standard'
    }
    
    @classmethod
    def from_env(cls) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = cls.DEFAULT_CONFIG.copy()
        
        # 从环境变量覆盖配置
        if os.getenv('LOG_LEVEL'):
            config['level'] = os.getenv('LOG_LEVEL')
        
        if os.getenv('LOG_FILE'):
            config['file'] = os.getenv('LOG_FILE')
        
        if os.getenv('LOG_MAX_SIZE'):
            config['max_size'] = os.getenv('LOG_MAX_SIZE')
        
        if os.getenv('LOG_BACKUP_COUNT'):
            config['backup_count'] = int(os.getenv('LOG_BACKUP_COUNT'))
        
        if os.getenv('LOG_FORMAT'):
            config['format'] = os.getenv('LOG_FORMAT')
        
        return config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """从字典加载配置"""
        config = cls.DEFAULT_CONFIG.copy()
        config.update(config_dict)
        return config
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """验证配置有效性"""
        required_keys = ['level', 'file', 'max_size', 'backup_count']
        
        # 检查必需的键
        for key in required_keys:
            if key not in config:
                return False
        
        # 验证日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config['level'].upper() not in valid_levels:
            return False
        
        # 验证备份数量
        if not isinstance(config['backup_count'], int) or config['backup_count'] < 0:
            return False
        
        return True