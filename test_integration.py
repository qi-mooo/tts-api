#!/usr/bin/env python3
"""
集成测试脚本 - 验证语音管理系统与 TTS 服务的完整集成
"""

import requests
import json
import sys
import time
from typing import Dict, Any


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'IntegrationTester/1.0'
        })
    
    def test_service_health(self):
        """测试服务健康状态"""
        print("🏥 测试服务健康状态...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 服务健康: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"   ❌ 服务不健康: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 健康检查失败: {e}")
            return False
    
    def test_voice_system_integration(self):
        """测试语音系统集成"""
        print("🎤 测试语音系统集成...")
        
        # 1. 检查根端点是否包含语音信息
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get('endpoints', {})
                voice_endpoints = ['voices', 'voice_stats', 'voice_validate']
                
                missing = [ep for ep in voice_endpoints if ep not in endpoints]
                if missing:
                    print(f"   ❌ 缺少语音端点: {missing}")
                    return False
                
                voice_stats = data.get('voice_stats', {})
                if not voice_stats:
                    print(f"   ❌ 根端点缺少语音统计信息")
                    return False
                
                print(f"   ✅ 根端点集成正常")
                print(f"      版本: {data.get('version', 'unknown')}")
                print(f"      语音统计: {voice_stats}")
                return True
            else:
                print(f"   ❌ 根端点访问失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 根端点测试失败: {e}")
            return False
    
    def test_voice_data_consistency(self):
        """测试语音数据一致性"""
        print("📊 测试语音数据一致性...")
        
        try:
            # 获取语音统计
            stats_response = self.session.get(f"{self.base_url}/api/voices/stats")
            if stats_response.status_code != 200:
                print(f"   ❌ 无法获取语音统计: HTTP {stats_response.status_code}")
                return False
            
            stats = stats_response.json()['stats']
            
            # 获取中文语音列表
            voices_response = self.session.get(f"{self.base_url}/api/voices")
            if voices_response.status_code != 200:
                print(f"   ❌ 无法获取语音列表: HTTP {voices_response.status_code}")
                return False
            
            voices_data = voices_response.json()
            actual_count = voices_data['count']
            
            # 验证数据一致性
            expected_chinese_count = stats['chinese_voices']
            if actual_count != expected_chinese_count:
                print(f"   ❌ 语音数量不一致: 统计显示 {expected_chinese_count}, 实际获取 {actual_count}")
                return False
            
            # 验证性别分布
            voices = voices_data['voices']
            male_count = len([v for v in voices if v['gender'] == 'Male'])
            female_count = len([v for v in voices if v['gender'] == 'Female'])
            
            expected_male = stats['gender_distribution']['Male']
            expected_female = stats['gender_distribution']['Female']
            
            if male_count != expected_male or female_count != expected_female:
                print(f"   ❌ 性别分布不一致:")
                print(f"      统计: 男性 {expected_male}, 女性 {expected_female}")
                print(f"      实际: 男性 {male_count}, 女性 {female_count}")
                return False
            
            print(f"   ✅ 语音数据一致性验证通过")
            print(f"      中文语音: {actual_count} 个")
            print(f"      性别分布: 男性 {male_count}, 女性 {female_count}")
            return True
            
        except Exception as e:
            print(f"   ❌ 数据一致性测试失败: {e}")
            return False
    
    def test_voice_validation_with_tts(self):
        """测试语音验证与 TTS 功能的集成"""
        print("🔊 测试语音验证与 TTS 集成...")
        
        try:
            # 获取默认语音
            voices_response = self.session.get(f"{self.base_url}/api/voices?locale=zh-CN")
            if voices_response.status_code != 200:
                print(f"   ❌ 无法获取 zh-CN 语音: HTTP {voices_response.status_code}")
                return False
            
            voices = voices_response.json()['voices']
            if not voices:
                print(f"   ❌ 没有找到 zh-CN 语音")
                return False
            
            # 选择第一个语音进行测试
            test_voice = voices[0]['name']
            print(f"   🎯 测试语音: {test_voice}")
            
            # 验证语音
            validate_response = self.session.post(
                f"{self.base_url}/api/voices/validate",
                json={'voice_name': test_voice}
            )
            
            if validate_response.status_code != 200:
                print(f"   ❌ 语音验证失败: HTTP {validate_response.status_code}")
                return False
            
            validate_data = validate_response.json()
            if not validate_data.get('valid'):
                print(f"   ❌ 语音验证返回无效: {test_voice}")
                return False
            
            # 测试 TTS API（不下载音频，只检查响应）
            tts_response = self.session.get(
                f"{self.base_url}/api",
                params={
                    'text': '测试语音集成',
                    'narr': test_voice,
                    'speed': '1.0'
                },
                stream=True
            )
            
            if tts_response.status_code == 200:
                # 检查响应头
                content_type = tts_response.headers.get('content-type', '')
                if 'audio' in content_type:
                    print(f"   ✅ TTS 集成正常: {test_voice}")
                    print(f"      内容类型: {content_type}")
                    return True
                else:
                    print(f"   ❌ TTS 响应不是音频格式: {content_type}")
                    return False
            else:
                print(f"   ❌ TTS API 调用失败: HTTP {tts_response.status_code}")
                # 尝试获取错误信息
                try:
                    error_data = tts_response.json()
                    print(f"      错误信息: {error_data.get('error', '未知错误')}")
                except:
                    pass
                return False
                
        except Exception as e:
            print(f"   ❌ 语音与 TTS 集成测试失败: {e}")
            return False
    
    def test_api_performance(self):
        """测试 API 性能"""
        print("⚡ 测试 API 性能...")
        
        endpoints_to_test = [
            ('/api/voices/stats', 'GET', None),
            ('/api/voices', 'GET', None),
            ('/api/voices/locales', 'GET', None),
            ('/api/voices/validate', 'POST', {'voice_name': 'zh-CN-YunjianNeural'})
        ]
        
        performance_results = []
        
        for endpoint, method, data in endpoints_to_test:
            try:
                start_time = time.time()
                
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json=data)
                
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # 转换为毫秒
                
                if response.status_code == 200:
                    performance_results.append((endpoint, duration, '✅'))
                    print(f"   ✅ {endpoint}: {duration:.2f}ms")
                else:
                    performance_results.append((endpoint, duration, '❌'))
                    print(f"   ❌ {endpoint}: {duration:.2f}ms (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {endpoint}: 测试失败 - {e}")
                performance_results.append((endpoint, 0, '❌'))
        
        # 性能分析
        successful_tests = [r for r in performance_results if r[2] == '✅']
        if successful_tests:
            avg_duration = sum(r[1] for r in successful_tests) / len(successful_tests)
            max_duration = max(r[1] for r in successful_tests)
            print(f"   📈 性能统计:")
            print(f"      平均响应时间: {avg_duration:.2f}ms")
            print(f"      最大响应时间: {max_duration:.2f}ms")
            
            # 性能评估
            if avg_duration < 100:
                print(f"   🚀 性能优秀 (< 100ms)")
            elif avg_duration < 500:
                print(f"   👍 性能良好 (< 500ms)")
            else:
                print(f"   ⚠️  性能需要优化 (> 500ms)")
        
        return len(successful_tests) == len(endpoints_to_test)
    
    def test_error_handling(self):
        """测试错误处理"""
        print("🛡️ 测试错误处理...")
        
        error_test_cases = [
            # (endpoint, method, data, expected_status, description)
            ('/api/voices/validate', 'POST', {}, 400, '空请求体'),
            ('/api/voices/validate', 'POST', {'voice_name': ''}, 400, '空语音名称'),
            ('/api/voices/search', 'GET', {'q': ''}, 400, '空搜索查询'),
            ('/api/nonexistent', 'GET', None, 404, '不存在的端点'),
        ]
        
        success_count = 0
        
        for endpoint, method, params, expected_status, description in error_test_cases:
            try:
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}", params=params)
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json=params)
                
                if response.status_code == expected_status:
                    print(f"   ✅ {description}: 正确返回 {expected_status}")
                    success_count += 1
                else:
                    print(f"   ❌ {description}: 期望 {expected_status}, 实际 {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {description}: 测试失败 - {e}")
        
        return success_count == len(error_test_cases)
    
    def run_integration_tests(self):
        """运行完整的集成测试"""
        print("=== TTS 语音管理系统集成测试 ===\n")
        
        tests = [
            ('服务健康检查', self.test_service_health),
            ('语音系统集成', self.test_voice_system_integration),
            ('语音数据一致性', self.test_voice_data_consistency),
            ('语音与TTS集成', self.test_voice_validation_with_tts),
            ('API性能测试', self.test_api_performance),
            ('错误处理测试', self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"{'='*50}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} - 通过\n")
                else:
                    print(f"❌ {test_name} - 失败\n")
            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}\n")
        
        print("="*50)
        print("=== 集成测试结果 ===")
        print(f"通过: {passed}/{total}")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 所有集成测试通过！语音管理系统完全集成成功。")
            print("\n✨ 系统功能:")
            print("  - 322+ 个语音支持")
            print("  - 14 个中文语音")
            print("  - 完整的 API 端点")
            print("  - 语音验证和搜索")
            print("  - 与 TTS 服务无缝集成")
            return True
        else:
            print("❌ 部分集成测试失败，请检查错误信息。")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TTS 语音管理系统集成测试')
    parser.add_argument('--url', default='http://localhost:8080', help='TTS 服务 URL')
    parser.add_argument('--quick', action='store_true', help='快速测试（跳过性能测试）')
    
    args = parser.parse_args()
    
    tester = IntegrationTester(args.url)
    
    if args.quick:
        # 快速测试，只运行核心功能
        tests = [
            tester.test_service_health,
            tester.test_voice_system_integration,
            tester.test_voice_data_consistency
        ]
        
        print("=== 快速集成测试 ===\n")
        passed = sum(1 for test in tests if test())
        total = len(tests)
        
        if passed == total:
            print(f"🎉 快速测试通过 ({passed}/{total})")
            return 0
        else:
            print(f"❌ 快速测试失败 ({passed}/{total})")
            return 1
    else:
        # 完整测试
        success = tester.run_integration_tests()
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())