# Web 管理控制台后端

## 概述

Web 管理控制台后端为 TTS 系统提供了完整的管理功能，包括用户认证、配置管理、字典规则管理和系统监控。

## 功能特性

### 1. 用户认证和会话管理
- 基于用户名/密码的登录认证
- 安全的密码哈希存储（PBKDF2 + SHA256）
- 会话管理和超时控制
- 登录/登出审计日志

### 2. 配置管理 API
- 获取和更新系统配置
- 配置验证和错误处理
- 支持 TTS、日志、系统等配置项
- 敏感信息过滤（密码哈希等）

### 3. 字典规则管理 API
- 获取所有字典规则或按类型过滤
- 添加新的发音替换和内容过滤规则
- 更新现有规则（启用/禁用、修改内容）
- 删除规则
- 规则验证（正则表达式检查）

### 4. 系统状态监控 API
- 系统运行时间和启动时间
- 内存使用情况（总量、已用、可用、百分比）
- CPU 使用率
- 磁盘使用情况
- Edge-TTS 服务状态检查
- 活跃会话数量

### 5. 其他功能
- 密码修改功能
- 日志查看功能
- 系统重启控制
- 完整的错误处理和日志记录

## API 端点

### 认证相关
- `POST /admin/login` - 用户登录
- `POST /admin/logout` - 用户登出
- `POST /admin/change-password` - 修改密码

### 配置管理
- `GET /admin/config` - 获取配置
- `POST /admin/config` - 更新配置

### 字典管理
- `GET /admin/dictionary` - 获取字典规则
- `POST /admin/dictionary` - 添加字典规则
- `PUT /admin/dictionary/<rule_id>` - 更新字典规则
- `DELETE /admin/dictionary/<rule_id>` - 删除字典规则

### 系统监控
- `GET /admin/dashboard` - 管理控制台仪表板
- `GET /admin/system/status` - 系统状态
- `POST /admin/system/restart` - 系统重启
- `GET /admin/logs` - 获取日志

## 安全特性

### 认证和授权
- 所有管理功能都需要认证
- 会话超时自动登出
- 密码强度验证
- 审计日志记录所有管理操作

### 数据保护
- 密码使用 PBKDF2 + SHA256 哈希
- 敏感配置信息不在 API 响应中暴露
- 输入验证和参数检查
- 错误信息不泄露系统内部信息

## 集成方式

### Flask 应用集成
```python
from admin.flask_integration import init_admin_app

app = Flask(__name__)
init_admin_app(app)
```

### 配置要求
- 需要设置管理员用户名和密码哈希
- 需要配置 Flask session 密钥
- 需要安装 psutil 依赖用于系统监控

## 测试

### 单元测试
```bash
./venv/bin/python3 -m unittest tests.test_admin_controller -v
```

### 基本功能测试
```bash
./venv/bin/python3 test_admin_basic.py
```

## 依赖项

- Flask - Web 框架
- psutil - 系统监控
- hashlib - 密码哈希
- secrets - 安全随机数生成
- 现有的配置管理、字典服务、日志系统和错误处理模块

## 配置示例

```json
{
  "admin": {
    "username": "admin",
    "password_hash": "salt:hash",
    "secret_key": "your-secret-key",
    "session_timeout": 3600
  }
}
```

## 使用说明

1. 启动应用后，管理控制台将在 `/admin` 路径下可用
2. 首次启动会使用默认密码 "admin123"，请及时修改
3. 所有管理操作都会记录审计日志
4. 系统状态监控提供实时的系统信息
5. 配置更改会立即生效并持久化保存

## 注意事项

- 生产环境中请确保使用 HTTPS
- 定期更换管理员密码
- 监控审计日志以发现异常操作
- 系统重启功能需要谨慎使用