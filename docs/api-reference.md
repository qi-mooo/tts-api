# API 参考文档

TTS API 提供了完整的文本转语音和语音管理功能。所有 API 端点都返回 JSON 格式的响应。

## 基础信息

- **基础 URL**: `http://localhost:8080`
- **API 版本**: v2.1.0
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

大部分 API 端点无需认证，管理相关的端点需要通过 Web 控制台登录。

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {...},
  "timestamp": 1640995200.123
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": "详细错误信息"
  },
  "timestamp": 1640995200.123,
  "request_id": "req_12345"
}
```

## 文本转语音 API

### 基础 TTS 转换

**端点**: `GET /api`

将文本转换为语音音频文件。

#### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `text` | string | 是 | - | 要转换的文本内容 |
| `speed` | float | 否 | 1.3 | 语速倍率 (0.5-2.0) |
| `narr` | string | 否 | zh-CN-YunjianNeural | 旁白语音 |
| `dlg` | string | 否 | zh-CN-XiaoyiNeural | 对话语音 |
| `all` | string | 否 | - | 统一使用的语音（覆盖 narr 和 dlg） |

#### 请求示例

```bash
# 基本用法
curl "http://localhost:8080/api?text=你好世界"

# 自定义语速
curl "http://localhost:8080/api?text=你好世界&speed=1.5"

# 自定义语音
curl "http://localhost:8080/api?text=你好世界&narr=zh-CN-YunjianNeural&dlg=zh-CN-XiaoyiNeural"

# 统一语音
curl "http://localhost:8080/api?text=你好世界&all=zh-CN-XiaoxiaoNeural"

# 对话文本（包含引号）
curl "http://localhost:8080/api?text=他说：\"你好！\"然后离开了。&speed=1.2"
```

#### 响应

**成功响应** (HTTP 200):
- **Content-Type**: `audio/webm`
- **Body**: 音频文件的二进制数据

**错误响应** (HTTP 400/500):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_VOICE",
    "message": "指定的语音不存在",
    "details": "语音 'invalid-voice' 不在支持的语音列表中"
  }
}
```

### 获取缓存音频

**端点**: `GET /audio`

获取当前缓存的合并音频。

#### 响应

**成功响应** (HTTP 200):
- **Content-Type**: `audio/webm`
- **Headers**: 
  - `X-Cache-Hit: true`
  - `X-Audio-Duration: {duration}`

**无缓存** (HTTP 404):
```json
{
  "success": false,
  "error": "没有可用的缓存音频",
  "cache_stats": {
    "cache_count": 0,
    "total_size": 0
  }
}
```

## 语音管理 API

### 获取语音列表

**端点**: `GET /api/voices`

获取可用的语音列表，支持多种筛选条件。

#### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `chinese_only` | boolean | 否 | true | 只返回中文语音 |
| `locale` | string | 否 | - | 按地区筛选 (如: zh-CN) |
| `gender` | string | 否 | - | 按性别筛选 (Male/Female) |

#### 请求示例

```bash
# 获取所有中文语音（默认）
curl "http://localhost:8080/api/voices"

# 获取所有语音
curl "http://localhost:8080/api/voices?chinese_only=false"

# 获取中文女性语音
curl "http://localhost:8080/api/voices?gender=Female"

# 获取大陆普通话语音
curl "http://localhost:8080/api/voices?locale=zh-CN"

# 组合筛选：大陆男性语音
curl "http://localhost:8080/api/voices?locale=zh-CN&gender=Male"
```

#### 响应

```json
{
  "success": true,
  "voices": [
    {
      "name": "zh-CN-YunjianNeural",
      "display_name": "Microsoft Yunjian Online (Natural) - Chinese (Mainland)",
      "gender": "Male",
      "locale": "zh-CN"
    },
    {
      "name": "zh-CN-XiaoyiNeural",
      "display_name": "Microsoft Xiaoyi Online (Natural) - Chinese (Mainland)",
      "gender": "Female",
      "locale": "zh-CN"
    }
  ],
  "count": 2,
  "filters": {
    "chinese_only": true,
    "locale": "zh-CN",
    "gender": null
  }
}
```

### 获取语音统计

**端点**: `GET /api/voices/stats`

获取语音系统的统计信息。

#### 请求示例

```bash
curl "http://localhost:8080/api/voices/stats"
```

#### 响应

```json
{
  "success": true,
  "stats": {
    "total_voices": 322,
    "chinese_voices": 14,
    "locales": 142,
    "chinese_locales": 5,
    "gender_distribution": {
      "Male": 6,
      "Female": 8,
      "Unknown": 0
    }
  },
  "timestamp": 1640995200.123
}
```

### 验证语音

**端点**: `POST /api/voices/validate`

验证指定的语音名称是否有效。

#### 请求体

```json
{
  "voice_name": "zh-CN-YunjianNeural"
}
```

#### 请求示例

```bash
curl -X POST "http://localhost:8080/api/voices/validate" \
  -H "Content-Type: application/json" \
  -d '{"voice_name": "zh-CN-YunjianNeural"}'
```

#### 响应

**有效语音**:
```json
{
  "success": true,
  "voice_name": "zh-CN-YunjianNeural",
  "valid": true,
  "voice_info": {
    "name": "zh-CN-YunjianNeural",
    "display_name": "Microsoft Yunjian Online (Natural) - Chinese (Mainland)",
    "gender": "Male",
    "locale": "zh-CN",
    "status": "GA"
  }
}
```

**无效语音**:
```json
{
  "success": true,
  "voice_name": "invalid-voice",
  "valid": false,
  "voice_info": null
}
```

### 获取语音地区

**端点**: `GET /api/voices/locales`

获取可用的语音地区列表。

#### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `chinese_only` | boolean | 否 | true | 只返回中文地区 |

#### 请求示例

```bash
# 获取中文地区
curl "http://localhost:8080/api/voices/locales"

# 获取所有地区
curl "http://localhost:8080/api/voices/locales?chinese_only=false"
```

#### 响应

```json
{
  "success": true,
  "locales": [
    {
      "locale": "zh-CN",
      "voice_count": 6,
      "male_count": 4,
      "female_count": 2
    },
    {
      "locale": "zh-HK",
      "voice_count": 3,
      "male_count": 1,
      "female_count": 2
    }
  ],
  "count": 2,
  "chinese_only": true
}
```

### 搜索语音

**端点**: `GET /api/voices/search`

根据关键词搜索语音。

#### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `q` | string | 是 | - | 搜索关键词 |
| `chinese_only` | boolean | 否 | true | 只搜索中文语音 |

#### 请求示例

```bash
# 搜索包含 "Yunjian" 的语音
curl "http://localhost:8080/api/voices/search?q=Yunjian"

# 搜索女性语音
curl "http://localhost:8080/api/voices/search?q=Female"

# 搜索台湾语音
curl "http://localhost:8080/api/voices/search?q=Taiwan"

# 在所有语音中搜索
curl "http://localhost:8080/api/voices/search?q=English&chinese_only=false"
```

#### 响应

```json
{
  "success": true,
  "query": "Female",
  "results": [
    {
      "name": "zh-CN-XiaoyiNeural",
      "display_name": "Microsoft Xiaoyi Online (Natural) - Chinese (Mainland)",
      "gender": "Female",
      "locale": "zh-CN"
    }
  ],
  "count": 1,
  "chinese_only": true
}
```

## 系统 API

### 根端点信息

**端点**: `GET /`

获取 API 服务的基本信息和可用端点。

#### 请求示例

```bash
curl "http://localhost:8080/"
```

#### 响应

```json
{
  "service": "Enhanced TTS API",
  "version": "2.1.0",
  "endpoints": {
    "tts": "/api",
    "cached_audio": "/audio",
    "status": "/api/status",
    "health": "/health",
    "voices": "/api/voices",
    "voice_stats": "/api/voices/stats",
    "voice_validate": "/api/voices/validate",
    "voice_locales": "/api/voices/locales",
    "voice_search": "/api/voices/search",
    "admin": "/admin"
  },
  "features": [
    "Text-to-Speech conversion",
    "Audio caching",
    "Dictionary management",
    "Voice management (322+ voices)",
    "Health monitoring",
    "Admin interface"
  ],
  "voice_stats": {
    "total_voices": "322+",
    "chinese_voices": "14",
    "supported_locales": "5 Chinese regions"
  }
}
```

### 健康检查

**端点**: `GET /health`

检查服务的健康状态。

#### 请求示例

```bash
curl "http://localhost:8080/health"
```

#### 响应

```json
{
  "status": "healthy",
  "timestamp": 1640995200.123,
  "port": 8080
}
```

### API 状态

**端点**: `GET /api/status`

获取详细的 API 状态信息。

#### 请求示例

```bash
curl "http://localhost:8080/api/status"
```

#### 响应

```json
{
  "success": true,
  "service": "Enhanced TTS API",
  "version": "2.0.0",
  "timestamp": 1640995200.123,
  "cache_stats": {
    "cache_count": 15,
    "total_size": 1048576,
    "hit_rate": 0.85
  },
  "config": {
    "max_workers": 10,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200,
    "default_voices": {
      "narration": "zh-CN-YunjianNeural",
      "dialogue": "zh-CN-XiaoyiNeural"
    }
  }
}
```

## 字典管理 API

### 获取字典规则

**端点**: `GET /api/dictionary/rules`

获取所有字典规则。

#### 响应

```json
{
  "success": true,
  "rules": [
    {
      "id": "rule_001",
      "pattern": "AI",
      "replacement": "人工智能",
      "type": "pronunciation",
      "enabled": true
    }
  ],
  "total": 1
}
```

### 添加字典规则

**端点**: `POST /api/dictionary/rules`

添加新的字典规则。

#### 请求体

```json
{
  "pattern": "TTS",
  "replacement": "文本转语音",
  "type": "pronunciation"
}
```

### 测试字典处理

**端点**: `POST /api/dictionary/test`

测试字典规则对文本的处理效果。

#### 请求体

```json
{
  "text": "这是一个 AI 和 TTS 的测试"
}
```

#### 响应

```json
{
  "success": true,
  "original_text": "这是一个 AI 和 TTS 的测试",
  "processed_text": "这是一个 人工智能 和 文本转语音 的测试",
  "changed": true
}
```

## 配置管理 API

### 获取配置

**端点**: `GET /api/config`

获取当前系统配置（敏感信息已隐藏）。

#### 响应

```json
{
  "success": true,
  "config": {
    "tts": {
      "narration_voice": "zh-CN-YunjianNeural",
      "dialogue_voice": "zh-CN-XiaoyiNeural",
      "default_speed": 1.3
    },
    "system": {
      "max_workers": 10,
      "debug": false
    }
  }
}
```

### 更新配置

**端点**: `POST /api/config`

更新系统配置（需要管理员权限）。

#### 请求体

```json
{
  "tts": {
    "default_speed": 1.5
  }
}
```

## 错误代码

| 错误代码 | HTTP 状态码 | 描述 |
|----------|-------------|------|
| `INVALID_VOICE` | 400 | 指定的语音不存在 |
| `INVALID_SPEED` | 400 | 语速参数超出范围 |
| `EMPTY_TEXT` | 400 | 文本内容为空 |
| `TEXT_TOO_LONG` | 400 | 文本内容过长 |
| `MISSING_PARAMETER` | 400 | 缺少必需参数 |
| `TTS_SERVICE_ERROR` | 500 | TTS 服务内部错误 |
| `CACHE_ERROR` | 500 | 缓存系统错误 |
| `NETWORK_ERROR` | 503 | 网络连接错误 |

## 速率限制

目前没有实施速率限制，但建议：

- 单个请求文本长度不超过 1000 字符
- 并发请求数不超过 10 个
- 避免频繁的重复请求

## 最佳实践

### 1. 语音选择

```bash
# 推荐：使用验证过的语音
curl -X POST "/api/voices/validate" -d '{"voice_name": "zh-CN-YunjianNeural"}'
# 然后使用验证通过的语音
curl "/api?text=测试&narr=zh-CN-YunjianNeural"
```

### 2. 错误处理

```javascript
// JavaScript 示例
async function callTTSAPI(text) {
  try {
    const response = await fetch(`/api?text=${encodeURIComponent(text)}`);
    if (!response.ok) {
      const error = await response.json();
      console.error('TTS API Error:', error.error.message);
      return null;
    }
    return await response.blob();
  } catch (error) {
    console.error('Network Error:', error);
    return null;
  }
}
```

### 3. 缓存利用

```bash
# 先检查是否有缓存
curl "/audio" -I
# 如果没有缓存（404），再调用 TTS API
curl "/api?text=你好世界"
```

### 4. 批量操作

```bash
# 获取多个语音信息
for voice in "zh-CN-YunjianNeural" "zh-CN-XiaoyiNeural"; do
  curl -X POST "/api/voices/validate" -d "{\"voice_name\": \"$voice\"}"
done
```

## SDK 和客户端库

目前提供以下语言的 SDK：

- **Python**: [tts-api-python](https://github.com/qi-mooo/tts-api-python)
- **JavaScript**: [tts-api-js](https://github.com/qi-mooo/tts-api-js)
- **Go**: [tts-api-go](https://github.com/qi-mooo/tts-api-go)

## 更新日志

### v2.1.0
- 新增语音管理 API
- 支持 322+ 个语音
- 添加语音搜索和验证功能
- 优化 API 响应时间

### v2.0.0
- 重构 API 架构
- 添加结构化日志
- 改进错误处理
- 添加缓存系统

---

如有问题或建议，请查看 [故障排除文档](troubleshooting.md) 或 [提交 Issue](https://github.com/qi-mooo/tts-api/issues)。