"""
字典服务模块

提供文本预处理、发音替换和内容净化功能
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import os


@dataclass
class DictionaryRule:
    """字典规则数据模型"""
    id: str
    type: str  # 'pronunciation' | 'filter'
    pattern: str
    replacement: str
    enabled: bool
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DictionaryRule':
        """从字典创建规则对象"""
        return cls(**data)


class DictionaryService:
    """
    字典服务类
    
    提供文本预处理、发音替换和内容净化功能
    支持正则表达式匹配和动态规则管理
    """
    
    def __init__(self, rules_file: str = "dictionary/rules.json"):
        """
        初始化字典服务
        
        Args:
            rules_file: 规则配置文件路径
        """
        self.rules_file = rules_file
        self.rules: List[DictionaryRule] = []
        self.logger = logging.getLogger(__name__)
        
        # 确保规则文件目录存在
        os.makedirs(os.path.dirname(rules_file), exist_ok=True)
        
        # 加载规则
        self.reload_rules()
    
    def process_text(self, text: str) -> str:
        """
        处理文本，应用所有启用的规则
        
        Args:
            text: 待处理的文本
            
        Returns:
            处理后的文本
        """
        if not text:
            return text
            
        processed_text = text
        
        # 按类型分组处理规则
        pronunciation_rules = [r for r in self.rules if r.type == 'pronunciation' and r.enabled]
        filter_rules = [r for r in self.rules if r.type == 'filter' and r.enabled]
        
        # 先应用发音替换规则
        for rule in pronunciation_rules:
            try:
                processed_text = re.sub(rule.pattern, rule.replacement, processed_text)
                self.logger.debug(f"应用发音规则 {rule.id}: {rule.pattern} -> {rule.replacement}")
            except re.error as e:
                self.logger.error(f"发音规则 {rule.id} 正则表达式错误: {e}")
                continue
        
        # 再应用内容过滤规则
        for rule in filter_rules:
            try:
                processed_text = re.sub(rule.pattern, rule.replacement, processed_text)
                self.logger.debug(f"应用过滤规则 {rule.id}: {rule.pattern} -> {rule.replacement}")
            except re.error as e:
                self.logger.error(f"过滤规则 {rule.id} 正则表达式错误: {e}")
                continue
        
        return processed_text
    
    def add_rule(self, pattern: str, replacement: str, rule_type: str, rule_id: Optional[str] = None) -> str:
        """
        添加新的字典规则
        
        Args:
            pattern: 匹配模式（支持正则表达式）
            replacement: 替换内容
            rule_type: 规则类型 ('pronunciation' | 'filter')
            rule_id: 规则ID，如果不提供则自动生成
            
        Returns:
            规则ID
            
        Raises:
            ValueError: 当规则参数无效时
        """
        # 验证规则类型
        if rule_type not in ['pronunciation', 'filter']:
            raise ValueError(f"无效的规则类型: {rule_type}")
        
        # 验证正则表达式
        if not self.validate_rule(pattern):
            raise ValueError(f"无效的正则表达式: {pattern}")
        
        # 生成规则ID
        if not rule_id:
            rule_id = f"{rule_type}_{len(self.rules) + 1:03d}"
        
        # 检查ID是否已存在
        if any(rule.id == rule_id for rule in self.rules):
            raise ValueError(f"规则ID已存在: {rule_id}")
        
        # 创建新规则
        now = datetime.now().isoformat()
        new_rule = DictionaryRule(
            id=rule_id,
            type=rule_type,
            pattern=pattern,
            replacement=replacement,
            enabled=True,
            created_at=now,
            updated_at=now
        )
        
        # 添加到规则列表
        self.rules.append(new_rule)
        
        # 保存到文件
        self._save_rules()
        
        self.logger.info(f"添加新规则: {rule_id} ({rule_type})")
        return rule_id
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        删除指定的规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功删除
        """
        original_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.id != rule_id]
        
        if len(self.rules) < original_count:
            self._save_rules()
            self.logger.info(f"删除规则: {rule_id}")
            return True
        
        self.logger.warning(f"规则不存在: {rule_id}")
        return False
    
    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """
        更新规则
        
        Args:
            rule_id: 规则ID
            **kwargs: 要更新的字段
            
        Returns:
            是否成功更新
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        
        # 验证更新的字段
        if 'pattern' in kwargs and not self.validate_rule(kwargs['pattern']):
            raise ValueError(f"无效的正则表达式: {kwargs['pattern']}")
        
        if 'type' in kwargs and kwargs['type'] not in ['pronunciation', 'filter']:
            raise ValueError(f"无效的规则类型: {kwargs['type']}")
        
        # 更新规则
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.now().isoformat()
        
        # 保存到文件
        self._save_rules()
        
        self.logger.info(f"更新规则: {rule_id}")
        return True
    
    def get_rule(self, rule_id: str) -> Optional[DictionaryRule]:
        """
        获取指定的规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则对象，如果不存在则返回None
        """
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_all_rules(self) -> List[DictionaryRule]:
        """
        获取所有规则
        
        Returns:
            规则列表
        """
        return self.rules.copy()
    
    def get_rules_by_type(self, rule_type: str) -> List[DictionaryRule]:
        """
        按类型获取规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            指定类型的规则列表
        """
        return [rule for rule in self.rules if rule.type == rule_type]
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        return self.update_rule(rule_id, enabled=True)
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        return self.update_rule(rule_id, enabled=False)
    
    def reload_rules(self) -> None:
        """
        重新加载规则文件
        """
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.rules = []
                for rule_data in data.get('rules', []):
                    try:
                        rule = DictionaryRule.from_dict(rule_data)
                        self.rules.append(rule)
                    except Exception as e:
                        self.logger.error(f"加载规则失败: {rule_data}, 错误: {e}")
                
                self.logger.info(f"成功加载 {len(self.rules)} 条规则")
            else:
                # 创建默认规则文件
                self._create_default_rules()
                self.logger.info("创建默认规则文件")
                
        except Exception as e:
            self.logger.error(f"加载规则文件失败: {e}")
            self.rules = []
    
    def validate_rule(self, pattern: str) -> bool:
        """
        验证正则表达式规则
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            是否有效
        """
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    def _save_rules(self) -> None:
        """保存规则到文件"""
        try:
            data = {
                'rules': [rule.to_dict() for rule in self.rules],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存规则文件失败: {e}")
            raise
    
    def _create_default_rules(self) -> None:
        """创建默认规则"""
        default_rules = [
            {
                'id': 'pronunciation_001',
                'type': 'pronunciation',
                'pattern': r'\bGitHub\b',
                'replacement': '吉特哈布',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 'pronunciation_002',
                'type': 'pronunciation',
                'pattern': r'\bAPI\b',
                'replacement': 'A P I',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 'filter_001',
                'type': 'filter',
                'pattern': r'[敏感词汇]',
                'replacement': '***',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        data = {
            'rules': default_rules,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 重新加载规则
        self.reload_rules()