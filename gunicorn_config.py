"""
Gunicorn 配置文件

用于生产环境部署的 Gunicorn 配置
"""

import os
import multiprocessing

# 服务器配置
bind = "0.0.0.0:8080"
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5

# 日志配置
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程配置
preload_app = True
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 性能配置
worker_tmp_dir = "/dev/shm"

def when_ready(server):
    """服务器启动完成时的回调"""
    print("🚀 TTS 服务器启动完成")
    print("🌐 管理界面: http://localhost:8080/admin")
    print("🔗 API 端点: http://localhost:8080/api")
    print("❤️  健康检查: http://localhost:8080/health")

def worker_int(worker):
    """工作进程中断时的回调"""
    print(f"⚠️  工作进程 {worker.pid} 被中断")

def pre_fork(server, worker):
    """工作进程 fork 前的回调"""
    print(f"🔄 启动工作进程 {worker.age}")

def post_fork(server, worker):
    """工作进程 fork 后的回调"""
    print(f"✅ 工作进程 {worker.pid} 已启动")

def pre_exec(server):
    """执行前的回调"""
    print("🔧 准备启动 Gunicorn 服务器...")

def on_exit(server):
    """退出时的回调"""
    print("👋 TTS 服务器已关闭")