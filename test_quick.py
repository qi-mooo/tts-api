#!/usr/bin/env python3
"""
快速测试脚本 - 用于在第二个终端中测试 TTS 服务

使用方法:
    ./venv/bin/python3 test_quick.py
    ./venv/bin/python3 test_quick.py --test api
    ./venv/bin/python3 test_quick.py --test health
    ./venv/bin/python3 test_quick.py --test admin
"""

import requests
import json
import time
import argparse
import sys
from typing import Dict, Any


class TTSQuickTester:
    """TTS 服务快速测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> Dict[str, Any]:
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            result = {
                "status": "✅ 成功" if response.status_code == 200 else "❌ 失败",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            }
            print(f"   状态码: {result['status_code']}")
            print(f"   响应时间: {result['response_time']:.3f}s")
            print(f"   服务状态: {result['data'].get('status', 'unknown') if isinstance(result['data'], dict) else 'unknown'}")
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"status": "❌ 失败", "error": str(e)}
    
    def test_api_status(self) -> Dict[str, Any]:
        """测试 API 状态"""
        print("🔍 测试 API 状态...")
        try:
            response = self.session.get(f"{self.base_url}/api/status", timeout=5)
            result = {
                "status": "✅ 成功" if response.status_code == 200 else "❌ 失败",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            }
            print(f"   状态码: {result['status_code']}")
            print(f"   响应时间: {result['response_time']:.3f}s")
            if isinstance(result['data'], dict):
                print(f"   服务版本: {result['data'].get('version', 'unknown')}")
                print(f"   缓存状态: {result['data'].get('cache_stats', {}).get('cache_size', 0)} 项")
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"status": "❌ 失败", "error": str(e)}
    
    def test_tts_api(self, text: str = "测试文本", speed: float = 1.2) -> Dict[str, Any]:
        """测试 TTS API"""
        print(f"🔍 测试 TTS API (文本: '{text}', 语速: {speed})...")
        try:
            params = {"text": text, "speed": speed}
            response = self.session.get(f"{self.base_url}/api", params=params, timeout=30)
            
            result = {
                "status": "✅ 成功" if response.status_code == 200 else "❌ 失败",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.content) if response.content else 0
            }
            
            print(f"   状态码: {result['status_code']}")
            print(f"   响应时间: {result['response_time']:.3f}s")
            print(f"   内容类型: {result['content_type']}")
            print(f"   内容大小: {result['content_length']} 字节")
            
            # 如果是音频内容，保存到文件
            if result['status_code'] == 200 and 'audio' in result['content_type']:
                filename = f"test_audio_{int(time.time())}.webm"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ 音频已保存到: {filename}")
                result['saved_file'] = filename
            elif result['status_code'] != 200:
                # 显示错误信息
                try:
                    error_data = response.json()
                    print(f"   ❌ 错误: {error_data.get('error', {}).get('message', 'unknown')}")
                    result['error_data'] = error_data
                except:
                    print(f"   ❌ 错误: {response.text[:200]}")
                    result['error_text'] = response.text[:200]
            
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"status": "❌ 失败", "error": str(e)}
    
    def test_admin_login(self, username: str = "admin", password: str = "admin123") -> Dict[str, Any]:
        """测试管理员登录"""
        print(f"🔍 测试管理员登录 (用户: {username})...")
        try:
            data = {"username": username, "password": password}
            response = self.session.post(f"{self.base_url}/admin/login", json=data, timeout=5)
            
            result = {
                "status": "✅ 成功" if response.status_code == 200 else "❌ 失败",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }
            
            print(f"   状态码: {result['status_code']}")
            print(f"   响应时间: {result['response_time']:.3f}s")
            
            try:
                response_data = response.json()
                result['data'] = response_data
                if response_data.get('success'):
                    print(f"   ✅ 登录成功")
                else:
                    print(f"   ❌ 登录失败: {response_data.get('message', 'unknown')}")
            except:
                result['text'] = response.text[:200]
                print(f"   响应: {response.text[:100]}")
            
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"status": "❌ 失败", "error": str(e)}
    
    def test_dictionary_rules(self) -> Dict[str, Any]:
        """测试字典规则"""
        print("🔍 测试字典规则...")
        try:
            response = self.session.get(f"{self.base_url}/api/dictionary/rules", timeout=5)
            result = {
                "status": "✅ 成功" if response.status_code == 200 else "❌ 失败",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }
            
            print(f"   状态码: {result['status_code']}")
            print(f"   响应时间: {result['response_time']:.3f}s")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['data'] = data
                    rules_count = len(data.get('rules', []))
                    print(f"   ✅ 字典规则数量: {rules_count}")
                except:
                    print(f"   ❌ 无法解析响应")
            
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"status": "❌ 失败", "error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始运行所有测试...\n")
        
        results = {}
        
        # 基础连通性测试
        results['health'] = self.test_health()
        print()
        
        results['api_status'] = self.test_api_status()
        print()
        
        # 功能测试
        results['tts_simple'] = self.test_tts_api("你好", 1.0)
        print()
        
        results['tts_complex'] = self.test_tts_api('他说："你好世界！"然后离开了。', 1.5)
        print()
        
        # 管理功能测试
        results['admin_login'] = self.test_admin_login()
        print()
        
        results['dictionary'] = self.test_dictionary_rules()
        print()
        
        # 汇总结果
        print("📊 测试结果汇总:")
        success_count = 0
        total_count = len(results)
        
        for test_name, result in results.items():
            status = result.get('status', '❌ 失败')
            print(f"   {test_name}: {status}")
            if '✅' in status:
                success_count += 1
        
        print(f"\n✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        
        return results


def main():
    parser = argparse.ArgumentParser(description="TTS 服务快速测试工具")
    parser.add_argument('--test', choices=['all', 'health', 'api', 'tts', 'admin', 'dict'], 
                       default='all', help='选择要运行的测试')
    parser.add_argument('--url', default='http://localhost:8080', help='服务 URL')
    parser.add_argument('--text', default='测试文本', help='TTS 测试文本')
    parser.add_argument('--speed', type=float, default=1.2, help='TTS 语速')
    
    args = parser.parse_args()
    
    tester = TTSQuickTester(args.url)
    
    print(f"🎯 TTS 服务快速测试工具")
    print(f"📍 目标服务: {args.url}")
    print(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        if args.test == 'all':
            results = tester.run_all_tests()
        elif args.test == 'health':
            results = {'health': tester.test_health()}
        elif args.test == 'api':
            results = {'api_status': tester.test_api_status()}
        elif args.test == 'tts':
            results = {'tts': tester.test_tts_api(args.text, args.speed)}
        elif args.test == 'admin':
            results = {'admin': tester.test_admin_login()}
        elif args.test == 'dict':
            results = {'dictionary': tester.test_dictionary_rules()}
        
        # 检查是否有失败的测试
        has_failures = any('❌' in result.get('status', '') for result in results.values())
        sys.exit(1 if has_failures else 0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()