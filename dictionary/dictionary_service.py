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
        
        # 生成简化的规则ID
        if not rule_id:
            rule_id = self._generate_simple_id(rule_type)
        
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
        重新加载规则文件 - 兼容新旧格式
        """
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.rules = []
                
                # 检查文件版本
                version = data.get('version', '1.0')
                rules_data = data.get('rules', [])
                
                if version == '2.0':
                    # 新格式
                    self.logger.info(f"加载新格式规则文件 (v{version})")
                    metadata = data.get('metadata', {})
                    self.logger.debug(f"规则文件元数据: {metadata}")
                else:
                    # 旧格式兼容
                    self.logger.info("加载旧格式规则文件，将在下次保存时升级")
                
                for rule_data in rules_data:
                    try:
                        rule = DictionaryRule.from_dict(rule_data)
                        self.rules.append(rule)
                    except Exception as e:
                        self.logger.error(f"加载规则失败: {rule_data}, 错误: {e}")
                
                self.logger.info(f"成功加载 {len(self.rules)} 条规则")
                
                # 如果是旧格式，自动升级
                if version != '2.0':
                    self.logger.info("自动升级规则文件格式")
                    self._save_rules()
                    
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
    
    def import_rules(self, rules_data: List[Dict[str, Any]], overwrite: bool = False) -> Dict[str, Any]:
        """
        批量导入字典规则
        
        Args:
            rules_data: 规则数据列表，每个元素包含 pattern, replacement, type 等字段
            overwrite: 是否覆盖已存在的规则
            
        Returns:
            导入结果统计
        """
        results = {
            'success_count': 0,
            'error_count': 0,
            'skipped_count': 0,
            'errors': [],
            'imported_ids': []
        }
        
        for i, rule_data in enumerate(rules_data):
            try:
                # 验证必需字段
                if not all(key in rule_data for key in ['pattern', 'replacement', 'type']):
                    results['errors'].append(f"第 {i+1} 条规则缺少必需字段")
                    results['error_count'] += 1
                    continue
                
                # 验证规则类型
                if rule_data['type'] not in ['pronunciation', 'filter']:
                    results['errors'].append(f"第 {i+1} 条规则类型无效: {rule_data['type']}")
                    results['error_count'] += 1
                    continue
                
                # 验证正则表达式
                if not self.validate_rule(rule_data['pattern']):
                    results['errors'].append(f"第 {i+1} 条规则正则表达式无效: {rule_data['pattern']}")
                    results['error_count'] += 1
                    continue
                
                # 检查是否已存在相同的规则
                existing_rule = None
                for rule in self.rules:
                    if rule.pattern == rule_data['pattern'] and rule.type == rule_data['type']:
                        existing_rule = rule
                        break
                
                if existing_rule and not overwrite:
                    results['skipped_count'] += 1
                    continue
                
                # 生成或使用指定的ID
                rule_id = rule_data.get('id')
                if not rule_id:
                    rule_id = self._generate_simple_id(rule_data['type'])
                
                # 如果ID已存在且不允许覆盖，生成新ID
                if any(rule.id == rule_id for rule in self.rules) and not overwrite:
                    rule_id = self._generate_simple_id(rule_data['type'])
                
                # 删除已存在的规则（如果覆盖）
                if existing_rule and overwrite:
                    self.remove_rule(existing_rule.id)
                
                # 添加新规则
                now = datetime.now().isoformat()
                new_rule = DictionaryRule(
                    id=rule_id,
                    type=rule_data['type'],
                    pattern=rule_data['pattern'],
                    replacement=rule_data['replacement'],
                    enabled=rule_data.get('enabled', True),
                    created_at=now,
                    updated_at=now
                )
                
                self.rules.append(new_rule)
                results['success_count'] += 1
                results['imported_ids'].append(rule_id)
                
            except Exception as e:
                results['errors'].append(f"第 {i+1} 条规则导入失败: {str(e)}")
                results['error_count'] += 1
        
        # 保存到文件
        if results['success_count'] > 0:
            self._save_rules()
            self.logger.info(f"批量导入完成: 成功 {results['success_count']}, 失败 {results['error_count']}, 跳过 {results['skipped_count']}")
        
        return results
    
    def export_rules(self, rule_type: Optional[str] = None, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        导出字典规则
        
        Args:
            rule_type: 规则类型过滤，None表示导出所有类型
            enabled_only: 是否只导出启用的规则
            
        Returns:
            规则数据列表
        """
        rules_to_export = self.rules
        
        # 按类型过滤
        if rule_type:
            rules_to_export = [rule for rule in rules_to_export if rule.type == rule_type]
        
        # 按启用状态过滤
        if enabled_only:
            rules_to_export = [rule for rule in rules_to_export if rule.enabled]
        
        # 转换为简化格式
        exported_data = []
        for rule in rules_to_export:
            exported_data.append({
                'id': rule.id,
                'type': rule.type,
                'pattern': rule.pattern,
                'replacement': rule.replacement,
                'enabled': rule.enabled,
                'created_at': rule.created_at,
                'updated_at': rule.updated_at
            })
        
        return exported_data
    
    def _save_rules(self) -> None:
        """保存规则到文件 - 使用简化的结构"""
        try:
            # 统计信息
            enabled_count = len([rule for rule in self.rules if rule.enabled])
            type_counts = {}
            for rule in self.rules:
                type_counts[rule.type] = type_counts.get(rule.type, 0) + 1
            
            data = {
                'version': '2.0',  # 版本标识
                'rules': [rule.to_dict() for rule in self.rules],
                'metadata': {
                    'updated_at': datetime.now().isoformat(),
                    'total_rules': len(self.rules),
                    'enabled_rules': enabled_count,
                    'type_counts': type_counts
                }
            }
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存规则文件失败: {e}")
            raise
    
    def _create_default_rules(self) -> None:
        """创建默认规则 - 使用简化的ID和结构"""
        default_rules = [
            {
                'id': '1',
                'type': 'pronunciation',
                'pattern': r'\bGitHub\b',
                'replacement': '吉特哈布',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': '2',
                'type': 'pronunciation',
                'pattern': r'\bAPI\b',
                'replacement': 'A P I',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': '3',
                'type': 'pronunciation',
                'pattern': r'\bJSON\b',
                'replacement': 'J S O N',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': '4',
                'type': 'filter',
                'pattern': r'敏感词汇',
                'replacement': '***',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        # 简化的配置文件结构
        data = {
            'version': '2.0',  # 版本标识
            'rules': default_rules,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'total_rules': len(default_rules)
            }
        }
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 重新加载规则
        self.reload_rules()
    
    def _generate_simple_id(self, rule_type: str) -> str:
        """生成简化的规则ID - 使用自增数字"""
        # 获取所有规则的数字ID
        existing_ids = []
        for rule in self.rules:
            if rule.id.isdigit():
                existing_ids.append(int(rule.id))
            elif '_' in rule.id and rule.id.split('_')[-1].isdigit():
                # 兼容旧格式
                existing_ids.append(int(rule.id.split('_')[-1]))
        
        next_id = max(existing_ids, default=0) + 1
        return str(next_id)