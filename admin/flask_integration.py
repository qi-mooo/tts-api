"""
Flask 集成模块

将管理控制台集成到 Flask 应用中
"""

from flask import Flask, render_template, redirect, url_for
from admin.admin_controller import admin_controller
from config.config_manager import config_manager


def init_admin_app(app: Flask) -> None:
    """
    初始化管理控制台到 Flask 应用
    
    Args:
        app: Flask 应用实例
    """
    # 设置 session 密钥
    app.secret_key = config_manager.admin.secret_key
    
    # 注册管理控制台蓝图
    app.register_blueprint(admin_controller.blueprint)
    
    # 添加管理界面主页路由
    @app.route('/admin')
    def admin_index():
        """管理控制台主页"""
        return render_template('admin.html')
    
    # 重定向根路径到管理界面
    @app.route('/')
    def index():
        """主页重定向到管理界面"""
        return redirect(url_for('admin_index'))
    
    # 设置 session 配置
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # 在生产环境中应该设置为 True（需要 HTTPS）
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=config_manager.admin.session_timeout
    )