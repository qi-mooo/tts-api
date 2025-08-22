# TTS API 接口文档

## 概述

本文档详细描述了 TTS API 系统的所有接口端点、参数说明、响应格式和使用示例。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **API版本**: v1
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

管理接口需要基于会话的认证：

```bash
# 登录获取会话
curl -X POST http://localhost:5000/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

## API 端点

### 1. 文本转语音 API

#### GET /api

将文本转换为语音音频文件。

**参数说明**

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `text` | string | 是 | - | 要转换的文本内容 |
| `speed` | float | 否 | 1.2 | 语音速度 (0.5-2.0) |
| `narr` | string | 否 | 配置文件中的值 | 旁白语音 |
| `dlg` | string | 否 | 配置文件中的值 | 对话语音 |
| `all` | string | 否 | - | 统一语音（覆盖 narr 和 dlg） |

**请求示例**

```bash
# 基本用法
GET /api?text=你好世界

# 自定义语速
GET /api?text=你好世界&speed=1.5

# 自定义语音
GET /api?text=你好世界&narr=zh-CN-YunjianNeural&dlg=zh-CN-XiaoyiNeural

# 统一语音
GET /api?text=你好世界&all=zh-CN-YunjianNeural

# 包含对话的文本
GET /api?text=这是旁白："这是对话内容"继续旁白
```

**响应格式**

成功响应（HTTP 200）：
```
Content-Type: audio/mpeg
Content-Length: [音频文件大小]

[二进制音频数据]
```

错误响应：
```json
{
  "success": false,
  "error": {
    "error_code": "VAL_001",
    "message": "参数验证失败",
    "details": {
      "field": "text",
      "reason": "文本参数不能为空"
    }
  },
  "request_id": "req_123456",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**支持的语音列表**

| 语音名称 | 语言 | 性别 | 说明 |
|----------|------|------|------|
| zh-CN-YunjianNeural | 中文 | 男 | 云健 |
| zh-CN-XiaoyiNeural | 中文 | 女 | 晓伊 |
| zh-CN-YunxiNeural | 中文 | 男 | 云希 |
| zh-CN-XiaoxiaoNeural | 中文 | 女 | 晓晓 |
| zh-CN-YunyangNeural | 中文 | 男 | 云扬 |

### 2. 健康检查 API

#### GET /health

获取系统健康状态和运行信息。

**参数说明**

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `detailed` | boolean | 否 | false | 是否返回详细信息 |

**请求示例**

```bash
# 基本健康检查
curl http://localhost:5000/health

# 详细健康信息
curl http://localhost:5000/health?detailed=true
```

**响应格式**

基本响应（HTTP 200）：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": "2 days, 3:45:12",
  "version": "1.0.0"
}
```

详细响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": "2 days, 3:45:12",
  "version": "1.0.0",
  "system": {
    "memory_usage": 45.2,
    "cpu_usage": 12.5,
    "disk_usage": 68.3
  },
  "services": {
    "edge_tts": {
      "status": "available",
      "response_time_ms": 150
    },
    "cache": {
      "status": "active",
      "size": 15,
      "hit_rate": 0.85
    }
  },
  "statistics": {
    "total_requests": 1234,
    "successful_requests": 1200,
    "error_rate": 0.028
  }
}
```

服务不可用响应（HTTP 503）：
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "errors": [
    {
      "service": "edge_tts",
      "error": "连接超时"
    }
  ]
}
```

## 管理 API

### 3. 管理员登录

#### POST /admin/login

管理员登录接口。

**请求体**

```json
{
  "username": "admin",
  "password": "your-password"
}
```

**响应格式**

成功响应（HTTP 200）：
```json
{
  "success": true,
  "message": "登录成功",
  "session_id": "sess_123456",
  "expires_at": "2024-01-01T13:00:00Z"
}
```

失败响应（HTTP 401）：
```json
{
  "success": false,
  "error": {
    "error_code": "AUTH_001",
    "message": "用户名或密码错误"
  }
}
```

### 4. 配置管理

#### GET /admin/config

获取当前系统配置。

**响应格式**

```json
{
  "success": true,
  "data": {
    "tts": {
      "narration_voice": "zh-CN-YunjianNeural",
      "dialogue_voice": "zh-CN-XiaoyiNeural",
      "default_speed": 1.2,
      "cache_size_limit": 10485760,
      "cache_time_limit": 1200
    },
    "logging": {
      "level": "INFO",
      "file": "logs/app.log"
    }
  }
}
```

#### PUT /admin/config

更新系统配置。

**请求体**

```json
{
  "tts": {
    "default_speed": 1.5,
    "cache_size_limit": 20971520
  }
}
```

**响应格式**

```json
{
  "success": true,
  "message": "配置更新成功",
  "updated_fields": ["tts.default_speed", "tts.cache_size_limit"]
}
```

### 5. 字典管理

#### GET /admin/dictionary/rules

获取所有字典规则。

**响应格式**

```json
{
  "success": true,
  "data": {
    "rules": [
      {
        "id": "rule_001",
        "type": "pronunciation",
        "pattern": "GitHub",
        "replacement": "吉特哈布",
        "enabled": true,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

#### POST /admin/dictionary/rules

添加新的字典规则。

**请求体**

```json
{
  "type": "pronunciation",
  "pattern": "API",
  "replacement": "A P I",
  "enabled": true
}
```

**响应格式**

```json
{
  "success": true,
  "message": "规则添加成功",
  "rule_id": "rule_002"
}
```

#### PUT /admin/dictionary/rules/{rule_id}

更新字典规则。

**请求体**

```json
{
  "replacement": "新的替换文本",
  "enabled": false
}
```

**响应格式**

```json
{
  "success": true,
  "message": "规则更新成功"
}
```

#### DELETE /admin/dictionary/rules/{rule_id}

删除字典规则。

**响应格式**

```json
{
  "success": true,
  "message": "规则删除成功"
}
```

### 6. 系统控制

#### POST /admin/restart

优雅重启系统。

**请求体**

```json
{
  "force": false,
  "timeout": 60
}
```

**响应格式**

```json
{
  "success": true,
  "message": "系统重启中...",
  "restart_id": "restart_123456"
}
```

#### GET /admin/logs

获取系统日志。

**参数说明**

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `level` | string | 否 | - | 日志级别过滤 |
| `limit` | integer | 否 | 100 | 返回条数限制 |
| `offset` | integer | 否 | 0 | 偏移量 |

**响应格式**

```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "timestamp": "2024-01-01T12:00:00Z",
        "level": "INFO",
        "module": "tts_service",
        "message": "TTS 请求处理成功",
        "request_id": "req_123456"
      }
    ],
    "total": 1000,
    "has_more": true
  }
}
```

## 错误码说明

### 系统错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| `SYS_001` | 500 | 系统内部错误 |
| `SYS_002` | 503 | 服务不可用 |
| `SYS_003` | 507 | 存储空间不足 |

### 验证错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| `VAL_001` | 400 | 参数验证失败 |
| `VAL_002` | 400 | 参数格式错误 |
| `VAL_003` | 400 | 参数值超出范围 |

### TTS 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| `TTS_001` | 503 | Edge-TTS 服务不可用 |
| `TTS_002` | 500 | 音频生成失败 |
| `TTS_003` | 400 | 不支持的语音 |

### 认证错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| `AUTH_001` | 401 | 认证失败 |
| `AUTH_002` | 403 | 权限不足 |
| `AUTH_003` | 401 | 会话过期 |

## 使用示例

### Python 示例

```python
import requests
import json

# 基本 TTS 请求
def text_to_speech(text, speed=1.2):
    url = "http://localhost:5000/api"
    params = {
        "text": text,
        "speed": speed
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        with open("output.mp3", "wb") as f:
            f.write(response.content)
        return True
    else:
        print(f"错误: {response.json()}")
        return False

# 管理 API 示例
def admin_login(username, password):
    url = "http://localhost:5000/admin/login"
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 添加字典规则
def add_dictionary_rule(pattern, replacement, rule_type="pronunciation"):
    url = "http://localhost:5000/admin/dictionary/rules"
    data = {
        "type": rule_type,
        "pattern": pattern,
        "replacement": replacement,
        "enabled": True
    }
    
    response = requests.post(url, json=data)
    return response.json()
```

### JavaScript 示例

```javascript
// 基本 TTS 请求
async function textToSpeech(text, speed = 1.2) {
    const url = `http://localhost:5000/api?text=${encodeURIComponent(text)}&speed=${speed}`;
    
    try {
        const response = await fetch(url);
        
        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            const audio = new Audio(audioUrl);
            audio.play();
            
            return true;
        } else {
            const error = await response.json();
            console.error('TTS 错误:', error);
            return false;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return false;
    }
}

// 管理 API 示例
async function adminLogin(username, password) {
    const url = 'http://localhost:5000/admin/login';
    const data = {
        username: username,
        password: password
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    } catch (error) {
        console.error('登录失败:', error);
        return { success: false, error: error.message };
    }
}
```

### cURL 示例

```bash
# 基本 TTS 请求
curl -G "http://localhost:5000/api" \
  --data-urlencode "text=你好世界" \
  --data-urlencode "speed=1.5" \
  -o output.mp3

# 健康检查
curl "http://localhost:5000/health?detailed=true" | jq

# 管理员登录
curl -X POST "http://localhost:5000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}' \
  -c cookies.txt

# 获取配置（需要先登录）
curl "http://localhost:5000/admin/config" \
  -b cookies.txt | jq

# 添加字典规则
curl -X POST "http://localhost:5000/admin/dictionary/rules" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "pronunciation",
    "pattern": "GitHub",
    "replacement": "吉特哈布",
    "enabled": true
  }'
```

## 性能和限制

### 请求限制

- 单次请求文本长度：最大 10,000 字符
- 并发请求数：最大 10 个（可配置）
- 请求超时：120 秒

### 缓存机制

- 音频缓存：基于文本内容和语音参数的 MD5 哈希
- 缓存大小：默认 10MB（可配置）
- 缓存时间：默认 20 分钟（可配置）

### 性能优化建议

1. **使用缓存**：相同的文本和参数会返回缓存的音频
2. **合理分段**：长文本建议分段处理
3. **并发控制**：避免过多并发请求
4. **网络优化**：确保到 Edge-TTS 服务的网络连接稳定

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基本 TTS 功能
- 添加 Web 管理控制台
- 实现字典服务
- 完善错误处理和日志系统

---

如有问题或建议，请参考项目文档或提交 Issue。