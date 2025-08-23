#!/usr/bin/env python3
"""
字典功能优化演示脚本

展示简化的ID生成、配置文件结构和批量导入导出功能
"""

import os
import sys
import json
import tempfile
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dictionary.dictionary_service import DictionaryService


def main():
    """主演示函数"""
    print("=== 字典功能优化演示 ===\n")
    
    # 创建临时文件用于演示
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    
    try:
        # 创建字典服务实例
        service = DictionaryService(temp_file.name)
        
        # 1. 演示简化的ID生成
        print("1. 简化的ID生成演示")
        print("-" * 30)
        
        rule_id1 = service.add_rule(r'\bGitHub\b', '吉特哈布', 'pronunciation')
        print(f"添加规则1，ID: {rule_id1} (纯数字ID)")
        
        rule_id2 = service.add_rule(r'\bAPI\b', 'A P I', 'pronunciation')
        print(f"添加规则2，ID: {rule_id2} (自增数字ID)")
        
        rule_id3 = service.add_rule(r'敏感词', '***', 'filter')
        print(f"添加规则3，ID: {rule_id3} (跨类型连续ID)")
        
        # 2. 演示简化的配置文件结构
        print(f"\n2. 简化的配置文件结构演示")
        print("-" * 30)
        
        with open(temp_file.name, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print("配置文件结构:")
        print(f"  版本: {config_data.get('version')}")
        print(f"  规则数量: {len(config_data.get('rules', []))}")
        
        metadata = config_data.get('metadata', {})
        print("元数据:")
        print(f"  总规则数: {metadata.get('total_rules')}")
        print(f"  启用规则数: {metadata.get('enabled_rules')}")
        print(f"  类型统计: {metadata.get('type_counts')}")
        
        # 3. 演示批量导入功能
        print(f"\n3. 批量导入功能演示")
        print("-" * 30)
        
        # 准备批量导入数据
        import_rules = [
            {
                'type': 'pronunciation',
                'pattern': r'\bPython\b',
                'replacement': '派森',
                'enabled': True
            },
            {
                'type': 'pronunciation',
                'pattern': r'\bJSON\b',
                'replacement': 'J S O N',
                'enabled': True
            },
            {
                'type': 'filter',
                'pattern': r'不当内容',
                'replacement': '[已过滤]',
                'enabled': False
            },
            {
                'type': 'pronunciation',
                'pattern': r'\bHTTP\b',
                'replacement': 'H T T P',
                'enabled': True
            }
        ]
        
        print(f"准备导入 {len(import_rules)} 条规则...")
        result = service.import_rules(import_rules)
        
        print("导入结果:")
        print(f"  成功: {result['success_count']} 条")
        print(f"  失败: {result['error_count']} 条")
        print(f"  跳过: {result['skipped_count']} 条")
        print(f"  导入的ID: {result['imported_ids']}")
        
        if result['errors']:
            print("  错误信息:")
            for error in result['errors']:
                print(f"    - {error}")
        
        # 4. 演示导出功能
        print(f"\n4. 导出功能演示")
        print("-" * 30)
        
        # 导出所有规则
        all_rules = service.export_rules()
        print(f"导出所有规则: {len(all_rules)} 条")
        
        # 按类型导出
        pronunciation_rules = service.export_rules(rule_type='pronunciation')
        filter_rules = service.export_rules(rule_type='filter')
        
        print(f"发音规则: {len(pronunciation_rules)} 条")
        print(f"过滤规则: {len(filter_rules)} 条")
        
        # 只导出启用的规则
        enabled_rules = service.export_rules(enabled_only=True)
        print(f"启用的规则: {len(enabled_rules)} 条")
        
        # 5. 演示文本处理
        print(f"\n5. 文本处理演示")
        print("-" * 30)
        
        test_texts = [
            "我在 GitHub 上开发 Python API 接口",
            "这个 JSON 数据通过 HTTP 传输",
            "请处理这些敏感词和不当内容"
        ]
        
        for text in test_texts:
            processed = service.process_text(text)
            print(f"原文: {text}")
            print(f"处理后: {processed}")
            print()
        
        # 6. 演示规则管理
        print(f"6. 规则管理演示")
        print("-" * 30)
        
        # 获取所有规则
        all_rules = service.get_all_rules()
        print(f"当前总规则数: {len(all_rules)}")
        
        # 按类型统计
        type_counts = {}
        enabled_counts = {}
        for rule in all_rules:
            type_counts[rule.type] = type_counts.get(rule.type, 0) + 1
            if rule.enabled:
                enabled_counts[rule.type] = enabled_counts.get(rule.type, 0) + 1
        
        print("规则统计:")
        for rule_type, count in type_counts.items():
            enabled_count = enabled_counts.get(rule_type, 0)
            print(f"  {rule_type}: {count} 条 (启用: {enabled_count})")
        
        # 演示规则操作
        if all_rules:
            sample_rule = all_rules[0]
            print(f"\n演示规则操作 (规则ID: {sample_rule.id}):")
            
            # 禁用规则
            service.disable_rule(sample_rule.id)
            print(f"  禁用规则: {sample_rule.id}")
            
            # 启用规则
            service.enable_rule(sample_rule.id)
            print(f"  启用规则: {sample_rule.id}")
            
            # 更新规则
            service.update_rule(sample_rule.id, replacement=sample_rule.replacement + " (已更新)")
            print(f"  更新规则: {sample_rule.id}")
        
        # 7. 演示向后兼容性
        print(f"\n7. 向后兼容性演示")
        print("-" * 30)
        
        # 创建旧格式文件
        old_format_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        old_format_data = {
            'rules': [
                {
                    'id': 'old_pronunciation_001',
                    'type': 'pronunciation',
                    'pattern': r'\bOldFormat\b',
                    'replacement': '旧格式',
                    'enabled': True,
                    'created_at': '2024-01-01T00:00:00',
                    'updated_at': '2024-01-01T00:00:00'
                }
            ],
            'updated_at': '2024-01-01T00:00:00'
        }
        
        with open(old_format_file.name, 'w', encoding='utf-8') as f:
            json.dump(old_format_data, f, ensure_ascii=False, indent=2)
        old_format_file.close()
        
        # 加载旧格式文件
        old_service = DictionaryService(old_format_file.name)
        old_rules = old_service.get_all_rules()
        
        print(f"加载旧格式文件: {len(old_rules)} 条规则")
        print(f"旧格式规则ID: {old_rules[0].id}")
        
        # 添加新规则，验证ID格式
        new_rule_id = old_service.add_rule(r'\bNewFormat\b', '新格式', 'pronunciation')
        print(f"新添加规则ID: {new_rule_id} (应该是数字格式)")
        
        # 验证文件被升级
        with open(old_format_file.name, 'r', encoding='utf-8') as f:
            upgraded_data = json.load(f)
        print(f"文件版本已升级到: {upgraded_data.get('version')}")
        
        # 清理旧格式文件
        os.unlink(old_format_file.name)
        
        print(f"\n=== 演示完成 ===")
        print("字典功能优化包括:")
        print("✓ 简化的数字ID生成")
        print("✓ 简化的配置文件结构")
        print("✓ 批量导入导出功能")
        print("✓ 向后兼容性支持")
        print("✓ 增强的规则管理")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


if __name__ == '__main__':
    main()