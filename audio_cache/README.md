# 优化音频缓存系统

## 概述

优化音频缓存系统是一个高性能、功能丰富的音频缓存解决方案，专为文本转语音（TTS）应用设计。该系统提供了智能的内存管理、详细的统计监控和灵活的配置选项。

## 主要特性

### 🚀 核心功能
- **LRU缓存策略**: 最近最少使用算法，智能管理缓存条目
- **配置集成**: 与配置管理系统深度集成，支持动态配置更新
- **线程安全**: 完全线程安全的实现，支持并发访问
- **内存优化**: 智能内存管理和自动清理机制

### 📊 统计监控
- **命中率统计**: 实时计算缓存命中率
- **内存使用监控**: 详细的内存使用情况跟踪
- **性能指标**: 包括平均条目大小、最旧条目年龄等
- **条目详情**: 每个缓存条目的详细信息

### ⚙️ 高级功能
- **自动过期**: 基于时间的自动条目过期
- **缓存优化**: 主动的缓存优化和清理
- **配置热更新**: 运行时配置更新支持
- **详细日志**: 结构化日志记录所有操作

## 安装和使用

### 基本使用

```python
from audio_cache import OptimizedAudioCache

# 创建缓存实例
cache = OptimizedAudioCache(
    size_limit=10*1024*1024,  # 10MB
    time_limit=1200           # 20分钟
)

# 存储音频
cache.put("你好世界", "zh-CN-YunjianNeural", 1.0, audio_segment)

# 获取音频
audio = cache.get("你好世界", "zh-CN-YunjianNeural", 1.0)
if audio:
    print("缓存命中！")
else:
    print("缓存未命中")
```

### 统计信息获取

```python
# 获取详细统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']:.2%}")
print(f"内存使用: {stats['memory_usage_percent']:.1f}%")
print(f"缓存条目数: {stats['entry_count']}")

# 获取条目详情
entries = cache.get_cache_entries_info()
for entry in entries:
    print(f"条目大小: {entry['size_kb']}KB, 访问次数: {entry['access_count']}")
```

### 缓存管理

```python
# 清空缓存
cache.clear()

# 优化缓存
result = cache.optimize()
print(f"优化移除了 {result['entries_removed']} 个条目")

# 检查缓存状态
print(f"缓存条目数: {len(cache)}")
```

## API 参考

### OptimizedAudioCache 类

#### 构造函数
```python
OptimizedAudioCache(size_limit=None, time_limit=None)
```
- `size_limit`: 缓存大小限制（字节），None则使用配置文件值
- `time_limit`: 缓存时间限制（秒），None则使用配置文件值

#### 主要方法

##### put(text, voice, speed, audio_segment)
存储音频到缓存
- `text`: 文本内容
- `voice`: 语音类型
- `speed`: 语速
- `audio_segment`: AudioSegment对象

##### get(text, voice, speed)
从缓存获取音频
- 返回: AudioSegment对象或None

##### get_stats()
获取详细统计信息
- 返回: 包含统计数据的字典

##### get_cache_entries_info()
获取所有缓存条目信息
- 返回: 条目信息列表

##### clear()
清空所有缓存

##### optimize()
优化缓存性能
- 返回: 优化结果统计

## 统计信息说明

### 基本统计
- `hits`: 缓存命中次数
- `misses`: 缓存未命中次数
- `evictions`: 条目淘汰次数
- `total_requests`: 总请求次数
- `entry_count`: 当前条目数
- `total_size_bytes`: 当前总大小

### 计算统计
- `hit_rate`: 命中率 (0.0-1.0)
- `memory_usage_percent`: 内存使用百分比
- `average_entry_size`: 平均条目大小
- `oldest_entry_age`: 最旧条目年龄（秒）

### 效率指标
- `hit_rate_percent`: 命中率百分比
- `memory_utilization_percent`: 内存利用率百分比
- `average_entry_size_kb`: 平均条目大小（KB）
- `entries_per_mb`: 每MB的条目数

## 配置集成

缓存系统与配置管理器集成，支持以下配置项：

```json
{
  "tts": {
    "cache_size_limit": 10485760,  // 10MB
    "cache_time_limit": 1200       // 20分钟
  }
}
```

配置更新会自动应用到运行中的缓存实例。

## 性能优化建议

### 缓存大小设置
- **小型应用**: 1-10MB
- **中型应用**: 10-100MB  
- **大型应用**: 100MB-1GB

### 时间限制设置
- **开发环境**: 5-10分钟
- **生产环境**: 20-60分钟
- **长期缓存**: 2-24小时

### 监控指标
- **命中率**: 目标 >70%
- **内存使用**: 保持 <90%
- **淘汰频率**: 监控异常增长

## 线程安全

缓存系统使用 `threading.RLock` 确保线程安全，支持：
- 并发读取操作
- 并发写入操作
- 混合读写操作

## 错误处理

系统包含完善的错误处理机制：
- 无效音频对象检测
- 配置错误恢复
- 内存不足保护
- 异常日志记录

## 测试

运行单元测试：
```bash
./venv/bin/python3 -m unittest tests.test_audio_cache -v
```

运行示例代码：
```bash
./venv/bin/python3 audio_cache/example_usage.py
```

## 日志记录

缓存系统使用结构化日志记录所有重要操作：
- 缓存命中/未命中
- 条目添加/移除
- 配置更新
- 优化操作
- 错误情况

日志级别：
- `DEBUG`: 详细操作信息
- `INFO`: 重要状态变更
- `WARNING`: 潜在问题
- `ERROR`: 错误情况

## 最佳实践

### 1. 合理设置缓存大小
```python
# 根据可用内存设置合理的缓存大小
available_memory = get_available_memory()
cache_size = min(available_memory * 0.1, 100 * 1024 * 1024)  # 10%或100MB
```

### 2. 监控缓存性能
```python
# 定期检查缓存统计
stats = cache.get_stats()
if stats['hit_rate'] < 0.5:
    logger.warning("缓存命中率过低，考虑调整配置")
```

### 3. 适时优化缓存
```python
# 在内存使用率过高时执行优化
stats = cache.get_stats()
if stats['memory_usage_percent'] > 85:
    cache.optimize()
```

### 4. 处理配置更新
```python
# 监听配置变更
def on_config_change(key, value):
    if key.startswith('tts.cache'):
        logger.info(f"缓存配置已更新: {key} = {value}")

config_manager.add_watcher(on_config_change)
```

## 故障排除

### 常见问题

1. **内存使用过高**
   - 减少 `cache_size_limit`
   - 缩短 `cache_time_limit`
   - 执行 `cache.optimize()`

2. **命中率过低**
   - 检查缓存键生成逻辑
   - 增加缓存大小
   - 延长过期时间

3. **性能问题**
   - 检查并发访问模式
   - 监控锁竞争
   - 优化缓存策略

### 调试信息

启用详细日志：
```python
import logging
logging.getLogger('audio_cache').setLevel(logging.DEBUG)
```

获取诊断信息：
```python
# 获取详细统计
stats = cache.get_stats()
entries = cache.get_cache_entries_info()

# 检查缓存状态
print(f"缓存健康度: {stats['hit_rate']:.2%}")
print(f"内存压力: {stats['memory_usage_percent']:.1f}%")
```