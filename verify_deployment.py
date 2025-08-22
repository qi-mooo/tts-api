#!/usr/bin/env python3
"""
部署验证脚本

验证系统配置、依赖安装和服务可用性
"""

import os
import sys
import json
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Any


class DeploymentVerifier:
    """部署验证器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        
    def verify_python_version(self) -> bool:
        """验证 Python 版本"""
        print("🔍 检查 Python 版本...")
        
        if sys.version_info < (3, 8):
            self.errors.append(f"Python 版本过低: {sys.version}, 需要 3.8+")
            return False
        
        print(f"✅ Python 版本: {sys.version}")
        return True
    
    def verify_dependencies(self) -> bool:
        """验证依赖包"""
        print("🔍 检查依赖包...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.errors.append("requirements.txt 文件不存在")
            return False
        
        # 读取依赖列表
        with open(requirements_file, 'r') as f:
            requirements = [
                line.strip().split('==')[0] 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
        
        missing_packages = []
        for package in requirements:
            try:
                # 处理特殊的包名映射
                import_mapping = {
                    'edge-tts': 'edge_tts',
                    'python-dotenv': 'dotenv',
                    'APScheduler': 'apscheduler',
                    'audioop-lts': 'audioop'  # audioop-lts 提供 audioop 模块
                }
                
                import_name = import_mapping.get(package, package.replace('-', '_').lower())
                importlib.import_module(import_name)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} 未安装")
        
        if missing_packages:
            self.errors.append(f"缺少依赖包: {', '.join(missing_packages)}")
            return False
        
        return True
    
    def verify_project_structure(self) -> bool:
        """验证项目结构"""
        print("🔍 检查项目结构...")
        
        required_dirs = [
            "config", "error_handler", "logger", "dictionary",
            "admin", "health_check", "restart", "audio_cache",
            "templates", "tests"
        ]
        
        required_files = [
            "enhanced_tts_api.py", "config.json.template",
            "requirements.txt", "dockerfile", "docker-compose.yml"
        ]
        
        missing_dirs = []
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists():
                print(f"✅ 目录: {directory}")
            else:
                missing_dirs.append(directory)
                print(f"❌ 目录缺失: {directory}")
        
        missing_files = []
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"✅ 文件: {file_name}")
            else:
                missing_files.append(file_name)
                print(f"❌ 文件缺失: {file_name}")
        
        if missing_dirs:
            self.errors.append(f"缺少目录: {', '.join(missing_dirs)}")
        
        if missing_files:
            self.errors.append(f"缺少文件: {', '.join(missing_files)}")
        
        return len(missing_dirs) == 0 and len(missing_files) == 0
    
    def verify_configuration(self) -> bool:
        """验证配置文件"""
        print("🔍 检查配置文件...")
        
        # 检查配置模板
        template_file = self.project_root / "config.json.template"
        if not template_file.exists():
            self.errors.append("config.json.template 文件不存在")
            return False
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            required_sections = ['tts', 'logging', 'admin', 'dictionary', 'system']
            for section in required_sections:
                if section in template_config:
                    print(f"✅ 配置节: {section}")
                else:
                    self.errors.append(f"配置节缺失: {section}")
                    print(f"❌ 配置节缺失: {section}")
            
        except json.JSONDecodeError as e:
            self.errors.append(f"配置文件格式错误: {e}")
            return False
        
        # 检查环境变量模板
        env_template = self.project_root / ".env.template"
        if env_template.exists():
            print("✅ 环境变量模板存在")
        else:
            self.warnings.append("环境变量模板不存在")
            print("⚠️  环境变量模板不存在")
        
        return True
    
    def verify_docker_config(self) -> bool:
        """验证 Docker 配置"""
        print("🔍 检查 Docker 配置...")
        
        dockerfile = self.project_root / "dockerfile"
        if dockerfile.exists():
            print("✅ Dockerfile 存在")
        else:
            self.errors.append("Dockerfile 不存在")
            return False
        
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            print("✅ docker-compose.yml 存在")
        else:
            self.warnings.append("docker-compose.yml 不存在")
            print("⚠️  docker-compose.yml 不存在")
        
        return True
    
    def verify_logs_directory(self) -> bool:
        """验证日志目录"""
        print("🔍 检查日志目录...")
        
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(exist_ok=True)
                print("✅ 日志目录已创建")
            except Exception as e:
                self.errors.append(f"无法创建日志目录: {e}")
                return False
        else:
            print("✅ 日志目录存在")
        
        # 检查日志目录权限
        if os.access(logs_dir, os.W_OK):
            print("✅ 日志目录可写")
        else:
            self.errors.append("日志目录不可写")
            return False
        
        return True
    
    def verify_network_connectivity(self) -> bool:
        """验证网络连接"""
        print("🔍 检查网络连接...")
        
        try:
            import urllib.request
            
            # 测试 Edge-TTS 服务连接
            url = "https://speech.platform.bing.com"
            req = urllib.request.Request(url, method='HEAD')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    print("✅ Edge-TTS 服务可访问")
                    return True
                else:
                    self.warnings.append(f"Edge-TTS 服务响应异常: {response.status}")
                    print(f"⚠️  Edge-TTS 服务响应异常: {response.status}")
                    return True
        
        except Exception as e:
            self.warnings.append(f"网络连接测试失败: {e}")
            print(f"⚠️  网络连接测试失败: {e}")
            return True  # 网络问题不应该阻止部署
    
    def verify_system_resources(self) -> bool:
        """验证系统资源"""
        print("🔍 检查系统资源...")
        
        try:
            import psutil
            
            # 检查内存
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            if memory_gb >= 2:
                print(f"✅ 内存: {memory_gb:.1f}GB")
            else:
                self.warnings.append(f"内存不足: {memory_gb:.1f}GB (推荐 2GB+)")
                print(f"⚠️  内存不足: {memory_gb:.1f}GB (推荐 2GB+)")
            
            # 检查磁盘空间
            disk = psutil.disk_usage('.')
            disk_gb = disk.free / (1024**3)
            
            if disk_gb >= 5:
                print(f"✅ 可用磁盘空间: {disk_gb:.1f}GB")
            else:
                self.warnings.append(f"磁盘空间不足: {disk_gb:.1f}GB (推荐 5GB+)")
                print(f"⚠️  磁盘空间不足: {disk_gb:.1f}GB (推荐 5GB+)")
            
            return True
            
        except ImportError:
            self.warnings.append("无法检查系统资源 (psutil 未安装)")
            print("⚠️  无法检查系统资源 (psutil 未安装)")
            return True
    
    def run_verification(self) -> bool:
        """运行完整验证"""
        print("🚀 开始部署验证...\n")
        
        checks = [
            ("Python 版本", self.verify_python_version),
            ("依赖包", self.verify_dependencies),
            ("项目结构", self.verify_project_structure),
            ("配置文件", self.verify_configuration),
            ("Docker 配置", self.verify_docker_config),
            ("日志目录", self.verify_logs_directory),
            ("网络连接", self.verify_network_connectivity),
            ("系统资源", self.verify_system_resources),
        ]
        
        passed = 0
        total = len(checks)
        
        for name, check_func in checks:
            print(f"\n--- {name} ---")
            if check_func():
                passed += 1
        
        # 输出结果
        print(f"\n{'='*50}")
        print(f"验证完成: {passed}/{total} 项检查通过")
        
        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors:
            print("\n✅ 部署验证通过！系统可以正常部署。")
            return True
        else:
            print("\n❌ 部署验证失败！请修复上述错误后重试。")
            return False


def main():
    """主函数"""
    verifier = DeploymentVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 系统已准备就绪，可以开始部署！")
        print("\n下一步:")
        print("1. 配置环境变量: cp .env.template .env")
        print("2. 设置管理员密码: python3 setup.py --password your-password")
        print("3. 启动服务: python3 enhanced_tts_api.py")
        print("   或使用 Docker: docker-compose up -d")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()