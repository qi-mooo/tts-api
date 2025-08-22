"""
统一错误处理器

提供统一的错误处理机制，包括重试策略、降级方案和错误恢复功能。
"""

import time
import random
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Union
from functools import wraps
from flask import Response, jsonify, request

from .exceptions import (
    TTSError, ServiceUnavailableError, AudioGenerationError,
    ValidationError, SystemResourceError, ConfigurationError,
    DictionaryError, CacheError, AuthenticationError, AuthorizationError
)


class RetryConfig:
    """重试配置类"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0,
                 jitter: bool = True):
        """初始化重试配置
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            backoff_factor: 退避因子
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


class ErrorHandler:
    """统一错误处理器
    
    提供错误处理、重试机制、降级策略等功能。
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化错误处理器
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger or logging.getLogger(__name__)
        self.retry_config = RetryConfig()
        
        # 降级策略配置
        self.fallback_voices = {
            'zh-CN-YunjianNeural': ['zh-CN-XiaoyiNeural', 'zh-CN-YunyangNeural'],
            'zh-CN-XiaoyiNeural': ['zh-CN-YunjianNeural', 'zh-CN-YunyangNeural'],
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Response:
        """统一错误处理入口
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            
        Returns:
            Flask Response 对象
        """
        context = context or {}
        
        # 记录错误日志
        self._log_error(error, context)
        
        # 根据异常类型处理
        if isinstance(error, TTSError):
            return self._handle_tts_error(error, context)
        elif isinstance(error, ValueError):
            return self._handle_validation_error(error, context)
        elif isinstance(error, ConnectionError):
            return self._handle_connection_error(error, context)
        elif isinstance(error, MemoryError):
            return self._handle_system_error(error, context)
        else:
            return self._handle_unknown_error(error, context)
    
    def _handle_tts_error(self, error: TTSError, context: Dict[str, Any]) -> Response:
        """处理 TTS 相关错误"""
        status_code = self._get_status_code_for_error(error)
        
        response_data = {
            'success': False,
            'error': error.to_dict(),
            'timestamp': time.time(),
            'request_id': context.get('request_id', 'unknown')
        }
        
        return jsonify(response_data), status_code
    
    def _handle_validation_error(self, error: Exception, context: Dict[str, Any]) -> Response:
        """处理参数验证错误"""
        validation_error = ValidationError(
            field_name='unknown',
            message=str(error),
            details={'original_error': str(error)}
        )
        return self._handle_tts_error(validation_error, context)
    
    def _handle_connection_error(self, error: Exception, context: Dict[str, Any]) -> Response:
        """处理连接错误"""
        service_error = ServiceUnavailableError(
            service_name='edge-tts',
            message=f"服务连接失败: {str(error)}",
            details={'original_error': str(error)}
        )
        return self._handle_tts_error(service_error, context)
    
    def _handle_system_error(self, error: Exception, context: Dict[str, Any]) -> Response:
        """处理系统资源错误"""
        system_error = SystemResourceError(
            resource_type='memory',
            message=f"系统资源不足: {str(error)}",
            details={'original_error': str(error)}
        )
        return self._handle_tts_error(system_error, context)
    
    def _handle_unknown_error(self, error: Exception, context: Dict[str, Any]) -> Response:
        """处理未知错误"""
        unknown_error = TTSError(
            message=f"未知错误: {str(error)}",
            error_code="UNKNOWN_001",
            details={'original_error': str(error), 'error_type': type(error).__name__}
        )
        return self._handle_tts_error(unknown_error, context)
    
    def _get_status_code_for_error(self, error: TTSError) -> int:
        """根据错误类型获取 HTTP 状态码"""
        status_code_map = {
            'TTS_001': 503,  # Service Unavailable
            'TTS_002': 500,  # Internal Server Error
            'VAL_001': 400,  # Bad Request
            'SYS_001': 503,  # Service Unavailable
            'CFG_001': 500,  # Internal Server Error
            'DIC_001': 500,  # Internal Server Error
            'CACHE_001': 500,  # Internal Server Error
            'AUTH_001': 401,  # Unauthorized
            'AUTH_002': 403,  # Forbidden
        }
        return status_code_map.get(error.error_code, 500)
    
    def _log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """记录错误日志"""
        log_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'request_path': getattr(request, 'path', 'unknown') if request else 'unknown',
            'request_method': getattr(request, 'method', 'unknown') if request else 'unknown',
        }
        
        if isinstance(error, TTSError):
            log_data.update({
                'error_code': error.error_code,
                'error_details': error.details
            })
        
        self.logger.error(f"处理错误: {str(error)}", extra=log_data, exc_info=True)
    
    def retry_with_backoff(self, func: Callable, *args, 
                          retry_config: Optional[RetryConfig] = None, 
                          **kwargs) -> Any:
        """使用指数退避算法重试函数执行
        
        Args:
            func: 要重试的函数
            *args: 函数位置参数
            retry_config: 重试配置，如果为 None 则使用默认配置
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        config = retry_config or self.retry_config
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    func_name = getattr(func, '__name__', str(func))
                    self.logger.info(f"函数 {func_name} 在第 {attempt + 1} 次尝试后成功执行")
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt == config.max_retries:
                    func_name = getattr(func, '__name__', str(func))
                    self.logger.error(f"函数 {func_name} 在 {config.max_retries + 1} 次尝试后仍然失败")
                    break
                
                # 计算延迟时间
                delay = min(
                    config.base_delay * (config.backoff_factor ** attempt),
                    config.max_delay
                )
                
                # 添加随机抖动
                if config.jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                func_name = getattr(func, '__name__', str(func))
                self.logger.warning(
                    f"函数 {func_name} 第 {attempt + 1} 次执行失败，{delay:.2f}秒后重试: {str(e)}"
                )
                
                time.sleep(delay)
        
        raise last_exception
    
    def with_fallback_voice(self, original_voice: str, func: Callable, *args, **kwargs) -> Any:
        """使用降级语音重试
        
        Args:
            original_voice: 原始语音
            func: 要执行的函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        # 首先尝试原始语音
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"使用语音 {original_voice} 失败: {str(e)}")
            
            # 尝试降级语音
            fallback_voices = self.fallback_voices.get(original_voice, [])
            
            for fallback_voice in fallback_voices:
                try:
                    self.logger.info(f"尝试使用降级语音: {fallback_voice}")
                    
                    # 更新 kwargs 中的语音参数
                    if 'voice' in kwargs:
                        kwargs['voice'] = fallback_voice
                    
                    result = func(*args, **kwargs)
                    self.logger.info(f"使用降级语音 {fallback_voice} 成功")
                    return result
                    
                except Exception as fallback_error:
                    self.logger.warning(f"降级语音 {fallback_voice} 也失败: {str(fallback_error)}")
                    continue
            
            # 所有降级方案都失败，抛出原始异常
            raise e
    
    def circuit_breaker(self, failure_threshold: int = 5, 
                       recovery_timeout: int = 60) -> Callable:
        """熔断器装饰器
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间（秒）
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            func._failure_count = 0
            func._last_failure_time = 0
            func._is_open = False
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # 检查熔断器状态
                if func._is_open:
                    if current_time - func._last_failure_time > recovery_timeout:
                        # 尝试恢复
                        func._is_open = False
                        func._failure_count = 0
                        self.logger.info(f"熔断器恢复: {func.__name__}")
                    else:
                        raise ServiceUnavailableError(
                            service_name=func.__name__,
                            message="服务熔断中，请稍后重试"
                        )
                
                try:
                    result = func(*args, **kwargs)
                    # 成功执行，重置失败计数
                    func._failure_count = 0
                    return result
                    
                except Exception as e:
                    func._failure_count += 1
                    func._last_failure_time = current_time
                    
                    if func._failure_count >= failure_threshold:
                        func._is_open = True
                        self.logger.error(f"熔断器开启: {func.__name__}")
                    
                    raise e
            
            return wrapper
        return decorator


def error_handler_middleware(error_handler: ErrorHandler):
    """Flask 错误处理中间件
    
    Args:
        error_handler: 错误处理器实例
        
    Returns:
        Flask 错误处理函数
    """
    def handle_exception(error: Exception) -> Response:
        """处理 Flask 应用中的异常"""
        context = {
            'request_id': getattr(request, 'id', None),
            'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown',
            'remote_addr': request.remote_addr if request else 'unknown'
        }
        
        return error_handler.handle_error(error, context)
    
    return handle_exception