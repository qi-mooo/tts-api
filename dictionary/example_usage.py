#!/usr/bin/env python3
"""
字典服务使用示例

演示如何使用 DictionaryService 进行文本预处理
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dictionary.dictionary_service import DictionaryService


def main():
    """主函数"""
    print("=== 字典服务使用示例 ===\n")
    
    # 创建字典服务实例
    service = DictionaryService("dictionary/rules.json")
    
    # 示例文本
    test_texts = [
        "我在 GitHub 上开发 API 接口",
        "这个 JSON 格式的 HTTP 请求有问题",
        "文本中包含敏感词需要过滤",
        "GitHub API 返回的 JSON 数据包含不当内容"
    ]
    
    print("1. 文本处理示例:")
    print("-" * 50)
    for i, text in enumerate(test_texts, 1):
        processed = service.process_text(text)
        print(f"原文: {text}")
        print(f"处理后: {processed}")
        print()
    
    print("2. 规则管理示例:")
    print("-" * 50)
    
    # 显示当前规则
    print("当前规则:")
    for rule in service.get_all_rules():
        status = "启用" if rule.enabled else "禁用"
        print(f"  {rule.id}: {rule.type} - {rule.pattern} -> {rule.replacement} ({status})")
    print()
    
    # 添加新规则
    print("添加新的发音规则...")
    rule_id = service.add_rule(
        pattern=r"\bPython\b",
        replacement="派森",
        rule_type="pronunciation"
    )
    print(f"添加规则成功: {rule_id}")
    
    # 测试新规则
    test_text = "我喜欢使用 Python 编程"
    processed = service.process_text(test_text)
    print(f"测试新规则 - 原文: {test_text}")
    print(f"测试新规则 - 处理后: {processed}")
    print()
    
    # 按类型获取规则
    print("发音规则:")
    for rule in service.get_rules_by_type("pronunciation"):
        print(f"  {rule.id}: {rule.pattern} -> {rule.replacement}")
    
    print("\n过滤规则:")
    for rule in service.get_rules_by_type("filter"):
        print(f"  {rule.id}: {rule.pattern} -> {rule.replacement}")
    
    print("\n3. 规则启用/禁用示例:")
    print("-" * 50)
    
    # 禁用一个规则
    print("禁用 GitHub 发音规则...")
    service.disable_rule("pronunciation_001")
    
    test_text = "GitHub 是一个代码托管平台"
    processed = service.process_text(test_text)
    print(f"禁用后 - 原文: {test_text}")
    print(f"禁用后 - 处理后: {processed}")
    
    # 重新启用规则
    print("\n重新启用 GitHub 发音规则...")
    service.enable_rule("pronunciation_001")
    
    processed = service.process_text(test_text)
    print(f"启用后 - 原文: {test_text}")
    print(f"启用后 - 处理后: {processed}")
    
    print("\n=== 示例结束 ===")


if __name__ == "__main__":
    main()