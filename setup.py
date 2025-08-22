#!/usr/bin/env python3
"""
TTS API 系统设置和配置脚本

用于初始化系统配置、设置管理员密码、验证环境等。
"""

import os
import sys
import json
import bcrypt
import argparse
from pathlib import Path
from typing import Dict, Any


class TTSSetup:
    """TTS 系统设置类"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_file = self.project_root / "config.json"
        self.env_file = self.project_root / ".env"
        
    def create_config(self, force: bool = False) -> None:
        """创建配置文件"""
        if self.config_file.exists() and not force:
            print(f"配置文件已存在: {self.config_file}")
            return
        
        # 默认配置
        config = {
            "tts": {
                "narration_voice": "zh-CN-YunjianNeural",
                "dialogue_voice": "zh-CN-XiaoyiNeural", 
                "default_speed": 1.2,
                "cache_size_limit": 10485760,
                "cache_time_limit": 1200
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "admin": {
                "username": "admin",
                "password_hash": "",
                "session_timeout": 3600
            },
            "dictionary": {
                "enabled": True,
                "rules_file": "dictionary/rules.json"
            },
            "system": {
                "max_workers": 10,
                "health_check_interval": 30,
                "restart_timeout": 60
            }
        }
        
        # 创建目录
        self.config_file.parent.mkdir(exist_ok=True)
        
        # 写入配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"配置文件已创建: {self.config_file}")
    
    def set_admin_password(self, password: str) -> None:
        """设置管理员密码"""
        if not self.config_file.exists():
            print("配置文件不存在，请先运行 setup.py --init")
            return
        
        # 生成密码哈希
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # 读取配置
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新密码哈希
        config['admin']['password_hash'] = password_hash
        
        # 写回配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("管理员密码已设置")
    
    def create_env_file(self, force: bool = False) -> None:
        """创建环境变量文件"""
        if self.env_file.exists() and not force:
            print(f"环境文件已存在: {self.env_file}")
            return
        
        # 从模板复制
        template_file = self.project_root / ".env.template"
        if template_file.exists():
            import shutil
            shutil.copy(template_file, self.env_file)
            print(f"环境文件已创建: {self.env_file}")
        else:
            print("环境文件模板不存在")
    
    def create_directories(self) -> None:
        """创建必要的目录"""
        directories = [
            "logs",
            "dictionary",
            "config",
            "error_handler", 
            "logger",
            "admin",
            "health_check",
            "restart",
            "audio_cache",
            "templates",
            "tests"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            
            # 创建 __init__.py 文件（如果是 Python 模块目录）
            if directory not in ["logs", "templates"]:
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
        
        print("目录结构已创建")
    
    def verify_environment(self) -> bool:
        """验证环境配置"""
        print("验证环境配置...")
        
        success = True
        
        # 检查 Python 版本
        if sys.version_info < (3, 8):
            print("❌ Python 版本需要 3.8 或更高")
            success = False
        else:
            print(f"✅ Python 版本: {sys.version}")
        
        # 检查必要的包
        required_packages = [
            'flask', 'gunicorn', 'pydub', 'edge_tts', 
            'bcrypt', 'apscheduler', 'psutil'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package} 已安装")
            except ImportError:
                print(f"❌ {package} 未安装")
                success = False
        
        # 检查配置文件
        if self.config_file.exists():
            print(f"✅ 配置文件存在: {self.config_file}")
            
            # 验证配置文件格式
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 检查必要的配置项
                required_keys = ['tts', 'logging', 'admin', 'dictionary', 'system']
                for key in required_keys:
                    if key in config:
                        print(f"✅ 配置项 {key} 存在")
                    else:
                        print(f"❌ 配置项 {key} 缺失")
                        success = False
                
                # 检查管理员密码
                if config.get('admin', {}).get('password_hash'):
                    print("✅ 管理员密码已设置")
                else:
                    print("⚠️  管理员密码未设置")
                    
            except json.JSONDecodeError as e:
                print(f"❌ 配置文件格式错误: {e}")
                success = False
        else:
            print(f"❌ 配置文件不存在: {self.config_file}")
            success = False
        
        # 检查目录结构
        required_dirs = ["logs", "dictionary", "templates"]
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists():
                print(f"✅ 目录存在: {directory}")
            else:
                print(f"❌ 目录不存在: {directory}")
                success = False
        
        return success
    
    def install_dependencies(self) -> None:
        """安装依赖包"""
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("requirements.txt 文件不存在")
            return
        
        print("安装依赖包...")
        os.system(f"pip install -r {requirements_file}")
        print("依赖包安装完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TTS API 系统设置脚本")
    parser.add_argument("--init", action="store_true", help="初始化系统配置")
    parser.add_argument("--password", type=str, help="设置管理员密码")
    parser.add_argument("--verify", action="store_true", help="验证环境配置")
    parser.add_argument("--install", action="store_true", help="安装依赖包")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有文件")
    
    args = parser.parse_args()
    
    setup = TTSSetup()
    
    if args.init:
        print("初始化系统配置...")
        setup.create_directories()
        setup.create_config(force=args.force)
        setup.create_env_file(force=args.force)
        print("系统初始化完成")
    
    if args.password:
        setup.set_admin_password(args.password)
    
    if args.verify:
        success = setup.verify_environment()
        if success:
            print("\n✅ 环境验证通过")
        else:
            print("\n❌ 环境验证失败")
            sys.exit(1)
    
    if args.install:
        setup.install_dependencies()
    
    if not any([args.init, args.password, args.verify, args.install]):
        parser.print_help()


if __name__ == "__main__":
    main()