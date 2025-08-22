# 健康检查模块

本模块为TTS系统提供全面的健康检查和系统监控功能。

## 功能特性

### 1. 系统状态监控
- **系统资源监控**: CPU使用率、内存使用率、磁盘使用率
- **服务状态检查**: Edge-TTS服务可用性和响应时间
- **应用状态监控**: 活跃请求数、缓存使用情况、错误统计

### 2. 健康检查端点
- **基本健康检查** (`/health`): 返回系统基本状态信息
- **详细健康检查** (`/health/detailed`): 返回完整的系统状态信息
- **就绪性检查** (`/health/ready`): 检查应用是否准备好接收流量
- **存活性检查** (`/health/live`): 检查应用是否仍在运行

### 3. 自动监控
- **请求监控**: 自动跟踪API请求的处理时间和状态
- **错误统计**: 自动记录和统计系统错误
- **缓存监控**: 自动监控缓存使用情况和命中率

## 快速开始

### 1. 基本集成

```python
from flask import Flask
from health_check.flask_integration import setup_health_monitoring

app = Flask(__name__)

# 设置健康监控（包含所有功能）
setup_health_monitoring(
    app=app,
    cache_instance=your_cache_instance,  # 可选
    app_version="1.0.0"
)

app.run()
```

### 2. 手动使用健康监控器

```python
from health_check.health_monitor import HealthMonitor
import asyncio

# 创建健康监控器
monitor = HealthMonitor(app_version="1.0.0")

# 获取健康状态摘要
summary = monitor.get_health_summary()
print(summary)

# 获取详细系统状态（异步）
async def get_status():
    status = await monitor.get_system_status()
    return status

status = asyncio.run(get_status())
```

### 3. 只使用健康检查端点

```python
from flask import Flask
from health_check.health_controller import health_controller

app = Flask(__name__)

# 注册健康检查端点
health_controller.register_with_app(app)

app.run()
```

## API 端点

### GET /health
基本健康检查端点，返回系统基本状态。

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime_seconds": 3600.0,
  "version": "1.0.0",
  "edge_tts_available": true
}
```

**状态码:**
- `200`: 系统健康或降级但可用
- `503`: 系统不健康

### GET /health/detailed
详细健康检查端点，返回完整的系统状态信息。

**查询参数:**
- `refresh=true`: 强制刷新缓存的状态信息

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": 3600.0,
  "version": "1.0.0",
  "memory_usage": 45.2,
  "memory_total": 8589934592,
  "memory_used": 3884917760,
  "cpu_usage": 25.5,
  "disk_usage": 60.8,
  "edge_tts_status": true,
  "edge_tts_response_time": 150.5,
  "active_requests": 3,
  "cache_size": 1048576,
  "cache_hit_rate": 85.2,
  "error_count_1h": 2,
  "error_count_24h": 15
}
```

### GET /health/ready
就绪性检查端点，检查应用是否准备好接收流量。

**响应示例:**
```json
{
  "ready": true,
  "status": "healthy",
  "edge_tts_available": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### GET /health/live
存活性检查端点，检查应用是否仍在运行。

**响应示例:**
```json
{
  "alive": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime_seconds": 3600.0
}
```

## 状态说明

### 系统状态
- **healthy**: 系统运行正常
- **degraded**: 系统运行但性能降级
- **unhealthy**: 系统存在严重问题

### 状态判断规则

#### Unhealthy (不健康)
- Edge-TTS服务不可用
- 内存使用率 > 90%
- CPU使用率 > 90%
- 磁盘使用率 > 95%

#### Degraded (降级)
- 1小时内错误数 > 50
- 内存使用率 > 80%
- CPU使用率 > 80%
- 磁盘使用率 > 85%

#### Healthy (健康)
- 所有服务正常
- 资源使用在合理范围内
- 错误率较低

## 监控指标

### 系统资源
- **内存使用率**: 当前内存使用百分比
- **CPU使用率**: 当前CPU使用百分比
- **磁盘使用率**: 根目录磁盘使用百分比

### 应用指标
- **活跃请求数**: 当前正在处理的请求数量
- **缓存大小**: 当前缓存使用的字节数
- **缓存命中率**: 缓存命中的百分比
- **错误统计**: 1小时和24小时内的错误数量

### 服务状态
- **Edge-TTS可用性**: Edge-TTS服务是否可用
- **Edge-TTS响应时间**: Edge-TTS服务的响应时间（毫秒）

## 配置选项

### HealthMonitor 配置
```python
monitor = HealthMonitor(
    app_version="1.0.0"  # 应用版本号
)
```

### 缓存TTL
健康状态信息会被缓存5秒，避免频繁的系统调用。可以通过 `force_refresh=True` 参数强制刷新。

## 集成示例

### 与现有TTS应用集成
```python
from flask import Flask
from health_check.flask_integration import setup_health_monitoring

app = Flask(__name__)

# 假设你有一个音频缓存实例
class AudioCache:
    def __init__(self):
        self.current_size = 0
    
    def add(self, data):
        # 缓存逻辑
        pass
    
    def combine(self):
        # 组合逻辑
        return cached_data

audio_cache = AudioCache()

# 设置健康监控
setup_health_monitoring(
    app=app,
    cache_instance=audio_cache,
    app_version="1.0.0"
)

# 你的其他路由
@app.route('/api')
def tts_api():
    # TTS API逻辑
    pass

if __name__ == '__main__':
    app.run()
```

### Docker健康检查
在Dockerfile中添加健康检查：

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
```

### Kubernetes健康检查
在Kubernetes部署中配置健康检查：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tts-app
spec:
  template:
    spec:
      containers:
      - name: tts
        image: tts-app:latest
        livenessProbe:
          httpGet:
            path: /health/live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 故障排除

### 常见问题

1. **Edge-TTS检查失败**
   - 检查网络连接
   - 确认Edge-TTS服务可用
   - 检查防火墙设置

2. **系统资源监控异常**
   - 确认psutil库已正确安装
   - 检查系统权限

3. **健康检查端点404**
   - 确认已正确注册蓝图
   - 检查URL路径

### 调试模式
启用详细日志记录：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 性能考虑

- 健康状态信息会被缓存5秒，减少系统调用开销
- Edge-TTS检查使用超时机制，避免长时间阻塞
- 系统资源监控使用高效的psutil库
- 错误统计使用时间窗口，自动清理过期数据

## 扩展功能

### 自定义健康检查
```python
from health_check.health_monitor import HealthMonitor

class CustomHealthMonitor(HealthMonitor):
    def _determine_overall_status(self, system_resources, edge_tts_status):
        # 自定义状态判断逻辑
        if your_custom_condition:
            return 'unhealthy'
        return super()._determine_overall_status(system_resources, edge_tts_status)
```

### 添加自定义指标
```python
monitor = HealthMonitor()

# 添加自定义统计
monitor.custom_metrics = {
    'database_connections': 10,
    'queue_size': 5
}
```