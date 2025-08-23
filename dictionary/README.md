# 字典服务模块

字典服务模块提供文本预处理、发音替换和内容净化功能，支持正则表达式匹配和动态规则管理。

## 功能特性

- **发音替换**: 将英文术语替换为中文发音，提升语音合成效果
- **内容过滤**: 过滤敏感词汇和不当内容
- **正则表达式支持**: 支持复杂的模式匹配
- **动态规则管理**: 运行时添加、删除、修改规则
- **规则启用/禁用**: 灵活控制规则的生效状态
- **持久化存储**: 规则自动保存到 JSON 文件

## 快速开始

### 基本使用

```python
from dictionary import DictionaryService

# 创建字典服务实例
service = DictionaryService("dictionary/rules.json")

# 处理文本
text = "我在 GitHub 上开发 API 接口"
processed = service.process_text(text)
print(processed)  # 输出: 我在 吉特哈布 上开发 A P I 接口
```

### 规则管理

```python
# 添加发音规则 - 自动生成简化ID
rule_id = service.add_rule(
    pattern=r"\bPython\b",
    replacement="派森",
    rule_type="pronunciation"
)
print(f"生成的规则ID: {rule_id}")  # 输出: 1

# 添加过滤规则
service.add_rule(
    pattern="敏感词",
    replacement="***",
    rule_type="filter"
)

# 获取所有规则
rules = service.get_all_rules()

# 按类型获取规则
pronunciation_rules = service.get_rules_by_type("pronunciation")
filter_rules = service.get_rules_by_type("filter")

# 启用/禁用规则 - 使用简化ID
service.disable_rule("1")
service.enable_rule("1")

# 更新规则
service.update_rule("1", replacement="新的替换")

# 删除规则
service.remove_rule("1")
```

### 批量导入导出

```python
# 批量导入规则
import_data = [
    {
        "type": "pronunciation",
        "pattern": r"\bAPI\b",
        "replacement": "A P I",
        "enabled": True
    },
    {
        "type": "filter",
        "pattern": "不当内容",
        "replacement": "[已过滤]",
        "enabled": True
    }
]

result = service.import_rules(import_data, overwrite=False)
print(f"导入结果: 成功 {result['success_count']}, 失败 {result['error_count']}")

# 导出规则
all_rules = service.export_rules()  # 导出所有规则
pronunciation_only = service.export_rules(rule_type="pronunciation")  # 按类型导出
enabled_only = service.export_rules(enabled_only=True)  # 只导出启用的规则
```

## 规则配置文件格式

规则存储在 JSON 文件中，使用简化的结构格式：

```json
{
  "version": "2.0",
  "rules": [
    {
      "id": "1",
      "type": "pronunciation",
      "pattern": "\\bGitHub\\b",
      "replacement": "吉特哈布",
      "enabled": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    },
    {
      "id": "2",
      "type": "filter",
      "pattern": "敏感词",
      "replacement": "***",
      "enabled": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "metadata": {
    "updated_at": "2024-01-01T00:00:00",
    "total_rules": 2,
    "enabled_rules": 2,
    "type_counts": {
      "pronunciation": 1,
      "filter": 1
    }
  }
}
```

### 版本 2.0 的改进

- **简化的ID格式**: 使用纯数字ID (如 "1", "2") 替代复杂的前缀格式
- **元数据支持**: 包含规则统计和更新信息
- **向后兼容**: 自动升级旧格式文件

## 规则类型

### 发音规则 (pronunciation)
用于将英文术语替换为中文发音，提升 TTS 效果。

示例：
- `GitHub` → `吉特哈布`
- `API` → `A P I`
- `JSON` → `J S O N`

### 过滤规则 (filter)
用于过滤敏感词汇和不当内容。

示例：
- `敏感词` → `***`
- `不当内容` → `[已过滤]`

## 正则表达式支持

字典服务支持 Python 正则表达式语法：

```python
# 单词边界匹配
service.add_rule(r"\bAPI\b", "A P I", "pronunciation")

# 大小写不敏感匹配
service.add_rule(r"(?i)github", "吉特哈布", "pronunciation")

# 复杂模式匹配
service.add_rule(r"\d+\.\d+", "[版本号]", "filter")
```

## API 参考

### DictionaryService 类

#### 构造函数
```python
DictionaryService(rules_file: str = "dictionary/rules.json")
```

#### 主要方法

- `process_text(text: str) -> str`: 处理文本，应用所有启用的规则
- `add_rule(pattern: str, replacement: str, rule_type: str, rule_id: Optional[str] = None) -> str`: 添加新规则（自动生成简化ID）
- `remove_rule(rule_id: str) -> bool`: 删除规则
- `update_rule(rule_id: str, **kwargs) -> bool`: 更新规则
- `get_rule(rule_id: str) -> Optional[DictionaryRule]`: 获取指定规则
- `get_all_rules() -> List[DictionaryRule]`: 获取所有规则
- `get_rules_by_type(rule_type: str) -> List[DictionaryRule]`: 按类型获取规则
- `enable_rule(rule_id: str) -> bool`: 启用规则
- `disable_rule(rule_id: str) -> bool`: 禁用规则
- `reload_rules() -> None`: 重新加载规则文件
- `validate_rule(pattern: str) -> bool`: 验证正则表达式
- `import_rules(rules_data: List[Dict], overwrite: bool = False) -> Dict`: 批量导入规则
- `export_rules(rule_type: Optional[str] = None, enabled_only: bool = False) -> List[Dict]`: 导出规则

### DictionaryRule 类

规则数据模型，包含以下字段：

- `id`: 规则唯一标识符
- `type`: 规则类型 ('pronunciation' | 'filter')
- `pattern`: 匹配模式（正则表达式）
- `replacement`: 替换内容
- `enabled`: 是否启用
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 示例脚本

运行示例脚本查看完整功能演示：

```bash
# 基础功能演示
python3 dictionary/example_usage.py

# 优化功能演示（包含批量导入导出、简化ID等）
python3 dictionary/example_optimization.py
```

## 测试

运行单元测试：

```bash
python3 -m unittest tests.test_dictionary_service -v
```

## 注意事项

1. **中文正则表达式**: 对于中文文本，单词边界 `\b` 可能不适用，建议直接使用文本匹配
2. **规则顺序**: 发音规则先于过滤规则执行
3. **性能考虑**: 大量规则可能影响处理性能，建议合理控制规则数量
4. **文件权限**: 确保规则文件具有读写权限
5. **正则表达式安全**: 避免使用可能导致性能问题的复杂正则表达式
6. **ID格式**: 新版本使用简化的数字ID，旧格式会自动升级
7. **批量导入**: 支持JSON和CSV格式，建议使用JSON格式以获得更好的兼容性

## 集成到 TTS 系统

字典服务可以轻松集成到现有的 TTS 系统中：

```python
from dictionary import DictionaryService

# 在 TTS 处理流程中添加文本预处理
dictionary_service = DictionaryService()

def generate_speech(text, voice):
    # 预处理文本
    processed_text = dictionary_service.process_text(text)
    
    # 生成语音
    return tts_engine.generate(processed_text, voice)
```