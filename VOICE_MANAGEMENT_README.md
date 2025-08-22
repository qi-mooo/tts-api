# 语音管理系统使用指南

本项目集成了完整的 edge-tts 语音管理系统，支持自动获取、存储和管理语音列表。

## 功能特性

- 🎤 自动获取 edge-tts 所有可用语音（322+ 个语音）
- 🇨🇳 专门优化中文语音支持（14 个中文语音）
- 📊 语音统计和分类管理
- 🔍 语音搜索和验证功能
- ⚙️ 与配置系统无缝集成
- 🚀 部署时自动更新语音列表

## 快速开始

### 1. 安装语音列表

```bash
# 获取最新的语音列表
./venv/bin/python3 scripts/install_voices.py

# 或使用 Makefile
make -f Makefile.voices install-voices
```

### 2. 测试语音管理器

```bash
# 运行完整测试
./venv/bin/python3 test_voice_manager.py

# 或使用 Makefile
make -f Makefile.voices test-voices
```

### 3. 在代码中使用

```python
from voice_manager import VoiceManager, get_default_narrator_voice

# 获取语音管理器实例
vm = VoiceManager()

# 获取默认语音
narrator_voice = get_default_narrator_voice()  # zh-CN-YunjianNeural
dialogue_voice = get_default_dialogue_voice()  # zh-CN-XiaoyiNeural

# 获取所有中文语音
chinese_voices = vm.get_chinese_voices()

# 验证语音是否有效
is_valid = vm.validate_voice("zh-CN-YunjianNeural")

# 搜索语音
results = vm.search_voices("Female", chinese_only=True)
```

## 文件结构

```
├── scripts/
│   ├── install_voices.py          # 安装语音列表
│   ├── update_voices.py           # 更新语音列表（详细版）
│   ├── integrate_voice_manager.py # 集成语音管理器
│   └── deploy_with_voices.sh      # 部署脚本（包含语音更新）
├── data/
│   ├── voices.json                # 完整语音数据
│   ├── voices_simplified.json     # 简化的中文语音列表
│   ├── chinese_voices_map.json    # 中文语音映射
│   └── voices_summary.json        # 语音统计摘要
├── voice_manager.py               # 语音管理器主模块
├── voice_api_endpoints.py         # API 端点示例
├── test_voice_manager.py          # 测试脚本
└── Makefile.voices               # 语音管理 Makefile 目标
```

## 可用的中文语音

### 中国大陆 (zh-CN) - 6 个语音
- **zh-CN-XiaoxiaoNeural** (女性) - Microsoft Xiaoxiao
- **zh-CN-XiaoyiNeural** (女性) - Microsoft Xiaoyi ⭐ 默认对话语音
- **zh-CN-YunjianNeural** (男性) - Microsoft Yunjian ⭐ 默认旁白语音
- **zh-CN-YunxiNeural** (男性) - Microsoft Yunxi
- **zh-CN-YunxiaNeural** (男性) - Microsoft Yunxia
- **zh-CN-YunyangNeural** (男性) - Microsoft Yunyang

### 香港 (zh-HK) - 3 个语音
- **zh-HK-HiuGaaiNeural** (女性) - 粤语传统
- **zh-HK-HiuMaanNeural** (女性) - 香港特别行政区
- **zh-HK-WanLungNeural** (男性) - 香港特别行政区

### 台湾 (zh-TW) - 3 个语音
- **zh-TW-HsiaoChenNeural** (女性) - 台湾
- **zh-TW-YunJheNeural** (男性) - 台湾
- **zh-TW-HsiaoYuNeural** (女性) - 台湾官话

### 方言语音 - 2 个语音
- **zh-CN-liaoning-XiaobeiNeural** (女性) - 东北官话
- **zh-CN-shaanxi-XiaoniNeural** (女性) - 中原官话陕西

## API 端点

项目提供了以下语音相关的 API 端点（参考 `voice_api_endpoints.py`）：

### GET /api/voices
获取可用语音列表

**参数:**
- `chinese_only` (boolean): 只返回中文语音，默认 true
- `locale` (string): 按地区筛选，如 "zh-CN"
- `gender` (string): 按性别筛选，"Male" 或 "Female"

**示例:**
```bash
curl "http://localhost:8080/api/voices?chinese_only=true&gender=Female"
```

### GET /api/voices/stats
获取语音统计信息

**示例:**
```bash
curl "http://localhost:8080/api/voices/stats"
```

### POST /api/voices/validate
验证语音名称是否有效

**请求体:**
```json
{
  "voice_name": "zh-CN-YunjianNeural"
}
```

## 配置集成

语音管理器会自动更新 `config.json` 文件，添加以下配置：

```json
{
  "tts": {
    "default_narrator_voice": "zh-CN-YunjianNeural",
    "default_dialogue_voice": "zh-CN-XiaoyiNeural",
    "available_voices": [...],
    "voice_stats": {...}
  }
}
```

## 部署集成

### 自动部署
使用集成的部署脚本：

```bash
./scripts/deploy_with_voices.sh
```

这个脚本会：
1. 检查虚拟环境
2. 安装依赖
3. 获取最新语音列表
4. 集成语音管理器
5. 运行测试验证

### Docker 部署
在 Dockerfile 中添加语音列表获取步骤：

```dockerfile
# 获取语音列表
RUN python3 scripts/install_voices.py

# 集成语音管理器
RUN python3 scripts/integrate_voice_manager.py
```

## 常用命令

### Makefile 命令
```bash
# 安装语音列表
make -f Makefile.voices install-voices

# 更新语音列表
make -f Makefile.voices update-voices

# 测试语音管理器
make -f Makefile.voices test-voices

# 集成语音管理器
make -f Makefile.voices integrate-voices

# 显示语音统计
make -f Makefile.voices voices-stats
```

### 直接 Python 命令
```bash
# 获取语音统计
./venv/bin/python3 -c "from voice_manager import voice_manager; print(voice_manager.get_voice_stats())"

# 列出所有中文语音
./venv/bin/python3 -c "from voice_manager import voice_manager; [print(v['ShortName']) for v in voice_manager.get_chinese_voices()]"

# 验证特定语音
./venv/bin/python3 -c "from voice_manager import voice_manager; print(voice_manager.validate_voice('zh-CN-YunjianNeural'))"
```

## 故障排除

### 1. 语音列表为空
```bash
# 重新获取语音列表
./venv/bin/python3 scripts/install_voices.py
```

### 2. 网络连接问题
如果无法连接到 Microsoft 服务器获取语音列表，可以：
- 检查网络连接
- 使用代理设置
- 或使用预先下载的语音列表文件

### 3. 配置文件问题
```bash
# 重新集成配置
./venv/bin/python3 scripts/integrate_voice_manager.py
```

### 4. 测试失败
```bash
# 运行详细测试
./venv/bin/python3 test_voice_manager.py

# 检查数据文件
ls -la data/
```

## 开发指南

### 添加新的语音功能
1. 在 `voice_manager.py` 中添加新方法
2. 在 `test_voice_manager.py` 中添加测试
3. 更新 API 端点（如需要）
4. 运行测试确保功能正常

### 自定义语音选择逻辑
```python
from voice_manager import VoiceManager

vm = VoiceManager()

# 自定义筛选逻辑
def get_preferred_voices():
    voices = vm.get_chinese_voices()
    # 优先选择大陆普通话语音
    mainland_voices = [v for v in voices if v['Locale'] == 'zh-CN']
    return mainland_voices

# 使用自定义逻辑
preferred = get_preferred_voices()
```

## 更新日志

- **v1.0.0**: 初始版本，支持基本语音管理功能
- **v1.1.0**: 添加搜索和验证功能
- **v1.2.0**: 集成配置系统和 API 端点
- **v1.3.0**: 添加部署脚本和 Makefile 支持

## 许可证

本语音管理系统遵循项目的整体许可证。edge-tts 语音数据来自 Microsoft，请遵守相关使用条款。