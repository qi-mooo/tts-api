# 语音管理系统指导

## 语音管理系统概述

项目集成了完整的 edge-tts 语音管理系统，支持 322+ 个语音，包括 14 个中文语音。

## 核心文件和模块

### 主要模块
- `voice_manager.py` - 核心语音管理器，提供所有语音管理功能
- `app_enhanced.py` - 主应用文件，已集成语音 API 端点

### 脚本文件
- `scripts/install_voices.py` - 安装和获取语音列表
- `scripts/update_voices.py` - 详细的语音更新脚本
- `scripts/integrate_voice_manager.py` - 系统集成脚本
- `scripts/deploy_with_voices.sh` - 集成语音更新的部署脚本

### 数据文件
- `data/voices.json` - 完整语音数据（322个语音）
- `data/voices_simplified.json` - 简化的中文语音列表（14个中文语音）
- `data/chinese_voices_map.json` - 中文语音快速映射
- `data/voices_summary.json` - 语音统计摘要

### 测试文件
- `test_voice_manager.py` - 语音管理器功能测试
- `test_voice_api.py` - 语音 API 端点测试

## 语音管理工作流程

### 1. 初始化语音系统
```bash
# 获取最新语音列表
./venv/bin/python3 scripts/install_voices.py

# 集成到系统配置
./venv/bin/python3 scripts/integrate_voice_manager.py

# 测试功能
./venv/bin/python3 test_voice_manager.py
```

### 2. 在代码中使用语音管理器
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
```

### 3. 语音 API 端点使用

#### 获取语音列表
```bash
# 获取所有中文语音
curl "http://localhost:8080/api/voices"

# 获取所有语音
curl "http://localhost:8080/api/voices?chinese_only=false"

# 按性别筛选
curl "http://localhost:8080/api/voices?gender=Female"

# 按地区筛选
curl "http://localhost:8080/api/voices?locale=zh-CN"
```

#### 获取语音统计
```bash
curl "http://localhost:8080/api/voices/stats"
```

#### 验证语音
```bash
curl -X POST "http://localhost:8080/api/voices/validate" \
  -H "Content-Type: application/json" \
  -d '{"voice_name": "zh-CN-YunjianNeural"}'
```

#### 搜索语音
```bash
curl "http://localhost:8080/api/voices/search?q=Female"
```

#### 获取地区列表
```bash
curl "http://localhost:8080/api/voices/locales"
```

## 可用的中文语音

### 中国大陆 (zh-CN) - 6个语音
- **zh-CN-YunjianNeural** (男性) - 默认旁白语音 ⭐
- **zh-CN-XiaoyiNeural** (女性) - 默认对话语音 ⭐
- **zh-CN-XiaoxiaoNeural** (女性)
- **zh-CN-YunxiNeural** (男性)
- **zh-CN-YunxiaNeural** (男性)
- **zh-CN-YunyangNeural** (男性)

### 香港 (zh-HK) - 3个语音
- **zh-HK-HiuGaaiNeural** (女性) - 粤语
- **zh-HK-HiuMaanNeural** (女性)
- **zh-HK-WanLungNeural** (男性)

### 台湾 (zh-TW) - 3个语音
- **zh-TW-HsiaoChenNeural** (女性)
- **zh-TW-YunJheNeural** (男性)
- **zh-TW-HsiaoYuNeural** (女性)

### 方言语音 - 2个语音
- **zh-CN-liaoning-XiaobeiNeural** (女性) - 东北官话
- **zh-CN-shaanxi-XiaoniNeural** (女性) - 陕西官话

## 部署和维护

### 部署时自动更新语音
```bash
# 使用集成部署脚本
./scripts/deploy_with_voices.sh
```

### 手动更新语音列表
```bash
# 更新语音数据
./venv/bin/python3 scripts/update_voices.py

# 重新集成配置
./venv/bin/python3 scripts/integrate_voice_manager.py
```

### 测试语音系统
```bash
# 测试语音管理器
./venv/bin/python3 test_voice_manager.py

# 测试 API 端点
./venv/bin/python3 test_voice_api.py

# 测试特定端点
./venv/bin/python3 test_voice_api.py --test voices
```

## 配置集成

语音管理器会自动更新 `config.json` 文件：

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

## 故障排除

### 语音列表为空
```bash
# 重新获取语音列表
./venv/bin/python3 scripts/install_voices.py
```

### API 端点返回 404
- 确保使用 `app_enhanced.py` 作为主应用文件
- 检查语音管理器是否正确导入
- 验证路由是否正确注册

### 语音验证失败
- 检查语音数据文件是否存在：`ls -la data/voices*.json`
- 重新运行集成脚本：`./venv/bin/python3 scripts/integrate_voice_manager.py`

### 网络连接问题
如果无法从 Microsoft 获取语音列表：
- 检查网络连接
- 考虑使用代理
- 或使用预先下载的语音数据

## 开发指导

### 添加新的语音功能
1. 在 `voice_manager.py` 中添加新方法
2. 在 `app_enhanced.py` 中添加对应的 API 端点
3. 在测试文件中添加测试用例
4. 更新文档

### 自定义语音选择逻辑
```python
from voice_manager import VoiceManager

vm = VoiceManager()

# 自定义筛选
def get_preferred_voices():
    voices = vm.get_chinese_voices()
    # 优先选择大陆普通话语音
    return [v for v in voices if v['Locale'] == 'zh-CN']
```

### 扩展 API 端点
在 `app_enhanced.py` 中添加新的路由：

```python
@app.route('/api/voices/custom', methods=['GET'])
def custom_voice_endpoint():
    # 自定义逻辑
    pass
```

## 最佳实践

1. **始终使用语音管理器**：不要直接调用 edge-tts，使用 `voice_manager` 模块
2. **验证语音名称**：在使用语音前先验证其有效性
3. **缓存语音数据**：语音列表不经常变化，可以缓存使用
4. **错误处理**：妥善处理网络错误和语音不可用的情况
5. **日志记录**：记录语音使用情况和错误信息
6. **定期更新**：定期更新语音列表以获取最新的语音选项

## 性能优化

1. **懒加载**：语音数据在首次使用时才加载
2. **内存缓存**：避免重复读取文件
3. **批量操作**：批量验证多个语音而不是逐个验证
4. **异步处理**：对于大量语音操作考虑使用异步处理

## 监控和指标

- 语音使用频率统计
- API 端点响应时间
- 语音验证成功率
- 缓存命中率
- 错误率和类型分析