# 错误处理模块
from .error_handler import ErrorHandler, RetryConfig, error_handler_middleware
from .exceptions import (
    TTSError, ServiceUnavailableError, AudioGenerationError,
    ValidationError, SystemResourceError, ConfigurationError,
    DictionaryError, CacheError, AuthenticationError, AuthorizationError
)

__all__ = [
    'ErrorHandler', 'RetryConfig', 'error_handler_middleware',
    'TTSError', 'ServiceUnavailableError', 'AudioGenerationError',
    'ValidationError', 'SystemResourceError', 'ConfigurationError',
    'DictionaryError', 'CacheError', 'AuthenticationError', 'AuthorizationError'
]