"""
字典服务单元测试
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dictionary.dictionary_service import DictionaryService, DictionaryRule


class TestDictionaryRule(unittest.TestCase):
    """字典规则数据模型测试"""
    
    def test_rule_creation(self):
        """测试规则创建"""
        rule = DictionaryRule(
            id="test_001",
            type="pronunciation",
            pattern="test",
            replacement="测试",
            enabled=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        self.assertEqual(rule.id, "test_001")
        self.assertEqual(rule.type, "pronunciation")
        self.assertEqual(rule.pattern, "test")
        self.assertEqual(rule.replacement, "测试")
        self.assertTrue(rule.enabled)
    
    def test_rule_to_dict(self):
        """测试规则转换为字典"""
        rule = DictionaryRule(
            id="test_001",
            type="pronunciation",
            pattern="test",
            replacement="测试",
            enabled=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        rule_dict = rule.to_dict()
        expected = {
            'id': 'test_001',
            'type': 'pronunciation',
            'pattern': 'test',
            'replacement': '测试',
            'enabled': True,
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
        
        self.assertEqual(rule_dict, expected)
    
    def test_rule_from_dict(self):
        """测试从字典创建规则"""
        rule_data = {
            'id': 'test_001',
            'type': 'pronunciation',
            'pattern': 'test',
            'replacement': '测试',
            'enabled': True,
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
        
        rule = DictionaryRule.from_dict(rule_data)
        
        self.assertEqual(rule.id, "test_001")
        self.assertEqual(rule.type, "pronunciation")
        self.assertEqual(rule.pattern, "test")
        self.assertEqual(rule.replacement, "测试")


class TestDictionaryService(unittest.TestCase):
    """字典服务测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时文件用于测试
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        # 创建测试规则数据
        self.test_rules = {
            "rules": [
                {
                    "id": "pronunciation_001",
                    "type": "pronunciation",
                    "pattern": "\\bGitHub\\b",
                    "replacement": "吉特哈布",
                    "enabled": True,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                },
                {
                    "id": "filter_001",
                    "type": "filter",
                    "pattern": "敏感词",
                    "replacement": "***",
                    "enabled": True,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "updated_at": "2024-01-01T00:00:00"
        }
        
        # 写入测试数据
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(self.test_rules, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = DictionaryService(self.temp_file.name)
        
        self.assertEqual(len(service.rules), 2)
        self.assertEqual(service.rules[0].id, "pronunciation_001")
        self.assertEqual(service.rules[1].id, "filter_001")
    
    def test_process_text_pronunciation(self):
        """测试发音替换功能"""
        service = DictionaryService(self.temp_file.name)
        
        text = "我在使用 GitHub 进行开发"
        result = service.process_text(text)
        
        self.assertEqual(result, "我在使用 吉特哈布 进行开发")
    
    def test_process_text_filter(self):
        """测试内容过滤功能"""
        service = DictionaryService(self.temp_file.name)
        
        text = "这里有敏感词需要过滤"
        result = service.process_text(text)
        
        self.assertEqual(result, "这里有***需要过滤")
    
    def test_process_text_combined(self):
        """测试组合处理功能"""
        service = DictionaryService(self.temp_file.name)
        
        text = "GitHub 上有敏感词内容"
        result = service.process_text(text)
        
        self.assertEqual(result, "吉特哈布 上有***内容")
    
    def test_process_empty_text(self):
        """测试空文本处理"""
        service = DictionaryService(self.temp_file.name)
        
        self.assertEqual(service.process_text(""), "")
        self.assertEqual(service.process_text(None), None)
    
    def test_add_rule(self):
        """测试添加规则"""
        service = DictionaryService(self.temp_file.name)
        
        rule_id = service.add_rule(
            pattern="\\btest\\b",
            replacement="测试",
            rule_type="pronunciation"
        )
        
        self.assertIsNotNone(rule_id)
        self.assertEqual(len(service.rules), 3)
        
        # 测试新规则是否生效
        result = service.process_text("This is a test")
        self.assertEqual(result, "This is a 测试")
    
    def test_add_rule_with_custom_id(self):
        """测试使用自定义ID添加规则"""
        service = DictionaryService(self.temp_file.name)
        
        rule_id = service.add_rule(
            pattern="\\bcustom\\b",
            replacement="自定义",
            rule_type="pronunciation",
            rule_id="custom_001"
        )
        
        self.assertEqual(rule_id, "custom_001")
        rule = service.get_rule("custom_001")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.pattern, "\\bcustom\\b")
    
    def test_add_rule_invalid_type(self):
        """测试添加无效类型规则"""
        service = DictionaryService(self.temp_file.name)
        
        with self.assertRaises(ValueError):
            service.add_rule(
                pattern="test",
                replacement="测试",
                rule_type="invalid_type"
            )
    
    def test_add_rule_invalid_pattern(self):
        """测试添加无效正则表达式规则"""
        service = DictionaryService(self.temp_file.name)
        
        with self.assertRaises(ValueError):
            service.add_rule(
                pattern="[invalid",  # 无效的正则表达式
                replacement="测试",
                rule_type="pronunciation"
            )
    
    def test_add_rule_duplicate_id(self):
        """测试添加重复ID规则"""
        service = DictionaryService(self.temp_file.name)
        
        with self.assertRaises(ValueError):
            service.add_rule(
                pattern="test",
                replacement="测试",
                rule_type="pronunciation",
                rule_id="pronunciation_001"  # 已存在的ID
            )
    
    def test_remove_rule(self):
        """测试删除规则"""
        service = DictionaryService(self.temp_file.name)
        
        # 删除存在的规则
        result = service.remove_rule("pronunciation_001")
        self.assertTrue(result)
        self.assertEqual(len(service.rules), 1)
        
        # 删除不存在的规则
        result = service.remove_rule("nonexistent")
        self.assertFalse(result)
    
    def test_update_rule(self):
        """测试更新规则"""
        service = DictionaryService(self.temp_file.name)
        
        # 更新存在的规则
        result = service.update_rule("pronunciation_001", replacement="新替换")
        self.assertTrue(result)
        
        rule = service.get_rule("pronunciation_001")
        self.assertEqual(rule.replacement, "新替换")
        
        # 更新不存在的规则
        result = service.update_rule("nonexistent", replacement="测试")
        self.assertFalse(result)
    
    def test_update_rule_invalid_pattern(self):
        """测试更新规则为无效正则表达式"""
        service = DictionaryService(self.temp_file.name)
        
        with self.assertRaises(ValueError):
            service.update_rule("pronunciation_001", pattern="[invalid")
    
    def test_update_rule_invalid_type(self):
        """测试更新规则为无效类型"""
        service = DictionaryService(self.temp_file.name)
        
        with self.assertRaises(ValueError):
            service.update_rule("pronunciation_001", type="invalid_type")
    
    def test_get_rule(self):
        """测试获取规则"""
        service = DictionaryService(self.temp_file.name)
        
        # 获取存在的规则
        rule = service.get_rule("pronunciation_001")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.id, "pronunciation_001")
        
        # 获取不存在的规则
        rule = service.get_rule("nonexistent")
        self.assertIsNone(rule)
    
    def test_get_all_rules(self):
        """测试获取所有规则"""
        service = DictionaryService(self.temp_file.name)
        
        rules = service.get_all_rules()
        self.assertEqual(len(rules), 2)
        self.assertIsInstance(rules, list)
    
    def test_get_rules_by_type(self):
        """测试按类型获取规则"""
        service = DictionaryService(self.temp_file.name)
        
        pronunciation_rules = service.get_rules_by_type("pronunciation")
        self.assertEqual(len(pronunciation_rules), 1)
        self.assertEqual(pronunciation_rules[0].type, "pronunciation")
        
        filter_rules = service.get_rules_by_type("filter")
        self.assertEqual(len(filter_rules), 1)
        self.assertEqual(filter_rules[0].type, "filter")
    
    def test_enable_disable_rule(self):
        """测试启用/禁用规则"""
        service = DictionaryService(self.temp_file.name)
        
        # 禁用规则
        result = service.disable_rule("pronunciation_001")
        self.assertTrue(result)
        
        rule = service.get_rule("pronunciation_001")
        self.assertFalse(rule.enabled)
        
        # 测试禁用的规则不生效
        text = "GitHub 测试"
        result = service.process_text(text)
        self.assertEqual(result, "GitHub 测试")  # 不应该被替换
        
        # 重新启用规则
        result = service.enable_rule("pronunciation_001")
        self.assertTrue(result)
        
        rule = service.get_rule("pronunciation_001")
        self.assertTrue(rule.enabled)
        
        # 测试启用的规则生效
        result = service.process_text(text)
        self.assertEqual(result, "吉特哈布 测试")
    
    def test_validate_rule(self):
        """测试规则验证"""
        service = DictionaryService(self.temp_file.name)
        
        # 有效的正则表达式
        self.assertTrue(service.validate_rule("\\btest\\b"))
        self.assertTrue(service.validate_rule(".*"))
        self.assertTrue(service.validate_rule("\\d+"))
        
        # 无效的正则表达式
        self.assertFalse(service.validate_rule("[invalid"))
        self.assertFalse(service.validate_rule("*"))
        self.assertFalse(service.validate_rule("(unclosed"))
    
    def test_reload_rules(self):
        """测试重新加载规则"""
        service = DictionaryService(self.temp_file.name)
        
        # 修改规则文件
        new_rules = {
            "rules": [
                {
                    "id": "new_rule",
                    "type": "pronunciation",
                    "pattern": "\\bnew\\b",
                    "replacement": "新的",
                    "enabled": True,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ],
            "updated_at": "2024-01-01T00:00:00"
        }
        
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(new_rules, f, ensure_ascii=False, indent=2)
        
        # 重新加载
        service.reload_rules()
        
        self.assertEqual(len(service.rules), 1)
        self.assertEqual(service.rules[0].id, "new_rule")
    
    def test_nonexistent_rules_file(self):
        """测试不存在的规则文件"""
        nonexistent_file = "/tmp/nonexistent_rules.json"
        if os.path.exists(nonexistent_file):
            os.unlink(nonexistent_file)
        
        service = DictionaryService(nonexistent_file)
        
        # 应该创建默认规则
        self.assertGreater(len(service.rules), 0)
        self.assertTrue(os.path.exists(nonexistent_file))
        
        # 清理
        if os.path.exists(nonexistent_file):
            os.unlink(nonexistent_file)
    
    @patch('dictionary.dictionary_service.logging.getLogger')
    def test_logging(self, mock_logger):
        """测试日志记录"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        service = DictionaryService(self.temp_file.name)
        
        # 测试处理文本时的日志
        service.process_text("GitHub 测试")
        
        # 验证日志调用
        mock_logger_instance.debug.assert_called()
    
    def test_regex_error_handling(self):
        """测试正则表达式错误处理"""
        service = DictionaryService(self.temp_file.name)
        
        # 添加一个无效的规则（绕过验证）
        invalid_rule = DictionaryRule(
            id="invalid_rule",
            type="pronunciation",
            pattern="[invalid",  # 无效正则表达式
            replacement="测试",
            enabled=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        service.rules.append(invalid_rule)
        
        # 处理文本时应该跳过无效规则
        result = service.process_text("test text")
        self.assertEqual(result, "test text")  # 应该返回原文本


if __name__ == '__main__':
    unittest.main()