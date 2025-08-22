# 配置管理系统

本模块提供了完整的配置管理功能，支持配置文件、环境变量和热重载。

## 功能特性

- 🔧 **集中配置管理**: 统一管理所有应用配置
- 🌍 **环境变量支持**: 支持通过环境变量覆盖配置
- 🔄 **热重载**: 支持运行时重新加载配置
- ✅ **配置验证**: 自动验证配置的有效性
- 🔒 **线程安全**: 支持多线程环境
- 👀 **变更监听**: 支持配置变更事件监听

## 配置结构

配置分为以下几个部分：

### TTS配置 (`tts`)
- `narration_voice`: 旁白语音名称
- `dialogue_voice`: 对话语音名称  
- `default_speed`: 默认语速
- `cache_size_limit`: 缓存大小限制（字节）
- `cache_time_limit`: 缓存时间限制（秒）

### 日志配置 (`logging`)
- `level`: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `file`: 日志文件路径
- `max_size`: 日志文件最大大小
- `backup_count`: 日志文件备份数量
- `format`: 日志格式

### 管理员配置 (`admin`)
- `username`: 管理员用户名
- `password_hash`: 密码哈希
- `session_timeout`: 会话超时时间（秒）
- `secret_key`: Flask会话密钥

### 字典配置 (`dictionary`)
- `enabled`: 是否启用字典功能
- `rules_file`: 字典规则文件路径

### 系统配置 (`system`)
- `debug`: 是否启用调试模式
- `host`: 服务器主机地址
- `port`: 服务器端口
- `max_workers`: 最大工作线程数

## 使用方法

### 基本使用

```python
from config import ConfigManager

# 创建配置管理器实例
config = ConfigManager("config.json")

# 获取配置值
voice = config.tts.narration_voice
speed = config.get("tts.default_speed")

# 设置配置值
config.set("tts.narration_voice", "zh-CN-NewVoice")
config.tts.default_speed = 1.5

# 保存配置
config.save()

# 验证配置
if config.validate():
    print("配置有效")
```

### 环境变量

支持以下环境变量：

```bash
# TTS配置
export TTS_NARRATION_VOICE="zh-CN-YunjianNeural"
export TTS_DIALOGUE_VOICE="zh-CN-XiaoyiNeural"
export TTS_DEFAULT_SPEED="1.2"
export TTS_CACHE_SIZE_LIMIT="10485760"
export TTS_CACHE_TIME_LIMIT="1200"

# 日志配置
export LOG_LEVEL="INFO"
export LOG_FILE="logs/app.log"

# 管理员配置
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD_HASH="..."
export ADMIN_SECRET_KEY="..."

# 系统配置
export SYSTEM_DEBUG="false"
export SYSTEM_HOST="0.0.0.0"
export SYSTEM_PORT="5000"
```

### 配置变更监听

```python
def on_config_change(key, value):
    print(f"配置已变更: {key} = {value}")

# 添加监听器
config.add_watcher(on_config_change)

# 移除监听器
config.remove_watcher(on_config_change)
```

### 热重载

```python
# 重新加载配置文件
config.reload()
```

## 命令行工具

提供了 `config_tool.py` 命令行工具来管理配置：

### 初始化配置

```bash
python3 config/config_tool.py init --admin-password mypassword
```

### 显示配置

```bash
python3 config/config_tool.py show
```

### 设置配置

```bash
python3 config/config_tool.py set tts.narration_voice "zh-CN-NewVoice"
python3 config/config_tool.py set admin.password "newpassword"
```

### 获取配置

```bash
python3 config/config_tool.py get tts.default_speed
```

### 验证配置

```bash
python3 config/config_tool.py validate
```

## 配置文件示例

参考 `config.json.template` 文件：

```json
{
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.2,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "admin": {
    "username": "admin",
    "password_hash": "",
    "session_timeout": 3600,
    "secret_key": ""
  },
  "dictionary": {
    "enabled": true,
    "rules_file": "dictionary/rules.json"
  },
  "system": {
    "debug": false,
    "host": "0.0.0.0",
    "port": 5000,
    "max_workers": 10
  }
}
```

## 最佳实践

1. **使用环境变量**: 在生产环境中使用环境变量来覆盖敏感配置
2. **定期验证**: 在应用启动时验证配置的有效性
3. **监听变更**: 使用配置变更监听器来响应配置更新
4. **备份配置**: 定期备份重要的配置文件
5. **安全存储**: 不要在代码中硬编码敏感信息

## 注意事项

- 配置文件使用UTF-8编码
- 密码会自动进行bcrypt哈希处理
- 配置变更会触发相关组件的更新
- 线程安全，支持并发访问