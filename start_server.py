#!/usr/bin/env python3
"""
TTS 服务启动脚本

使用方法:
    ./venv/bin/python3 start_server.py
    ./venv/bin/python3 start_server.py --port 8080
    ./venv/bin/python3 start_server.py --debug
    ./venv/bin/python3 start_server.py --production
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查虚拟环境
    venv_python = Path("venv/bin/python3")
    if not venv_python.exists():
        print("❌ 虚拟环境不存在，请先创建虚拟环境")
        print("   python3 -m venv venv")
        print("   ./venv/bin/pip install -r requirements.txt")
        return False
    
    # 检查依赖
    try:
        result = subprocess.run([str(venv_python), "-c", "import flask, edge_tts, pydub"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ 依赖包缺失，请安装依赖")
            print("   ./venv/bin/pip install -r requirements.txt")
            return False
    except Exception as e:
        print(f"❌ 检查依赖时出错: {e}")
        return False
    
    # 检查配置文件
    if not Path("config.json").exists():
        print("❌ 配置文件 config.json 不存在")
        return False
    
    # 检查日志目录
    Path("logs").mkdir(exist_ok=True)
    
    print("✅ 环境检查通过")
    return True


def check_port(port):
    """检查端口是否被占用"""
    try:
        result = subprocess.run(["lsof", "-i", f":{port}"], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"⚠️  端口 {port} 已被占用:")
            print(result.stdout)
            
            response = input(f"是否要停止占用端口 {port} 的进程? (y/N): ")
            if response.lower() == 'y':
                # 获取占用端口的进程ID
                pids = []
                for line in result.stdout.split('\n')[1:]:  # 跳过标题行
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            pids.append(parts[1])
                
                for pid in pids:
                    try:
                        subprocess.run(["kill", pid], check=True)
                        print(f"✅ 已停止进程 {pid}")
                    except subprocess.CalledProcessError:
                        print(f"❌ 无法停止进程 {pid}")
                        return False
            else:
                print("❌ 端口被占用，无法启动服务")
                return False
    except FileNotFoundError:
        # lsof 命令不存在，跳过检查
        pass
    except Exception as e:
        print(f"⚠️  检查端口时出错: {e}")
    
    return True


def start_development_server(port=8080, debug=False):
    """启动开发服务器"""
    print(f"🚀 启动开发服务器 (端口: {port}, 调试: {debug})...")
    
    env = os.environ.copy()
    if debug:
        env['FLASK_DEBUG'] = '1'
    
    try:
        # 使用 app_enhanced.py 启动
        cmd = ["./venv/bin/python3", "app_enhanced.py"]
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n⚠️  服务被用户停止")
    except Exception as e:
        print(f"❌ 启动服务时出错: {e}")
        return False
    
    return True


def start_production_server(port=8080):
    """启动生产服务器"""
    print(f"🚀 启动生产服务器 (端口: {port})...")
    
    try:
        # 使用 gunicorn 启动
        cmd = ["./venv/bin/gunicorn", "-c", "gunicorn_config.py", "app_enhanced:app"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⚠️  服务被用户停止")
    except Exception as e:
        print(f"❌ 启动生产服务器时出错: {e}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="TTS 服务启动工具")
    parser.add_argument('--port', type=int, default=8080, help='服务端口 (默认: 8080)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--production', action='store_true', help='使用生产模式 (gunicorn)')
    parser.add_argument('--skip-checks', action='store_true', help='跳过环境检查')
    
    args = parser.parse_args()
    
    print("🎯 TTS 服务启动工具")
    print("=" * 50)
    
    # 环境检查
    if not args.skip_checks:
        if not check_environment():
            sys.exit(1)
        
        if not check_port(args.port):
            sys.exit(1)
    
    # 显示服务信息
    print(f"\n📋 服务信息:")
    print(f"   🌐 管理界面: http://localhost:{args.port}/admin")
    print(f"   🔗 API 端点: http://localhost:{args.port}/api")
    print(f"   ❤️  健康检查: http://localhost:{args.port}/health")
    print(f"   👤 默认账号: admin / admin123")
    print(f"   📊 API 状态: http://localhost:{args.port}/api/status")
    
    print(f"\n💡 测试命令 (在另一个终端中运行):")
    print(f"   ./venv/bin/python3 test_quick.py")
    print(f"   curl http://localhost:{args.port}/health")
    print(f"   curl http://localhost:{args.port}/api/status")
    
    print("\n" + "=" * 50)
    print("按 Ctrl+C 停止服务")
    print("=" * 50 + "\n")
    
    # 启动服务
    try:
        if args.production:
            success = start_production_server(args.port)
        else:
            success = start_development_server(args.port, args.debug)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
        sys.exit(0)


if __name__ == "__main__":
    main()