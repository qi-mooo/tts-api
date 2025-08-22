# 语音管理指南

TTS API 集成了完整的 Microsoft Edge-TTS 语音管理系统，支持 322+ 个语音，包括 14 个中文语音。本指南将详细介绍如何使用语音管理功能。

## 概述

语音管理系统提供以下功能：

- 🎤 **语音列表管理**: 自动获取和更新 Edge-TTS 语音列表
- 🔍 **语音搜索**: 根据名称、性别、地区搜索语音
- ✅ **语音验证**: 验证语音名称是否有效
- 📊 **统计信息**: 提供详细的语音统计数据
- 🌍 **地区管理**: 按地区组织和筛选语音
- ⚙️ **配置集成**: 与系统配置无缝集成

## 支持的语音

### 中文语音（14个）

#### 中国大陆 (zh-CN) - 6个语音

| 语音名称 | 性别 | 描述 | 推荐用途 |
|---------|------|------|----------|
| **zh-CN-YunjianNeural** | 男性 | 标准普通话，声音沉稳 | 默认旁白语音 ⭐ |
| **zh-CN-XiaoyiNeural** | 女性 | 标准普通话，声音清晰 | 默认对话语音 ⭐ |
| zh-CN-XiaoxiaoNeural | 女性 | 标准普通话，声音甜美 | 女性角色对话 |
| zh-CN-YunxiNeural | 男性 | 标准普通话，声音年轻 | 年轻男性角色 |
| zh-CN-YunxiaNeural | 男性 | 标准普通话，声音温和 | 温和男性角色 |
| zh-CN-YunyangNeural | 男性 | 标准普通话，声音成熟 | 成熟男性角色 |

#### 香港 (zh-HK) - 3个语音

| 语音名称 | 性别 | 描述 | 推荐用途 |
|---------|------|------|----------|
| zh-HK-HiuGaaiNeural | 女性 | 粤语传统发音 | 粤语内容 |
| zh-HK-HiuMaanNeural | 女性 | 香港普通话 | 港式普通话 |
| zh-HK-WanLungNeural | 男性 | 香港普通话 | 港式男性角色 |

#### 台湾 (zh-TW) - 3个语音

| 语音名称 | 性别 | 描述 | 推荐用途 |
|---------|------|------|----------|
| zh-TW-HsiaoChenNeural | 女性 | 台湾国语 | 台湾女性角色 |
| zh-TW-YunJheNeural | 男性 | 台湾国语 | 台湾男性角色 |
| zh-TW-HsiaoYuNeural | 女性 | 台湾官话 | 正式台湾内容 |

#### 方言语音 - 2个语音

| 语音名称 | 性别 | 描述 | 推荐用途 |
|---------|------|------|----------|
| zh-CN-liaoning-XiaobeiNeural | 女性 | 东北官话 | 东北方言内容 |
| zh-CN-shaanxi-XiaoniNeural | 女性 | 陕西官话 | 西北方言内容 |

### 全球语音支持

除了中文语音，系统还支持：

- **总语音数**: 322+ 个
- **支持地区**: 142 个
- **语言覆盖**: 包括英语、日语、韩语、法语、德语、西班牙语等主要语言

## 语音管理 API

### 1. 获取语音列表

```bash
# 获取所有中文语音
curl "http://localhost:8080/api/voices"

# 获取所有语音
curl "http://localhost:8080/api/voices?chinese_only=false"

# 按性别筛选
curl "http://localhost:8080/api/voices?gender=Female"

# 按地区筛选
curl "http://localhost:8080/api/voices?locale=zh-CN"

# 组合筛选
curl "http://localhost:8080/api/voices?locale=zh-CN&gender=Male"
```

### 2. 语音搜索

```bash
# 搜索特定语音
curl "http://localhost:8080/api/voices/search?q=Yunjian"

# 搜索女性语音
curl "http://localhost:8080/api/voices/search?q=Female"

# 搜索台湾语音
curl "http://localhost:8080/api/voices/search?q=Taiwan"

# 搜索粤语语音
curl "http://localhost:8080/api/voices/search?q=Cantonese"
```

### 3. 语音验证

```bash
# 验证语音是否有效
curl -X POST "http://localhost:8080/api/voices/validate" \
  -H "Content-Type: application/json" \
  -d '{"voice_name": "zh-CN-YunjianNeural"}'
```

### 4. 获取统计信息

```bash
# 获取语音统计
curl "http://localhost:8080/api/voices/stats"

# 获取地区列表
curl "http://localhost:8080/api/voices/locales"
```

## 在 TTS API 中使用语音

### 基础用法

```bash
# 使用默认语音
curl "http://localhost:8080/api?text=你好世界"

# 指定旁白语音
curl "http://localhost:8080/api?text=你好世界&narr=zh-CN-YunjianNeural"

# 指定对话语音
curl "http://localhost:8080/api?text=你好世界&dlg=zh-CN-XiaoyiNeural"

# 统一使用一个语音
curl "http://localhost:8080/api?text=你好世界&all=zh-CN-XiaoxiaoNeural"
```

### 高级用法

```bash
# 混合使用不同地区的语音
curl "http://localhost:8080/api?text=大家好，我是小明。&narr=zh-CN-YunjianNeural&dlg=zh-TW-YunJheNeural"

# 使用方言语音
curl "http://localhost:8080/api?text=你好，我来自东北。&all=zh-CN-liaoning-XiaobeiNeural"

# 粤语内容
curl "http://localhost:8080/api?text=你好，欢迎来到香港。&all=zh-HK-HiuGaaiNeural"
```

## 语音管理系统架构

### 核心组件

1. **VoiceManager**: 核心语音管理器
   - 语音数据加载和缓存
   - 语音验证和搜索
   - 统计信息生成

2. **数据文件**:
   - `data/voices.json`: 完整语音数据
   - `data/voices_simplified.json`: 简化的中文语音列表
   - `data/chinese_voices_map.json`: 中文语音快速映射

3. **API 端点**: 集成在主应用中的 RESTful API

### 数据流程

```
Edge-TTS API → 语音数据获取 → 本地存储 → VoiceManager → API 端点 → 客户端
```

## 语音管理脚本

### 安装语音列表

```bash
# 获取最新语音列表
./venv/bin/python3 scripts/install_voices.py

# 更新语音列表（详细版）
./venv/bin/python3 scripts/update_voices.py
```

### 集成到系统

```bash
# 集成语音管理器到配置
./venv/bin/python3 scripts/integrate_voice_manager.py
```

### 测试语音系统

```bash
# 测试语音管理器
./venv/bin/python3 test_voice_manager.py

# 测试语音 API
./venv/bin/python3 test_voice_api.py
```

## 配置管理

### 默认语音配置

语音管理器会自动更新 `config.json` 文件：

```json
{
  "tts": {
    "default_narrator_voice": "zh-CN-YunjianNeural",
    "default_dialogue_voice": "zh-CN-XiaoyiNeural",
    "available_voices": [
      {
        "name": "zh-CN-YunjianNeural",
        "display_name": "Microsoft Yunjian Online (Natural) - Chinese (Mainland)",
        "gender": "Male",
        "locale": "zh-CN"
      }
    ],
    "voice_stats": {
      "total_voices": 322,
      "chinese_voices": 14
    }
  }
}
```

### 在代码中使用

```python
from voice_manager import VoiceManager, get_default_narrator_voice

# 获取语音管理器实例
vm = VoiceManager()

# 获取默认语音
narrator = get_default_narrator_voice()  # zh-CN-YunjianNeural
dialogue = get_default_dialogue_voice()  # zh-CN-XiaoyiNeural

# 验证语音
is_valid = vm.validate_voice("zh-CN-YunjianNeural")

# 获取中文语音列表
chinese_voices = vm.get_chinese_voices()

# 搜索语音
female_voices = vm.search_voices("Female", chinese_only=True)
```

## 性能优化

### 缓存策略

1. **内存缓存**: 语音数据在首次加载后缓存在内存中
2. **懒加载**: 只在需要时加载语音数据
3. **数据压缩**: 使用简化的数据结构减少内存占用

### 响应时间优化

- **语音列表**: < 5ms
- **语音验证**: < 2ms
- **语音搜索**: < 10ms
- **统计信息**: < 3ms

## 故障排除

### 常见问题

#### 1. 语音列表为空

**症状**: API 返回空的语音列表

**解决方案**:
```bash
# 重新获取语音列表
./venv/bin/python3 scripts/install_voices.py

# 检查数据文件
ls -la data/voices*.json
```

#### 2. 语音验证失败

**症状**: 有效的语音名称验证失败

**解决方案**:
```bash
# 检查语音数据完整性
./venv/bin/python3 -c "
from voice_manager import VoiceManager
vm = VoiceManager()
print(f'语音数量: {len(vm.get_all_voices())}')
"

# 重新集成配置
./venv/bin/python3 scripts/integrate_voice_manager.py
```

#### 3. 网络连接问题

**症状**: 无法从 Microsoft 获取语音列表

**解决方案**:
```bash
# 检查网络连接
curl -I https://speech.platform.bing.com

# 使用代理（如果需要）
export https_proxy=http://proxy.example.com:8080
./venv/bin/python3 scripts/install_voices.py
```

#### 4. API 端点返回 404

**症状**: 语音管理 API 端点不可用

**解决方案**:
- 确保使用 `app_enhanced.py` 作为主应用文件
- 检查语音管理器是否正确导入
- 验证路由是否正确注册

### 调试技巧

#### 1. 检查语音数据

```bash
# 查看语音文件
ls -la data/
cat data/voices_summary.json

# 测试语音管理器
./venv/bin/python3 -c "
from voice_manager import voice_manager
stats = voice_manager.get_voice_stats()
print(f'统计信息: {stats}')
"
```

#### 2. 验证 API 集成

```bash
# 检查根端点是否包含语音信息
curl "http://localhost:8080/" | grep -i voice

# 测试语音端点
curl "http://localhost:8080/api/voices/stats"
```

#### 3. 日志分析

```bash
# 查看语音相关日志
tail -f logs/app.log | grep -i voice

# 搜索错误信息
grep -i "voice\|error" logs/app.log
```

## 最佳实践

### 1. 语音选择建议

- **旁白内容**: 使用 `zh-CN-YunjianNeural`（男性，沉稳）
- **对话内容**: 使用 `zh-CN-XiaoyiNeural`（女性，清晰）
- **正式内容**: 使用标准普通话语音
- **地方内容**: 使用对应地区的语音

### 2. 性能优化

```python
# 批量验证语音
voices_to_check = ["zh-CN-YunjianNeural", "zh-CN-XiaoyiNeural"]
vm = VoiceManager()
results = {voice: vm.validate_voice(voice) for voice in voices_to_check}
```

### 3. 错误处理

```python
from voice_manager import VoiceManager

def safe_get_voice_info(voice_name):
    try:
        vm = VoiceManager()
        if vm.validate_voice(voice_name):
            return vm.get_voice_by_name(voice_name)
        else:
            # 使用默认语音
            return vm.get_voice_by_name("zh-CN-YunjianNeural")
    except Exception as e:
        print(f"获取语音信息失败: {e}")
        return None
```

### 4. 定期更新

```bash
# 设置定时任务更新语音列表（每周）
# 添加到 crontab
0 2 * * 0 cd /path/to/tts-api && ./venv/bin/python3 scripts/update_voices.py
```

## 扩展开发

### 添加新的语音功能

1. **在 `voice_manager.py` 中添加新方法**:

```python
def get_voices_by_quality(self, quality: str) -> List[Dict[str, Any]]:
    """根据音质获取语音列表"""
    # 实现逻辑
    pass
```

2. **在 `app_enhanced.py` 中添加对应的 API 端点**:

```python
@app.route('/api/voices/quality/<quality>', methods=['GET'])
def get_voices_by_quality(quality):
    # API 实现
    pass
```

3. **添加测试用例**:

```python
def test_get_voices_by_quality(self):
    # 测试实现
    pass
```

### 自定义语音筛选

```python
from voice_manager import VoiceManager

def get_recommended_voices():
    """获取推荐的语音列表"""
    vm = VoiceManager()
    voices = vm.get_chinese_voices()
    
    # 自定义筛选逻辑
    recommended = []
    for voice in voices:
        if voice['Locale'] == 'zh-CN' and voice['Status'] == 'GA':
            recommended.append(voice)
    
    return recommended
```

## 更新日志

### v2.1.0
- 新增语音管理系统
- 支持 322+ 个语音
- 添加语音搜索和验证功能
- 集成语音统计和地区管理

### v2.0.0
- 初始语音管理功能
- 支持基础语音列表获取
- 集成默认语音配置

---

如需更多帮助，请查看 [API 参考文档](api-reference.md) 或 [提交 Issue](https://github.com/qi-mooo/tts-api/issues)。