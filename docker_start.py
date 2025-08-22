#!/usr/bin/env python3
"""
Docker 环境启动脚本

为 Docker 容器环境配置和启动 TTS 应用
"""

import os
import sys
import json
import logging
from pathlib import Path

def setup_docker_config():
    """设置 Docker 环境配置"""
    config_file = Path("/app/config.json")
    
    # 默认配置
    default_config = {
        "tts": {
            "narration_voice": os.getenv("TTS_NARRATION_VOICE", "zh-CN-YunjianNeural"),
            "dialogue_voice": os.getenv("TTS_DIALOGUE_VOICE", "zh-CN-XiaoyiNeural"),
            "default_speed": float(os.getenv("TTS_DEFAULT_SPEED", "1.2")),
            "cache_size_limit": 10485760,
            "cache_time_limit": 1200
        },
        "logging": {
            "level": os.getenv("TTS_LOG_LEVEL", "INFO"),
            "file": "/app/logs/app.log",
            "max_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "admin": {
            "username": os.getenv("TTS_ADMIN_USERNAME", "admin"),
            "password_hash": "$2b$12$wpsaDgig4ZnAblJMyxWQq.GLOkNY8yrNN0a2ToqfyU/JpecYmQ0vC",  # admin123
            "session_timeout": 3600,
            "secret_key": os.getenv("TTS_SECRET_KEY", "caa2cad010ae1a54bef123fceee071a1e0d062e99ac915fdbda6905642002c12")
        },
        "dictionary": {
            "enabled": True,
            "rules_file": "/app/dictionary/rules.json"
        },
        "system": {
            "debug": os.getenv("FLASK_DEBUG", "0") == "1",
            "host": "0.0.0.0",
            "port": 8080,
            "max_workers": 10
        }
    }
    
    # 如果环境变量中有自定义密码，重新生成哈希
    custom_password = os.getenv("TTS_ADMIN_PASSWORD")
    if custom_password and custom_password != "admin123":
        import bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(custom_password.encode('utf-8'), salt)
        default_config["admin"]["password_hash"] = password_hash.decode('utf-8')
    
    # 写入配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Docker 配置已生成: {config_file}")
    return default_config

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        "/app/logs",
        "/app/audio_cache",
        "/app/data",
        "/app/dictionary"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 目录已创建: {directory}")

def main():
    """主函数"""
    print("🐳 Docker 环境初始化...")
    
    # 设置工作目录
    os.chdir("/app")
    
    # 确保目录存在
    ensure_directories()
    
    # 设置配置
    config = setup_docker_config()
    
    # 显示配置信息
    print("\n📋 当前配置:")
    print(f"  🌐 服务地址: {config['system']['host']}:{config['system']['port']}")
    print(f"  👤 管理员用户: {config['admin']['username']}")
    print(f"  🔊 旁白语音: {config['tts']['narration_voice']}")
    print(f"  💬 对话语音: {config['tts']['dialogue_voice']}")
    print(f"  📊 日志级别: {config['logging']['level']}")
    
    # 启动应用
    print("\n🚀 启动 TTS 应用...")
    print("🌐 管理界面: http://localhost:8080/admin")
    print("🔗 API 端点: http://localhost:8080/api")
    print("❤️  健康检查: http://localhost:8080/health")
    
    # 导入并启动应用
    try:
        from app_with_admin import app
        app.run(
            host=config['system']['host'],
            port=config['system']['port'],
            debug=config['system']['debug']
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()