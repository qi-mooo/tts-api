#!/usr/bin/env python3
"""
快速检查服务状态
"""

import requests
import sys
import time

def check_service(url="http://localhost:8080"):
    """检查服务是否运行"""
    try:
        print(f"🔍 检查服务状态: {url}")
        
        # 检查健康状态
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正在运行")
            return True
        else:
            print(f"❌ 服务响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    success = check_service(url)
    sys.exit(0 if success else 1)