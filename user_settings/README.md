# 用户个人设置模块

用户个人设置模块提供基于用户身份的个性化偏好设置管理功能，支持语音偏好、界面主题、行为设置等。

## 功能特性

- **用户身份识别**: 基于IP地址和User-Agent自动生成用户ID
- **个性化设置**: 支持默认语音、语速、音频格式等偏好设置
- **界面定制**: 主题、语言、高级选项显示等界面设置
- **数据持久化**: 设置自动保存到本地文件
- **导入导出**: 支持设置的备份、导出和导入
- **多用户支持**: 不同用户的设置完全独立
- **设置验证**: 自动验证和修正无效的设置值

## 快速开始

### 基本使用

```python
from user_settings import user_settings_service

# 获取用户信息（通常从Flask request中获取）
user_info = {
    'ip': request.remote_addr,
    'user_agent': request.headers.get('User-Agent')
}

# 生成用户ID
user_id = user_settings_service.get_user_id_from_request(user_info)

# 加载用户设置
settings = user_settings_service.load_user_settings(user_id)
print(f"用户默认语速: {settings.default_speed}")

# 更新设置
user_settings_service.update_user_settings(
    user_id,
    default_speed=1.5,
    theme="dark",
    auto_play=True
)
```

### REST API 使用

```bash
# 获取用户设置
curl -X GET "http://localhost:8080/api/settings"

# 更新用户设置
curl -X POST "http://localhost:8080/api/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "default_speed": 1.5,
    "theme": "dark",
    "auto_play": true
  }'

# 导出设置
curl -X GET "http://localhost:8080/api/settings/export?download=true"

# 重置设置
curl -X POST "http://localhost:8080/api/settings/reset"
```

## 设置项说明

### 语音设置

- `default_narration_voice`: 默认旁白语音（可选）
- `default_dialogue_voice`: 默认对话语音（可选）
- `default_speed`: 默认语速（0.5-3.0，默认1.0）
- `preferred_format`: 首选音频格式（webm/mp3/wav，默认webm）

### 界面设置

- `theme`: 界面主题（light/dark/auto，默认light）
- `language`: 界面语言（zh-CN/en-US，默认zh-CN）
- `auto_play`: 是否自动播放音频（默认false）
- `show_advanced_options`: 是否显示高级选项（默认false）

## 用户身份识别

系统使用IP地址和User-Agent的组合来生成唯一的用户ID：

```python
# 用户ID生成逻辑
identifier = f"{ip}:{user_agent}"
user_id = hashlib.md5(identifier.encode('utf-8')).hexdigest()[:16]
```

这种方式的特点：
- **无需注册**: 用户无需创建账户即可享受个性化设置
- **自动识别**: 基于浏览器和网络环境自动识别用户
- **隐私保护**: 不收集个人敏感信息
- **跨会话**: 设置在浏览器会话间保持

## 数据存储格式

用户设置以JSON格式存储在 `user_settings/data/` 目录下：

```json
{
  "user_id": "0257ef049147659d",
  "default_narration_voice": "zh-CN-YunjianNeural",
  "default_dialogue_voice": "zh-CN-XiaoxiaoNeural",
  "default_speed": 1.5,
  "preferred_format": "webm",
  "auto_play": false,
  "show_advanced_options": true,
  "theme": "dark",
  "language": "zh-CN",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

## API 参考

### UserSettingsService 类

#### 主要方法

- `get_user_id_from_request(request_info: Dict) -> str`: 从请求信息生成用户ID
- `load_user_settings(user_id: str) -> UserSettings`: 加载用户设置
- `save_user_settings(settings: UserSettings) -> bool`: 保存用户设置
- `update_user_settings(user_id: str, **kwargs) -> bool`: 更新用户设置
- `export_user_settings(user_id: str) -> Dict`: 导出用户设置
- `import_user_settings(user_id: str, data: Dict) -> bool`: 导入用户设置
- `reset_user_settings(user_id: str) -> bool`: 重置用户设置
- `backup_user_settings(user_id: str) -> str`: 备份用户设置
- `restore_from_backup(user_id: str, backup_path: str) -> bool`: 从备份恢复

### REST API 端点

- `GET /api/settings`: 获取用户设置
- `POST /api/settings`: 更新用户设置
- `GET /api/settings/export`: 导出用户设置
- `POST /api/settings/import`: 导入用户设置
- `POST /api/settings/reset`: 重置用户设置
- `POST /api/settings/backup`: 备份用户设置
- `GET /api/settings/backups`: 获取备份列表
- `POST /api/settings/restore`: 从备份恢复

## 管理界面集成

用户设置功能已集成到管理控制台的"个人设置"页面：

1. **基本设置**: 语音偏好、语速、音频格式
2. **界面设置**: 主题、语言、行为选项
3. **操作功能**: 保存、重置、导入、导出、备份

### 使用步骤

1. 访问管理控制台
2. 点击左侧菜单的"个人设置"
3. 在"用户偏好设置"区域调整各项设置
4. 点击"保存设置"按钮保存更改

## 示例脚本

运行示例脚本查看完整功能演示：

```bash
python3 tests/test_user_settings.py
```

## 集成到 TTS 系统

用户设置可以轻松集成到TTS请求处理中：

```python
from user_settings import user_settings_service

def process_tts_request(request):
    # 获取用户设置
    user_info = {
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    }
    user_id = user_settings_service.get_user_id_from_request(user_info)
    settings = user_settings_service.load_user_settings(user_id)
    
    # 应用用户偏好
    if not request.args.get('speed'):
        speed = settings.default_speed
    
    if not request.args.get('narr') and settings.default_narration_voice:
        narration_voice = settings.default_narration_voice
    
    # 处理TTS请求...
```

## 注意事项

1. **用户识别限制**: 基于IP和User-Agent的识别可能在某些情况下不够精确
2. **数据清理**: 建议定期清理长期未使用的设置文件
3. **备份管理**: 备份文件会占用存储空间，需要定期清理
4. **设置验证**: 系统会自动验证和修正无效设置值
5. **并发安全**: 多个请求同时修改同一用户设置时可能存在竞争条件

## 扩展功能

### 自定义设置字段

可以通过修改 `UserSettings` 数据模型来添加新的设置字段：

```python
@dataclass
class UserSettings:
    # 现有字段...
    custom_field: str = "default_value"
```

### 设置分组

可以将相关设置分组管理：

```python
# 语音设置组
voice_settings = {
    'default_narration_voice': settings.default_narration_voice,
    'default_dialogue_voice': settings.default_dialogue_voice,
    'default_speed': settings.default_speed
}

# 界面设置组
ui_settings = {
    'theme': settings.theme,
    'language': settings.language,
    'auto_play': settings.auto_play
}
```

### 设置同步

可以实现设置在多个设备间的同步：

```python
def sync_settings_to_cloud(user_id: str, settings: UserSettings):
    # 上传设置到云端
    pass

def sync_settings_from_cloud(user_id: str) -> UserSettings:
    # 从云端下载设置
    pass
```