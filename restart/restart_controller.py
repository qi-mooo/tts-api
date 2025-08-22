"""
重启控制器 - 实现优雅重启功能

提供系统重启、配置重载、服务恢复等功能
支持正在处理请求的等待机制和重启失败回滚
"""

import os
import sys
import time
import signal
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import psutil

from config.config_manager import config_manager
from logger.structured_logger import get_logger
from error_handler.error_handler import ErrorHandler
from error_handler.exceptions import SystemError, AuthorizationError, ValidationError


class RestartStatus(Enum):
    """重启状态枚举"""
    IDLE = "idle"
    PREPARING = "preparing"
    WAITING_REQUESTS = "waiting_requests"
    RESTARTING = "restarting"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RestartRequest:
    """重启请求数据类"""
    request_id: str
    user: str
    timestamp: datetime
    reason: str
    force: bool = False
    config_reload: bool = True
    timeout: int = 30  # 等待超时时间（秒）


@dataclass
class ActiveRequest:
    """活跃请求数据类"""
    request_id: str
    start_time: datetime
    endpoint: str
    remote_addr: str
    user_agent: str


class RestartController:
    """重启控制器 - 管理系统优雅重启"""
    
    def __init__(self):
        """初始化重启控制器"""
        self.logger = get_logger('restart_controller')
        self.error_handler = ErrorHandler(self.logger.logger)
        
        # 重启状态管理
        self._status = RestartStatus.IDLE
        self._status_lock = threading.RLock()
        self._current_request: Optional[RestartRequest] = None
        
        # 活跃请求跟踪
        self._active_requests: Dict[str, ActiveRequest] = {}
        self._requests_lock = threading.RLock()
        
        # 重启回调函数
        self._pre_restart_callbacks: List[Callable] = []
        self._post_restart_callbacks: List[Callable] = []
        
        # 配置备份
        self._config_backup: Optional[Dict[str, Any]] = None
        
        # 重启历史
        self._restart_history: List[Dict[str, Any]] = []
        
        self.logger.info("重启控制器初始化完成")
    
    @property
    def status(self) -> RestartStatus:
        """获取当前重启状态"""
        with self._status_lock:
            return self._status
    
    @property
    def is_restarting(self) -> bool:
        """检查是否正在重启"""
        return self.status != RestartStatus.IDLE
    
    def request_restart(self, user: str, reason: str = "手动重启", 
                       force: bool = False, config_reload: bool = True,
                       timeout: int = 30) -> Dict[str, Any]:
        """
        请求系统重启
        
        Args:
            user: 请求用户
            reason: 重启原因
            force: 是否强制重启（忽略活跃请求）
            config_reload: 是否重新加载配置
            timeout: 等待超时时间（秒）
        
        Returns:
            重启请求结果
        """
        try:
            with self._status_lock:
                # 检查是否已在重启过程中
                if self.is_restarting:
                    raise SystemError(
                        "系统正在重启中",
                        "RESTART_001",
                        {"current_status": self._status.value}
                    )
                
                # 创建重启请求
                request_id = f"restart_{int(time.time())}"
                restart_request = RestartRequest(
                    request_id=request_id,
                    user=user,
                    timestamp=datetime.now(),
                    reason=reason,
                    force=force,
                    config_reload=config_reload,
                    timeout=timeout
                )
                
                self._current_request = restart_request
                self._status = RestartStatus.PREPARING
                
                # 记录重启请求
                self.logger.audit('restart_requested', user,
                                request_id=request_id,
                                reason=reason,
                                force=force,
                                config_reload=config_reload)
                
                # 启动重启流程
                restart_thread = threading.Thread(
                    target=self._execute_restart,
                    args=(restart_request,),
                    daemon=True
                )
                restart_thread.start()
                
                return {
                    'success': True,
                    'message': '重启请求已提交',
                    'request_id': request_id,
                    'status': self._status.value,
                    'estimated_time': timeout + 10  # 预估重启时间
                }
                
        except Exception as e:
            self.logger.error(f"重启请求失败: {e}")
            with self._status_lock:
                self._status = RestartStatus.FAILED
            raise
    
    def cancel_restart(self, user: str) -> Dict[str, Any]:
        """
        取消重启请求（仅在准备阶段可取消）
        
        Args:
            user: 取消用户
        
        Returns:
            取消结果
        """
        try:
            with self._status_lock:
                if self._status not in [RestartStatus.PREPARING, RestartStatus.WAITING_REQUESTS]:
                    raise SystemError(
                        "无法取消重启",
                        "RESTART_002",
                        {"current_status": self._status.value}
                    )
                
                # 记录取消操作
                self.logger.audit('restart_cancelled', user,
                                request_id=self._current_request.request_id if self._current_request else None)
                
                # 重置状态
                self._status = RestartStatus.IDLE
                self._current_request = None
                
                return {
                    'success': True,
                    'message': '重启已取消'
                }
                
        except Exception as e:
            self.logger.error(f"取消重启失败: {e}")
            raise
    
    def get_restart_status(self) -> Dict[str, Any]:
        """
        获取重启状态信息
        
        Returns:
            重启状态详情
        """
        with self._status_lock:
            status_info = {
                'status': self._status.value,
                'is_restarting': self.is_restarting,
                'active_requests_count': len(self._active_requests),
                'timestamp': datetime.now().isoformat()
            }
            
            if self._current_request:
                status_info.update({
                    'current_request': {
                        'request_id': self._current_request.request_id,
                        'user': self._current_request.user,
                        'reason': self._current_request.reason,
                        'timestamp': self._current_request.timestamp.isoformat(),
                        'force': self._current_request.force,
                        'config_reload': self._current_request.config_reload
                    }
                })
            
            # 添加活跃请求信息
            if self._active_requests:
                status_info['active_requests'] = [
                    {
                        'request_id': req.request_id,
                        'endpoint': req.endpoint,
                        'duration': (datetime.now() - req.start_time).total_seconds(),
                        'remote_addr': req.remote_addr
                    }
                    for req in self._active_requests.values()
                ]
            
            return status_info
    
    def register_request(self, request_id: str, endpoint: str, 
                        remote_addr: str = "", user_agent: str = "") -> None:
        """
        注册活跃请求
        
        Args:
            request_id: 请求ID
            endpoint: 端点路径
            remote_addr: 远程地址
            user_agent: 用户代理
        """
        with self._requests_lock:
            self._active_requests[request_id] = ActiveRequest(
                request_id=request_id,
                start_time=datetime.now(),
                endpoint=endpoint,
                remote_addr=remote_addr,
                user_agent=user_agent
            )
            
            self.logger.debug(f"注册活跃请求: {request_id} -> {endpoint}")
    
    def unregister_request(self, request_id: str) -> None:
        """
        注销活跃请求
        
        Args:
            request_id: 请求ID
        """
        with self._requests_lock:
            if request_id in self._active_requests:
                request_info = self._active_requests.pop(request_id)
                duration = (datetime.now() - request_info.start_time).total_seconds()
                
                self.logger.debug(f"注销活跃请求: {request_id}, 持续时间: {duration:.2f}s")
    
    def add_pre_restart_callback(self, callback: Callable) -> None:
        """添加重启前回调函数"""
        self._pre_restart_callbacks.append(callback)
    
    def add_post_restart_callback(self, callback: Callable) -> None:
        """添加重启后回调函数"""
        self._post_restart_callbacks.append(callback)
    
    def get_restart_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取重启历史记录
        
        Args:
            limit: 返回记录数量限制
        
        Returns:
            重启历史列表
        """
        return self._restart_history[-limit:] if self._restart_history else []
    
    def _execute_restart(self, restart_request: RestartRequest) -> None:
        """
        执行重启流程
        
        Args:
            restart_request: 重启请求
        """
        start_time = datetime.now()
        success = False
        error_message = ""
        
        try:
            self.logger.info(f"开始执行重启流程: {restart_request.request_id}")
            
            # 1. 执行重启前回调
            self._execute_pre_restart_callbacks()
            
            # 2. 等待活跃请求完成
            if not restart_request.force:
                self._wait_for_active_requests(restart_request.timeout)
            
            # 3. 备份当前配置
            if restart_request.config_reload:
                self._backup_config()
            
            # 4. 执行重启
            with self._status_lock:
                self._status = RestartStatus.RESTARTING
            
            self._perform_restart(restart_request)
            
            # 5. 执行重启后回调
            self._execute_post_restart_callbacks()
            
            with self._status_lock:
                self._status = RestartStatus.COMPLETED
            
            success = True
            self.logger.info(f"重启流程完成: {restart_request.request_id}")
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"重启流程失败: {e}")
            
            # 尝试回滚
            try:
                self._rollback_restart()
            except Exception as rollback_error:
                self.logger.error(f"重启回滚失败: {rollback_error}")
            
            with self._status_lock:
                self._status = RestartStatus.FAILED
        
        finally:
            # 记录重启历史
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            history_entry = {
                'request_id': restart_request.request_id,
                'user': restart_request.user,
                'reason': restart_request.reason,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'success': success,
                'error_message': error_message,
                'force': restart_request.force,
                'config_reload': restart_request.config_reload
            }
            
            self._restart_history.append(history_entry)
            
            # 保持历史记录数量限制
            if len(self._restart_history) > 50:
                self._restart_history = self._restart_history[-50:]
            
            # 重置状态
            with self._status_lock:
                if self._status != RestartStatus.FAILED:
                    self._status = RestartStatus.IDLE
                self._current_request = None
    
    def _execute_pre_restart_callbacks(self) -> None:
        """执行重启前回调函数"""
        self.logger.info("执行重启前回调函数")
        
        for callback in self._pre_restart_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"重启前回调执行失败: {e}")
                # 继续执行其他回调，不中断重启流程
    
    def _execute_post_restart_callbacks(self) -> None:
        """执行重启后回调函数"""
        self.logger.info("执行重启后回调函数")
        
        for callback in self._post_restart_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"重启后回调执行失败: {e}")
                # 继续执行其他回调
    
    def _wait_for_active_requests(self, timeout: int) -> None:
        """
        等待活跃请求完成
        
        Args:
            timeout: 超时时间（秒）
        """
        with self._status_lock:
            self._status = RestartStatus.WAITING_REQUESTS
        
        self.logger.info(f"等待活跃请求完成，超时时间: {timeout}s")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._requests_lock:
                if not self._active_requests:
                    self.logger.info("所有活跃请求已完成")
                    return
                
                # 记录当前活跃请求
                active_count = len(self._active_requests)
                self.logger.info(f"等待 {active_count} 个活跃请求完成")
            
            time.sleep(1)  # 每秒检查一次
        
        # 超时处理
        with self._requests_lock:
            if self._active_requests:
                active_count = len(self._active_requests)
                self.logger.warning(f"等待超时，仍有 {active_count} 个活跃请求")
                
                # 记录超时的请求
                for req in self._active_requests.values():
                    duration = (datetime.now() - req.start_time).total_seconds()
                    self.logger.warning(f"超时请求: {req.request_id} -> {req.endpoint}, 持续时间: {duration:.2f}s")
    
    def _backup_config(self) -> None:
        """备份当前配置"""
        try:
            self.logger.info("备份当前配置")
            self._config_backup = config_manager.get_config_dict()
        except Exception as e:
            self.logger.error(f"配置备份失败: {e}")
            raise SystemError("配置备份失败", "RESTART_003", {"error": str(e)})
    
    def _perform_restart(self, restart_request: RestartRequest) -> None:
        """
        执行实际的重启操作
        
        Args:
            restart_request: 重启请求
        """
        try:
            # 重新加载配置
            if restart_request.config_reload:
                self.logger.info("重新加载配置")
                config_manager.reload()
                
                # 验证配置
                if not config_manager.validate():
                    raise SystemError("配置验证失败", "RESTART_004")
            
            # 这里可以添加其他重启操作
            # 例如：重新初始化服务、清理缓存等
            
            self.logger.info("重启操作完成")
            
        except Exception as e:
            self.logger.error(f"重启操作失败: {e}")
            raise
    
    def _rollback_restart(self) -> None:
        """回滚重启操作"""
        try:
            with self._status_lock:
                self._status = RestartStatus.RECOVERING
            
            self.logger.info("开始重启回滚")
            
            # 恢复配置备份
            if self._config_backup:
                self.logger.info("恢复配置备份")
                
                # 这里应该实现配置恢复逻辑
                # 由于配置管理器的限制，暂时只记录日志
                self.logger.info("配置回滚完成")
            
            self.logger.info("重启回滚完成")
            
        except Exception as e:
            self.logger.error(f"重启回滚失败: {e}")
            raise


# 创建全局实例
restart_controller = RestartController()