# 重启控制器模块

重启控制器模块提供了优雅重启功能，支持在不中断服务的情况下重新加载配置和重启系统。

## 功能特性

### 核心功能
- **优雅重启**: 等待活跃请求完成后再执行重启
- **配置重载**: 重启时自动重新加载配置文件
- **请求跟踪**: 实时跟踪活跃的HTTP请求
- **权限控制**: 支持重启权限验证和安全控制
- **回滚机制**: 重启失败时自动回滚到之前状态
- **历史记录**: 记录所有重启操作的历史

### 安全特性
- 重启权限验证
- 配置备份和恢复
- 异常处理和错误恢复
- 审计日志记录

## 使用方法

### 1. 基本使用

```python
from restart.restart_controller import restart_controller

# 请求重启
result = restart_controller.request_restart(
    user="admin",
    reason="配置更新",
    force=False,
    config_reload=True,
    timeout=30
)

# 检查重启状态
status = restart_controller.get_restart_status()
print(f"重启状态: {status['status']}")

# 取消重启（仅在准备阶段可取消）
restart_controller.cancel_restart("admin")
```

### 2. Flask集成

```python
from flask import Flask
from restart.flask_integration import restart_middleware

app = Flask(__name__)

# 初始化重启中间件
restart_middleware.init_app(app)

# 中间件会自动：
# - 跟踪活跃请求
# - 在重启期间阻止新请求
# - 提供重启相关的API端点
```

### 3. 回调函数

```python
def pre_restart_callback():
    """重启前执行的清理工作"""
    print("准备重启，清理资源...")
    # 保存缓存、关闭连接等

def post_restart_callback():
    """重启后执行的恢复工作"""
    print("重启完成，恢复服务...")
    # 重新初始化缓存、重建连接等

# 注册回调函数
restart_controller.add_pre_restart_callback(pre_restart_callback)
restart_controller.add_post_restart_callback(post_restart_callback)
```

## API端点

当使用Flask集成时，会自动注册以下API端点：

### GET /api/restart/status
获取重启状态信息

**响应示例：**
```json
{
  "success": true,
  "data": {
    "status": "idle",
    "is_restarting": false,
    "active_requests_count": 0,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### POST /api/restart/request
请求系统重启

**请求体：**
```json
{
  "user": "admin",
  "reason": "配置更新",
  "force": false,
  "config_reload": true,
  "timeout": 30
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "重启请求已提交",
  "request_id": "restart_1234567890",
  "status": "preparing",
  "estimated_time": 40
}
```

### POST /api/restart/cancel
取消重启请求

**请求体：**
```json
{
  "user": "admin"
}
```

### GET /api/restart/history
获取重启历史记录

**查询参数：**
- `limit`: 返回记录数量限制（默认10）

## 重启状态

重启控制器支持以下状态：

- `idle`: 空闲状态，可以接受新的重启请求
- `preparing`: 准备重启，执行重启前的准备工作
- `waiting_requests`: 等待活跃请求完成
- `restarting`: 正在执行重启操作
- `recovering`: 重启失败，正在恢复
- `completed`: 重启完成
- `failed`: 重启失败

## 配置选项

重启功能的配置通过配置管理器进行：

```json
{
  "restart": {
    "default_timeout": 30,
    "max_wait_time": 300,
    "enable_force_restart": true,
    "backup_config": true
  }
}
```

## 错误处理

重启控制器定义了以下错误码：

- `RESTART_001`: 系统正在重启中
- `RESTART_002`: 无法取消重启
- `RESTART_003`: 配置备份失败
- `RESTART_004`: 配置验证失败

## 最佳实践

### 1. 重启前准备
- 确保没有重要的长时间运行任务
- 备份重要数据和配置
- 通知相关用户

### 2. 监控重启过程
- 监控重启状态
- 检查活跃请求数量
- 关注重启日志

### 3. 重启后验证
- 验证服务是否正常启动
- 检查配置是否正确加载
- 测试关键功能

### 4. 异常处理
- 设置合理的超时时间
- 准备回滚方案
- 监控重启历史

## 示例代码

### 完整的重启流程示例

```python
import time
from restart.restart_controller import restart_controller

def safe_restart(user, reason, timeout=60):
    """安全重启函数"""
    try:
        # 1. 检查当前状态
        if restart_controller.is_restarting:
            print("系统正在重启中，请稍后再试")
            return False
        
        # 2. 请求重启
        result = restart_controller.request_restart(
            user=user,
            reason=reason,
            timeout=timeout
        )
        
        if not result['success']:
            print(f"重启请求失败: {result.get('message', '未知错误')}")
            return False
        
        print(f"重启请求已提交: {result['request_id']}")
        
        # 3. 监控重启过程
        while True:
            status = restart_controller.get_restart_status()
            print(f"重启状态: {status['status']}")
            
            if status['status'] == 'completed':
                print("重启完成")
                return True
            elif status['status'] == 'failed':
                print("重启失败")
                return False
            
            time.sleep(2)
            
    except Exception as e:
        print(f"重启过程异常: {e}")
        return False

# 使用示例
if __name__ == '__main__':
    success = safe_restart("admin", "系统维护")
    if success:
        print("重启成功")
    else:
        print("重启失败")
```

## 故障排除

### 常见问题

1. **重启请求被拒绝**
   - 检查是否已有重启在进行中
   - 验证用户权限
   - 检查系统状态

2. **重启超时**
   - 检查活跃请求数量
   - 增加超时时间
   - 考虑使用强制重启

3. **配置重载失败**
   - 检查配置文件语法
   - 验证配置文件权限
   - 查看错误日志

4. **重启后服务异常**
   - 检查重启日志
   - 验证配置文件
   - 检查依赖服务状态

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.getLogger('restart_controller').setLevel(logging.DEBUG)
   ```

2. **监控重启状态**
   ```python
   status = restart_controller.get_restart_status()
   print(json.dumps(status, indent=2))
   ```

3. **查看重启历史**
   ```python
   history = restart_controller.get_restart_history(limit=5)
   for entry in history:
       print(f"{entry['timestamp']}: {entry['reason']} - {entry['success']}")
   ```

## 注意事项

1. **重启是一个敏感操作**，应该谨慎使用并做好权限控制
2. **强制重启**会中断正在处理的请求，只在紧急情况下使用
3. **配置备份**很重要，确保重启失败时能够恢复
4. **监控重启过程**，及时发现和处理异常情况
5. **测试重启功能**，在生产环境使用前充分测试