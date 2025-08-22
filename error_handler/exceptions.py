"""
TTS 系统自定义异常类层次结构

定义了所有 TTS 系统中可能出现的异常类型，提供统一的错误处理机制。
"""

from typing import Dict, Any, Optional
import traceback


class TTSError(Exception):
    """TTS 系统基础异常类
    
    所有 TTS 相关异常的基类，提供统一的错误信息格式和错误码机制。
    """
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        """初始化 TTS 异常
        
        Args:
            message: 错误描述信息
            error_code: 错误代码，用于程序化处理
            details: 额外的错误详情字典
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.traceback_info = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式
        
        Returns:
            包含异常信息的字典
        """
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'traceback': self.traceback_info
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ServiceUnavailableError(TTSError):
    """服务不可用异常
    
    当 Edge-TTS 服务或其他依赖服务不可用时抛出。
    """
    
    def __init__(self, service_name: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"服务 {service_name} 当前不可用"
        
        error_code = "TTS_001"
        if details is None:
            details = {}
        details['service_name'] = service_name
        
        super().__init__(message, error_code, details)


class AudioGenerationError(TTSError):
    """音频生成失败异常
    
    当音频生成过程中发生错误时抛出。
    """
    
    def __init__(self, message: str = "音频生成失败", details: Optional[Dict[str, Any]] = None):
        error_code = "TTS_002"
        super().__init__(message, error_code, details)


class ValidationError(TTSError):
    """参数验证失败异常
    
    当输入参数不符合要求时抛出。
    """
    
    def __init__(self, field_name: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"参数 {field_name} 验证失败"
        
        error_code = "VAL_001"
        if details is None:
            details = {}
        details['field_name'] = field_name
        
        super().__init__(message, error_code, details)


class SystemResourceError(TTSError):
    """系统资源不足异常
    
    当系统资源（内存、磁盘空间等）不足时抛出。
    """
    
    def __init__(self, resource_type: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"系统资源不足: {resource_type}"
        
        error_code = "SYS_001"
        if details is None:
            details = {}
        details['resource_type'] = resource_type
        
        super().__init__(message, error_code, details)


class ConfigurationError(TTSError):
    """配置错误异常
    
    当系统配置有误时抛出。
    """
    
    def __init__(self, config_key: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"配置项 {config_key} 错误"
        
        error_code = "CFG_001"
        if details is None:
            details = {}
        details['config_key'] = config_key
        
        super().__init__(message, error_code, details)


class DictionaryError(TTSError):
    """字典服务异常
    
    当字典服务处理过程中发生错误时抛出。
    """
    
    def __init__(self, message: str = "字典服务处理失败", details: Optional[Dict[str, Any]] = None):
        error_code = "DIC_001"
        super().__init__(message, error_code, details)


class CacheError(TTSError):
    """缓存操作异常
    
    当缓存操作失败时抛出。
    """
    
    def __init__(self, operation: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"缓存操作失败: {operation}"
        
        error_code = "CACHE_001"
        if details is None:
            details = {}
        details['operation'] = operation
        
        super().__init__(message, error_code, details)


class AuthenticationError(TTSError):
    """认证失败异常
    
    当用户认证失败时抛出。
    """
    
    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        error_code = "AUTH_001"
        super().__init__(message, error_code, details)


class AuthorizationError(TTSError):
    """授权失败异常
    
    当用户权限不足时抛出。
    """
    
    def __init__(self, action: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if message is None:
            message = f"权限不足，无法执行操作: {action}"
        
        error_code = "AUTH_002"
        if details is None:
            details = {}
        details['action'] = action
        
        super().__init__(message, error_code, details)


class SystemError(TTSError):
    """系统错误异常
    
    当系统级别的错误发生时抛出，如重启失败、服务异常等。
    """
    
    def __init__(self, message: str, error_code: str = "SYS_002", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)