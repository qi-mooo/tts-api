#!/usr/bin/env python3
"""
配置管理工具
提供命令行接口来管理应用配置
"""

import argparse
import sys
import json
from pathlib import Path
import bcrypt
import secrets

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


def generate_password_hash(password: str) -> str:
    """生成密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def generate_secret_key() -> str:
    """生成Flask会话密钥"""
    return secrets.token_hex(32)


def init_config(args):
    """初始化配置文件"""
    config_file = args.config or "config.json"
    config_manager = ConfigManager(config_file)
    
    print(f"配置文件已初始化: {config_file}")
    
    # 如果需要设置管理员密码
    if args.admin_password:
        password_hash = generate_password_hash(args.admin_password)
        config_manager.set("admin.password_hash", password_hash)
        print("管理员密码已设置")
    
    # 生成会话密钥
    if not config_manager.admin.secret_key:
        secret_key = generate_secret_key()
        config_manager.set("admin.secret_key", secret_key)
        print("会话密钥已生成")
    
    config_manager.save()
    print("配置已保存")


def show_config(args):
    """显示当前配置"""
    config_file = args.config or "config.json"
    config_manager = ConfigManager(config_file)
    
    config_dict = config_manager.get_config_dict()
    
    # 隐藏敏感信息
    if "admin" in config_dict and "password_hash" in config_dict["admin"]:
        config_dict["admin"]["password_hash"] = "***"
    if "admin" in config_dict and "secret_key" in config_dict["admin"]:
        config_dict["admin"]["secret_key"] = "***"
    
    print(json.dumps(config_dict, indent=2, ensure_ascii=False))


def set_config(args):
    """设置配置值"""
    config_file = args.config or "config.json"
    config_manager = ConfigManager(config_file)
    
    # 特殊处理密码设置
    if args.key == "admin.password":
        if not args.value:
            print("错误: 密码不能为空")
            return
        password_hash = generate_password_hash(args.value)
        config_manager.set("admin.password_hash", password_hash)
        print("管理员密码已更新")
    else:
        # 尝试将值转换为适当的类型
        value = args.value
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "").isdigit():
            value = float(value)
        
        config_manager.set(args.key, value)
        print(f"配置已更新: {args.key} = {value}")
    
    config_manager.save()


def get_config(args):
    """获取配置值"""
    config_file = args.config or "config.json"
    config_manager = ConfigManager(config_file)
    
    value = config_manager.get(args.key)
    if value is not None:
        print(f"{args.key} = {value}")
    else:
        print(f"配置项不存在: {args.key}")


def validate_config(args):
    """验证配置"""
    config_file = args.config or "config.json"
    config_manager = ConfigManager(config_file)
    
    if config_manager.validate():
        print("配置验证通过")
    else:
        print("配置验证失败")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TTS应用配置管理工具")
    parser.add_argument("--config", "-c", help="配置文件路径 (默认: config.json)")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init 命令
    init_parser = subparsers.add_parser("init", help="初始化配置文件")
    init_parser.add_argument("--admin-password", help="设置管理员密码")
    
    # show 命令
    subparsers.add_parser("show", help="显示当前配置")
    
    # set 命令
    set_parser = subparsers.add_parser("set", help="设置配置值")
    set_parser.add_argument("key", help="配置键 (支持点号分隔)")
    set_parser.add_argument("value", help="配置值")
    
    # get 命令
    get_parser = subparsers.add_parser("get", help="获取配置值")
    get_parser.add_argument("key", help="配置键 (支持点号分隔)")
    
    # validate 命令
    subparsers.add_parser("validate", help="验证配置")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "init":
            init_config(args)
        elif args.command == "show":
            show_config(args)
        elif args.command == "set":
            set_config(args)
        elif args.command == "get":
            get_config(args)
        elif args.command == "validate":
            validate_config(args)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()