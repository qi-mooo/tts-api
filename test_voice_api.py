#!/usr/bin/env python3
"""
测试语音 API 端点
验证集成到 app_enhanced.py 中的语音管理功能
"""

import requests
import json
import sys
from typing import Dict, Any


class VoiceAPITester:
    """语音 API 测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'VoiceAPITester/1.0'
        })
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, str] = None) -> Dict[str, Any]:
        """测试单个端点"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'data': response.json() if response.content else None,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"请求失败: {e}",
                'status_code': None
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"JSON 解析失败: {e}",
                'status_code': response.status_code,
                'raw_content': response.text[:200]
            }
    
    def test_get_voices(self):
        """测试获取语音列表"""
        print("🎤 测试获取语音列表...")
        
        # 测试默认参数（只获取中文语音）
        result = self.test_endpoint('GET', '/api/voices')
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            print(f"   ✅ 默认请求成功: 获取到 {data.get('count', 0)} 个中文语音")
        else:
            print(f"   ❌ 默认请求失败: {result.get('error', '未知错误')}")
            return False
        
        # 测试获取所有语音
        result = self.test_endpoint('GET', '/api/voices', params={'chinese_only': 'false'})
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            print(f"   ✅ 获取所有语音成功: 获取到 {data.get('count', 0)} 个语音")
        else:
            print(f"   ❌ 获取所有语音失败: {result.get('error', '未知错误')}")
        
        # 测试按性别筛选
        result = self.test_endpoint('GET', '/api/voices', params={'gender': 'Female'})
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            print(f"   ✅ 按性别筛选成功: 获取到 {data.get('count', 0)} 个女性语音")
        else:
            print(f"   ❌ 按性别筛选失败: {result.get('error', '未知错误')}")
        
        # 测试按地区筛选
        result = self.test_endpoint('GET', '/api/voices', params={'locale': 'zh-CN'})
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            print(f"   ✅ 按地区筛选成功: 获取到 {data.get('count', 0)} 个 zh-CN 语音")
        else:
            print(f"   ❌ 按地区筛选失败: {result.get('error', '未知错误')}")
        
        return True
    
    def test_voice_stats(self):
        """测试获取语音统计"""
        print("📊 测试获取语音统计...")
        
        result = self.test_endpoint('GET', '/api/voices/stats')
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            stats = data.get('stats', {})
            print(f"   ✅ 获取统计成功:")
            print(f"      - 总语音数: {stats.get('total_voices', 0)}")
            print(f"      - 中文语音数: {stats.get('chinese_voices', 0)}")
            print(f"      - 中文地区数: {stats.get('chinese_locales', 0)}")
            gender_dist = stats.get('gender_distribution', {})
            print(f"      - 性别分布: 男性 {gender_dist.get('Male', 0)}, 女性 {gender_dist.get('Female', 0)}")
            return True
        else:
            print(f"   ❌ 获取统计失败: {result.get('error', '未知错误')}")
            return False
    
    def test_voice_validation(self):
        """测试语音验证"""
        print("✅ 测试语音验证...")
        
        # 测试有效语音
        test_cases = [
            ('zh-CN-YunjianNeural', True, '有效的中文语音'),
            ('zh-CN-XiaoyiNeural', True, '有效的中文语音'),
            ('en-US-JennyNeural', True, '有效的英文语音'),
            ('zh-CN-NonExistentNeural', False, '不存在的语音'),
            ('', False, '空语音名称')
        ]
        
        success_count = 0
        for voice_name, expected_valid, description in test_cases:
            result = self.test_endpoint('POST', '/api/voices/validate', data={'voice_name': voice_name})
            
            if result['success'] and result['status_code'] == 200:
                data = result['data']
                is_valid = data.get('valid', False)
                if is_valid == expected_valid:
                    print(f"   ✅ {description}: {voice_name} -> {'有效' if is_valid else '无效'}")
                    success_count += 1
                else:
                    print(f"   ❌ {description}: {voice_name} -> 预期 {'有效' if expected_valid else '无效'}, 实际 {'有效' if is_valid else '无效'}")
            elif result['status_code'] == 400 and not voice_name:
                # 空语音名称应该返回 400 错误
                print(f"   ✅ {description}: 正确返回 400 错误")
                success_count += 1
            else:
                print(f"   ❌ {description}: 请求失败 - {result.get('error', '未知错误')}")
        
        return success_count == len(test_cases)
    
    def test_voice_locales(self):
        """测试获取语音地区"""
        print("🌍 测试获取语音地区...")
        
        # 测试获取中文地区
        result = self.test_endpoint('GET', '/api/voices/locales')
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            locales = data.get('locales', [])
            print(f"   ✅ 获取中文地区成功: {len(locales)} 个地区")
            for locale_info in locales[:3]:  # 只显示前3个
                print(f"      - {locale_info['locale']}: {locale_info['voice_count']} 个语音")
        else:
            print(f"   ❌ 获取中文地区失败: {result.get('error', '未知错误')}")
            return False
        
        # 测试获取所有地区
        result = self.test_endpoint('GET', '/api/voices/locales', params={'chinese_only': 'false'})
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            locales = data.get('locales', [])
            print(f"   ✅ 获取所有地区成功: {len(locales)} 个地区")
        else:
            print(f"   ❌ 获取所有地区失败: {result.get('error', '未知错误')}")
        
        return True
    
    def test_voice_search(self):
        """测试语音搜索"""
        print("🔍 测试语音搜索...")
        
        search_queries = [
            ('Yunjian', '搜索特定语音名称'),
            ('Female', '按性别搜索'),
            ('zh-CN', '按地区搜索'),
            ('Taiwan', '搜索台湾语音'),
            ('NonExistent', '搜索不存在的语音')
        ]
        
        success_count = 0
        for query, description in search_queries:
            result = self.test_endpoint('GET', '/api/voices/search', params={'q': query})
            
            if result['success'] and result['status_code'] == 200:
                data = result['data']
                count = data.get('count', 0)
                print(f"   ✅ {description} '{query}': 找到 {count} 个结果")
                success_count += 1
            else:
                print(f"   ❌ {description} '{query}': 搜索失败 - {result.get('error', '未知错误')}")
        
        # 测试空查询（应该返回错误）
        result = self.test_endpoint('GET', '/api/voices/search', params={'q': ''})
        if result['success'] and result['status_code'] == 400:
            print(f"   ✅ 空查询正确返回 400 错误")
            success_count += 1
        else:
            print(f"   ❌ 空查询处理异常")
        
        return success_count == len(search_queries) + 1
    
    def test_root_endpoint(self):
        """测试根端点是否包含语音相关信息"""
        print("🏠 测试根端点...")
        
        result = self.test_endpoint('GET', '/')
        if result['success'] and result['status_code'] == 200:
            data = result['data']
            endpoints = data.get('endpoints', {})
            
            # 检查是否包含语音端点
            voice_endpoints = ['voices', 'voice_stats', 'voice_validate', 'voice_locales', 'voice_search']
            missing_endpoints = [ep for ep in voice_endpoints if ep not in endpoints]
            
            if not missing_endpoints:
                print(f"   ✅ 根端点包含所有语音端点")
                print(f"   ✅ 服务版本: {data.get('version', 'unknown')}")
                voice_stats = data.get('voice_stats', {})
                if voice_stats:
                    print(f"   ✅ 语音统计: {voice_stats}")
                return True
            else:
                print(f"   ❌ 缺少语音端点: {missing_endpoints}")
                return False
        else:
            print(f"   ❌ 根端点请求失败: {result.get('error', '未知错误')}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=== 语音 API 端点测试 ===\n")
        
        # 首先测试服务是否可用
        result = self.test_endpoint('GET', '/health')
        if not result['success'] or result['status_code'] != 200:
            print("❌ 服务不可用，请确保 TTS 服务正在运行")
            return False
        
        print("✅ 服务可用，开始测试语音 API...\n")
        
        tests = [
            ('根端点', self.test_root_endpoint),
            ('语音列表', self.test_get_voices),
            ('语音统计', self.test_voice_stats),
            ('语音验证', self.test_voice_validation),
            ('语音地区', self.test_voice_locales),
            ('语音搜索', self.test_voice_search)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                print()  # 空行分隔
            except Exception as e:
                print(f"   ❌ 测试 {test_name} 时发生异常: {e}\n")
        
        print("=== 测试结果 ===")
        print(f"通过: {passed}/{total}")
        
        if passed == total:
            print("🎉 所有测试通过！语音 API 集成成功。")
            return True
        else:
            print("❌ 部分测试失败，请检查错误信息。")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试语音 API 端点')
    parser.add_argument('--url', default='http://localhost:8080', help='TTS 服务 URL')
    parser.add_argument('--test', choices=['all', 'voices', 'stats', 'validate', 'locales', 'search', 'root'], 
                       default='all', help='要运行的测试')
    
    args = parser.parse_args()
    
    tester = VoiceAPITester(args.url)
    
    if args.test == 'all':
        success = tester.run_all_tests()
    elif args.test == 'voices':
        success = tester.test_get_voices()
    elif args.test == 'stats':
        success = tester.test_voice_stats()
    elif args.test == 'validate':
        success = tester.test_voice_validation()
    elif args.test == 'locales':
        success = tester.test_voice_locales()
    elif args.test == 'search':
        success = tester.test_voice_search()
    elif args.test == 'root':
        success = tester.test_root_endpoint()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())