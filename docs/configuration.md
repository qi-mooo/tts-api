# 配置说明

本文档详细介绍 TTS API 系统的配置选项和最佳实践。

## 配置文件结构

TTS API 使用 JSON 格式的配置文件 `config.json`，主要包含以下几个部分：

```json
{
  "system": { ... },      // 系统配置
  "tts": { ... },         // TTS 服务配置
  "admin": { ... },       // 管理员配置
  "logging": { ... }      // 日志配置
}
```

## 系统配置 (system)

### 基础设置

```json
{
  "system": {
    "host": "0.0.0.0",           // 监听地址
    "port": 8080,                // 监听端口
    "debug": false,              // 调试模式
    "max_workers": 10            // 最大工作线程数
  }
}
```

#### 配置说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `host` | string | "0.0.0.0" | 服务监听地址，0.0.0.0 表示监听所有接口 |
| `port` | integer | 8080 | 服务监听端口 |
| `debug` | boolean | false | 是否启用调试模式 |
| `max_workers` | integer | 10 | 最大并发工作线程数 |

#### 环境变量覆盖

```bash
export TTS_HOST=127.0.0.1
export TTS_PORT=9000
export TTS_DEBUG=true
export TTS_MAX_WORKERS=20
```

## TTS 服务配置 (tts)

### 语音设置

```json
{
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.3,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200,
    "default_narrator_voice": "zh-CN-YunjianNeural",
    "default_dialogue_voice": "zh-CN-XiaoyiNeural"
  }
}
```

#### 配置说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `narration_voice` | string | "zh-CN-YunjianNeural" | 默认旁白语音 |
| `dialogue_voice` | string | "zh-CN-XiaoyiNeural" | 默认对话语音 |
| `default_speed` | float | 1.3 | 默认语速倍率 (0.5-2.0) |
| `cache_size_limit` | integer | 10485760 | 缓存大小限制（字节） |
| `cache_time_limit` | integer | 1200 | 缓存时间限制（秒） |

#### 推荐语音配置

```json
{
  "tts": {
    // 标准配置（推荐）
    "narration_voice": "zh-CN-YunjianNeural",    // 男性，沉稳
    "dialogue_voice": "zh-CN-XiaoyiNeural",     // 女性，清晰
    
    // 全女性配置
    "narration_voice": "zh-CN-XiaoxiaoNeural",  // 女性，甜美
    "dialogue_voice": "zh-CN-XiaoyiNeural",     // 女性，清晰
    
    // 台湾配置
    "narration_voice": "zh-TW-YunJheNeural",    // 台湾男性
    "dialogue_voice": "zh-TW-HsiaoChenNeural",  // 台湾女性
    
    // 香港配置
    "narration_voice": "zh-HK-WanLungNeural",   // 香港男性
    "dialogue_voice": "zh-HK-HiuMaanNeural"     // 香港女性
  }
}
```

#### 环境变量覆盖

```bash
export TTS_NARRATION_VOICE=zh-CN-YunjianNeural
export TTS_DIALOGUE_VOICE=zh-CN-XiaoyiNeural
export TTS_DEFAULT_SPEED=1.5
export TTS_CACHE_SIZE_LIMIT=20971520
export TTS_CACHE_TIME_LIMIT=1800
```

## 管理员配置 (admin)

### 认证设置

```json
{
  "admin": {
    "username": "admin",
    "password_hash": "$2b$12$...",
    "session_timeout": 3600,
    "secret_key": "your-secret-key"
  }
}
```

#### 配置说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `username` | string | "admin" | 管理员用户名 |
| `password_hash` | string | - | 密码哈希值（bcrypt） |
| `session_timeout` | integer | 3600 | 会话超时时间（秒） |
| `secret_key` | string | - | 会话加密密钥 |

#### 密码设置

```bash
# 方法1：使用 Python 生成密码哈希
./venv/bin/python3 -c "
import bcrypt
password = 'your-secure-password'
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f'Password hash: {hash.decode()}')
"

# 方法2：使用设置脚本
./venv/bin/python3 setup.py --password your-secure-password

# 方法3：环境变量
export TTS_ADMIN_PASSWORD=your-secure-password
```

#### 安全建议

1. **强密码**: 使用至少12位包含大小写字母、数字和特殊字符的密码
2. **定期更换**: 建议每3-6个月更换一次密码
3. **密钥管理**: `secret_key` 应该是随机生成的长字符串
4. **会话超时**: 根据安全需求调整会话超时时间

## 日志配置 (logging)

### 日志设置

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size": 10485760,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

#### 配置说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `level` | string | "INFO" | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `file` | string | "logs/app.log" | 日志文件路径 |
| `max_size` | integer | 10485760 | 单个日志文件最大大小（字节） |
| `backup_count` | integer | 5 | 保留的日志文件数量 |
| `format` | string | - | 日志格式字符串 |

#### 日志级别说明

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（推荐）
- **WARNING**: 警告信息
- **ERROR**: 错误信息

#### 环境变量覆盖

```bash
export TTS_LOG_LEVEL=DEBUG
export TTS_LOG_FILE=logs/debug.log
```

## 高级配置

### 性能调优

#### 内存优化配置

```json
{
  "system": {
    "max_workers": 4
  },
  "tts": {
    "cache_size_limit": 52428800,    // 50MB
    "cache_time_limit": 3600         // 1小时
  }
}
```

#### 高并发配置

```json
{
  "system": {
    "max_workers": 20
  },
  "tts": {
    "cache_size_limit": 104857600,   // 100MB
    "cache_time_limit": 7200         // 2小时
  }
}
```

#### 低资源配置

```json
{
  "system": {
    "max_workers": 2
  },
  "tts": {
    "cache_size_limit": 5242880,     // 5MB
    "cache_time_limit": 600          // 10分钟
  }
}
```

### 网络配置

#### 代理设置

```bash
# HTTP 代理
export http_proxy=http://proxy.example.com:8080
export https_proxy=http://proxy.example.com:8080

# SOCKS 代理
export http_proxy=socks5://proxy.example.com:1080
export https_proxy=socks5://proxy.example.com:1080

# 不使用代理的地址
export no_proxy=localhost,127.0.0.1,*.local
```

#### 超时设置

```json
{
  "tts": {
    "request_timeout": 30,           // 请求超时（秒）
    "connection_timeout": 10         // 连接超时（秒）
  }
}
```

## 环境特定配置

### 开发环境

```json
{
  "system": {
    "debug": true,
    "max_workers": 2
  },
  "logging": {
    "level": "DEBUG"
  },
  "tts": {
    "cache_size_limit": 5242880
  }
}
```

### 测试环境

```json
{
  "system": {
    "debug": false,
    "max_workers": 4
  },
  "logging": {
    "level": "INFO"
  },
  "tts": {
    "cache_size_limit": 10485760
  }
}
```

### 生产环境

```json
{
  "system": {
    "debug": false,
    "max_workers": 10
  },
  "logging": {
    "level": "WARNING",
    "backup_count": 10
  },
  "tts": {
    "cache_size_limit": 52428800,
    "cache_time_limit": 3600
  }
}
```

## 配置验证

### 验证配置文件

```bash
# 验证 JSON 语法
./venv/bin/python3 -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
print('配置文件语法正确')
"

# 验证配置完整性
./venv/bin/python3 -c "
from config.config_manager import config_manager
print('配置加载成功')
print(f'TTS 配置: {config_manager.tts.__dict__}')
"
```

### 测试配置

```bash
# 测试语音配置
./venv/bin/python3 -c "
from voice_manager import voice_manager
from config.config_manager import config_manager

narr_voice = config_manager.tts.narration_voice
dlg_voice = config_manager.tts.dialogue_voice

print(f'旁白语音: {narr_voice} - 有效: {voice_manager.validate_voice(narr_voice)}')
print(f'对话语音: {dlg_voice} - 有效: {voice_manager.validate_voice(dlg_voice)}')
"

# 测试管理员配置
curl -X POST "http://localhost:8080/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

## 配置模板

### 基础模板

```json
{
  "system": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "max_workers": 10
  },
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.3,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200
  },
  "admin": {
    "username": "admin",
    "password_hash": "$2b$12$REPLACE_WITH_ACTUAL_HASH",
    "session_timeout": 3600,
    "secret_key": "REPLACE_WITH_RANDOM_SECRET_KEY"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
```

### Docker 模板

```json
{
  "system": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "max_workers": 8
  },
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.3,
    "cache_size_limit": 20971520,
    "cache_time_limit": 1800
  },
  "admin": {
    "username": "admin",
    "password_hash": "$2b$12$REPLACE_WITH_ACTUAL_HASH",
    "session_timeout": 7200,
    "secret_key": "REPLACE_WITH_RANDOM_SECRET_KEY"
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/app.log",
    "max_size": 20971520,
    "backup_count": 3
  }
}
```

## 故障排除

### 常见配置问题

#### 1. JSON 语法错误

```bash
# 错误信息：JSONDecodeError
# 解决方案：验证 JSON 语法
python3 -m json.tool config.json
```

#### 2. 语音配置无效

```bash
# 错误信息：语音验证失败
# 解决方案：检查语音名称
./venv/bin/python3 -c "
from voice_manager import voice_manager
print('可用的中文语音:')
for voice in voice_manager.get_chinese_voices():
    print(f'  {voice[\"ShortName\"]} ({voice[\"Gender\"]}, {voice[\"Locale\"]})')
"
```

#### 3. 端口占用

```bash
# 错误信息：Address already in use
# 解决方案：更改端口或杀死占用进程
lsof -i :8080
kill -9 $(lsof -t -i:8080)
```

#### 4. 权限问题

```bash
# 错误信息：Permission denied
# 解决方案：修复文件权限
chmod 644 config.json
chmod 755 logs/
```

### 配置重载

```bash
# 重启服务以应用新配置
sudo systemctl restart tts-api

# Docker 环境
docker-compose restart

# 开发环境
# 停止服务 (Ctrl+C) 然后重新启动
./venv/bin/python3 app_enhanced.py
```

## 最佳实践

### 1. 安全配置

- 使用强密码和随机密钥
- 定期更换密码
- 限制管理员会话超时时间
- 在生产环境中禁用调试模式

### 2. 性能配置

- 根据服务器资源调整 `max_workers`
- 合理设置缓存大小和时间
- 监控内存和 CPU 使用情况

### 3. 日志配置

- 生产环境使用 WARNING 级别
- 设置合适的日志轮转策略
- 定期清理旧日志文件

### 4. 备份配置

```bash
# 定期备份配置文件
cp config.json config.json.$(date +%Y%m%d)

# 版本控制（排除敏感信息）
git add config.json.template
```

---

更多配置选项请参考 [API 文档](api-reference.md) 和 [部署指南](deployment.md)。