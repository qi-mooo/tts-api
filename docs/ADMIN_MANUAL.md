# TTS 系统管理员使用手册

## 概述

本手册为 TTS 系统管理员提供详细的操作指南，包括系统配置、用户管理、监控维护和故障处理等内容。

## 目录

1. [快速开始](#快速开始)
2. [Web 管理控制台](#web-管理控制台)
3. [系统配置管理](#系统配置管理)
4. [字典服务管理](#字典服务管理)
5. [用户和权限管理](#用户和权限管理)
6. [系统监控](#系统监控)
7. [日志管理](#日志管理)
8. [备份和恢复](#备份和恢复)
9. [性能优化](#性能优化)
10. [故障处理](#故障处理)

## 快速开始

### 首次登录

1. **访问管理控制台**
   ```
   http://your-server:8080/admin
   ```

2. **使用默认凭据登录**
   - 用户名：`admin`
   - 密码：部署时设置的密码

3. **修改默认密码**（强烈推荐）
   - 进入"系统设置" → "安全配置"
   - 点击"修改密码"
   - 输入新密码并确认

### 基本系统检查

登录后首先检查以下项目：

1. **系统状态**：确认所有服务正常运行
2. **Edge-TTS 连接**：验证外部服务可用性
3. **存储空间**：检查日志和缓存空间使用情况
4. **配置完整性**：确认所有必要配置项已设置

## Web 管理控制台

### 控制台概览

管理控制台提供以下主要功能模块：

#### 1. 仪表板
- 系统运行状态概览
- 实时性能指标
- 最近请求统计
- 告警信息显示

#### 2. TTS 配置
- 语音参数设置
- 缓存配置管理
- 性能参数调优

#### 3. 字典管理
- 发音规则配置
- 内容过滤规则
- 规则测试和预览

#### 4. 系统监控
- 服务状态监控
- 性能指标图表
- 日志实时查看

#### 5. 系统设置
- 用户账户管理
- 安全配置
- 系统维护工具

### 界面导航

```
┌─────────────────────────────────────────────────────────┐
│ TTS 管理控制台                              [admin] [退出] │
├─────────────────────────────────────────────────────────┤
│ [仪表板] [TTS配置] [字典管理] [系统监控] [系统设置]        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  主要内容区域                                            │
│                                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 系统配置管理

### TTS 语音配置

#### 基本语音设置

1. **旁白语音配置**
   - 进入"TTS配置" → "语音设置"
   - 选择旁白语音：推荐使用 `zh-CN-YunjianNeural`（男声）
   - 设置语速：建议范围 0.8-1.5
   - 测试语音效果

2. **对话语音配置**
   - 选择对话语音：推荐使用 `zh-CN-XiaoyiNeural`（女声）
   - 设置语速：通常与旁白保持一致
   - 配置音调和音量（如支持）

#### 高级语音设置

```json
{
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.2,
    "voice_styles": {
      "narration": "calm",
      "dialogue": "cheerful"
    },
    "prosody": {
      "rate": "medium",
      "pitch": "medium",
      "volume": "medium"
    }
  }
}
```

#### 语音测试

使用内置的语音预览功能：

1. 在语音配置页面点击"测试语音"
2. 输入测试文本：`这是旁白内容："这是对话内容"`
3. 点击"生成预览"
4. 播放音频确认效果
5. 满意后点击"保存配置"

### 缓存配置

#### 缓存参数设置

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `cache_size_limit` | 50MB | 缓存总大小限制 |
| `cache_time_limit` | 3600秒 | 缓存过期时间 |
| `max_cache_entries` | 1000 | 最大缓存条目数 |

#### 缓存策略配置

```json
{
  "cache": {
    "enabled": true,
    "size_limit": 52428800,
    "time_limit": 3600,
    "cleanup_interval": 300,
    "compression": true,
    "strategy": "lru"
  }
}
```

### 系统性能配置

#### 并发控制

```json
{
  "system": {
    "max_workers": 10,
    "request_timeout": 120,
    "queue_size": 100,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60
    }
  }
}
```

#### 资源限制

```json
{
  "resources": {
    "memory_limit": "1GB",
    "cpu_limit": "2.0",
    "disk_space_threshold": "90%"
  }
}
```

## 字典服务管理

### 发音规则管理

#### 添加发音规则

1. **进入字典管理页面**
   - 点击"字典管理" → "发音规则"

2. **添加新规则**
   - 点击"添加规则"按钮
   - 填写规则信息：
     ```
     规则类型：发音替换
     匹配模式：GitHub
     替换文本：吉特哈布
     启用状态：是
     ```

3. **测试规则**
   - 在测试区域输入：`这是一个 GitHub 项目`
   - 点击"测试规则"
   - 确认输出：`这是一个 吉特哈布 项目`

4. **保存规则**
   - 确认无误后点击"保存"

#### 常用发音规则示例

| 原文 | 替换 | 说明 |
|------|------|------|
| API | A P I | 英文缩写 |
| GitHub | 吉特哈布 | 平台名称 |
| Docker | 多克 | 技术术语 |
| Linux | 里纳克斯 | 操作系统 |
| MySQL | 迈 S Q L | 数据库 |

### 内容过滤规则

#### 添加过滤规则

1. **敏感词过滤**
   ```
   规则类型：内容过滤
   匹配模式：敏感词
   替换文本：***
   启用状态：是
   ```

2. **正则表达式过滤**
   ```
   规则类型：内容过滤
   匹配模式：\b\d{11}\b
   替换文本：[手机号]
   启用状态：是
   ```

#### 规则优先级

规则按以下优先级执行：
1. 内容过滤规则（最高优先级）
2. 发音替换规则
3. 格式化规则（最低优先级）

### 批量规则管理

#### 导入规则

1. **准备规则文件**（JSON格式）
   ```json
   {
     "rules": [
       {
         "type": "pronunciation",
         "pattern": "API",
         "replacement": "A P I",
         "enabled": true
       },
       {
         "type": "filter",
         "pattern": "敏感词",
         "replacement": "***",
         "enabled": true
       }
     ]
   }
   ```

2. **导入操作**
   - 点击"批量导入"
   - 选择规则文件
   - 预览导入内容
   - 确认导入

#### 导出规则

1. **选择导出范围**
   - 全部规则
   - 已启用规则
   - 特定类型规则

2. **导出格式**
   - JSON 格式（推荐）
   - CSV 格式
   - Excel 格式

## 用户和权限管理

### 管理员账户管理

#### 修改管理员密码

1. **通过 Web 界面**
   - 进入"系统设置" → "安全配置"
   - 点击"修改密码"
   - 输入当前密码和新密码
   - 确认修改

2. **通过命令行**
   ```bash
   # 使用设置脚本
   python3 setup.py --password new-password
   
   # 使用 bcrypt 生成哈希
   python3 -c "
   import bcrypt
   password = 'new-password'
   hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   print(hash.decode('utf-8'))
   "
   ```

#### 会话管理

```json
{
  "admin": {
    "session_timeout": 3600,
    "max_sessions": 3,
    "force_logout_on_password_change": true,
    "remember_me_duration": 86400
  }
}
```

### 访问控制

#### IP 白名单配置

```json
{
  "security": {
    "ip_whitelist": {
      "enabled": true,
      "allowed_ips": [
        "127.0.0.1",
        "192.168.1.0/24",
        "10.0.0.0/8"
      ]
    }
  }
}
```

#### API 访问控制

```json
{
  "api": {
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_limit": 10
    },
    "authentication": {
      "required": false,
      "api_key_header": "X-API-Key"
    }
  }
}
```

## 系统监控

### 实时监控仪表板

#### 系统状态指标

1. **服务状态**
   - TTS API 服务：运行中/停止
   - Edge-TTS 连接：正常/异常
   - 缓存服务：活跃/不可用
   - 数据库连接：正常/异常

2. **性能指标**
   - CPU 使用率：< 80% 正常
   - 内存使用率：< 85% 正常
   - 磁盘使用率：< 90% 正常
   - 网络延迟：< 200ms 正常

3. **业务指标**
   - 请求成功率：> 95% 正常
   - 平均响应时间：< 3秒 正常
   - 缓存命中率：> 70% 正常
   - 错误率：< 5% 正常

#### 告警配置

```json
{
  "alerts": {
    "cpu_threshold": 80,
    "memory_threshold": 85,
    "disk_threshold": 90,
    "error_rate_threshold": 5,
    "response_time_threshold": 5000,
    "notification": {
      "email": "admin@example.com",
      "webhook": "https://hooks.slack.com/..."
    }
  }
}
```

### 性能图表

#### 请求统计图表

- 每小时请求数量
- 请求成功率趋势
- 平均响应时间
- 错误类型分布

#### 系统资源图表

- CPU 使用率历史
- 内存使用趋势
- 磁盘 I/O 统计
- 网络流量统计

### 健康检查

#### 自动健康检查

系统每 30 秒执行一次健康检查：

1. **Edge-TTS 服务检查**
   - 连接测试
   - 响应时间测量
   - 服务可用性验证

2. **本地服务检查**
   - 缓存服务状态
   - 文件系统可用性
   - 配置文件完整性

3. **资源使用检查**
   - 内存使用情况
   - 磁盘空间检查
   - CPU 负载监控

#### 手动健康检查

```bash
# 通过 API 检查
curl http://localhost:8080/health?detailed=true

# 通过管理界面
# 进入"系统监控" → "健康检查" → 点击"立即检查"
```

## 日志管理

### 日志配置

#### 日志级别设置

```json
{
  "logging": {
    "level": "INFO",
    "modules": {
      "tts_service": "DEBUG",
      "cache": "INFO",
      "admin": "WARNING"
    }
  }
}
```

#### 日志轮转配置

```json
{
  "logging": {
    "rotation": {
      "max_size": "10MB",
      "backup_count": 10,
      "compress": true,
      "interval": "daily"
    }
  }
}
```

### 日志查看和分析

#### Web 界面日志查看

1. **进入日志管理**
   - 点击"系统监控" → "日志管理"

2. **日志过滤**
   - 按时间范围过滤
   - 按日志级别过滤
   - 按模块名称过滤
   - 按关键词搜索

3. **日志导出**
   - 选择时间范围
   - 选择导出格式（TXT/JSON/CSV）
   - 下载日志文件

#### 命令行日志查看

```bash
# 查看实时日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log

# 查看特定时间段日志
grep "2024-01-01" logs/app.log

# 统计错误数量
grep -c "ERROR" logs/app.log
```

### 日志分析

#### 常见日志模式

1. **成功请求日志**
   ```json
   {
     "timestamp": "2024-01-01T12:00:00Z",
     "level": "INFO",
     "module": "tts_service",
     "message": "TTS 请求处理成功",
     "request_id": "req_123456",
     "duration_ms": 1500,
     "cache_hit": true
   }
   ```

2. **错误日志**
   ```json
   {
     "timestamp": "2024-01-01T12:00:00Z",
     "level": "ERROR",
     "module": "tts_service",
     "message": "Edge-TTS 服务不可用",
     "error_code": "TTS_001",
     "request_id": "req_123456",
     "retry_count": 3
   }
   ```

#### 性能分析

通过日志分析系统性能：

```bash
# 分析平均响应时间
grep "duration_ms" logs/app.log | \
  awk -F'"duration_ms":' '{print $2}' | \
  awk -F',' '{sum+=$1; count++} END {print "平均响应时间:", sum/count, "ms"}'

# 分析缓存命中率
grep "cache_hit" logs/app.log | \
  grep -c "true" && grep "cache_hit" logs/app.log | wc -l

# 分析错误率
total=$(grep -c "request_id" logs/app.log)
errors=$(grep -c "ERROR" logs/app.log)
echo "错误率: $(echo "scale=2; $errors * 100 / $total" | bc)%"
```

## 备份和恢复

### 数据备份

#### 自动备份配置

```json
{
  "backup": {
    "enabled": true,
    "schedule": "0 2 * * *",
    "retention_days": 30,
    "backup_path": "/backup",
    "items": [
      "config.json",
      "dictionary/rules.json",
      "logs/",
      "cache/"
    ]
  }
}
```

#### 手动备份

```bash
# 创建完整备份
./scripts/backup.sh --full

# 创建配置备份
./scripts/backup.sh --config-only

# 创建增量备份
./scripts/backup.sh --incremental
```

### 数据恢复

#### 配置恢复

```bash
# 恢复配置文件
cp backup/config.json.backup config.json

# 恢复字典规则
cp backup/rules.json.backup dictionary/rules.json

# 重启服务
docker-compose restart
```

#### 完整系统恢复

```bash
# 停止服务
docker-compose down

# 恢复数据
tar -xzf backup-20240101.tar.gz

# 验证配置
python3 -c "import json; json.load(open('config.json'))"

# 启动服务
docker-compose up -d

# 验证恢复
curl http://localhost:8080/health
```

## 性能优化

### 系统性能调优

#### CPU 优化

```json
{
  "system": {
    "max_workers": 4,
    "worker_class": "sync",
    "worker_connections": 1000,
    "preload_app": true
  }
}
```

#### 内存优化

```json
{
  "memory": {
    "cache_size_limit": 52428800,
    "max_cache_entries": 1000,
    "garbage_collection": {
      "enabled": true,
      "threshold": 0.8
    }
  }
}
```

#### 网络优化

```json
{
  "network": {
    "connection_pool_size": 20,
    "timeout": 30,
    "retry_attempts": 3,
    "keepalive": true
  }
}
```

### 缓存优化

#### 缓存策略调整

1. **LRU 策略**：适用于访问模式相对均匀的场景
2. **LFU 策略**：适用于热点数据明显的场景
3. **TTL 策略**：适用于数据时效性要求高的场景

#### 缓存监控

```bash
# 查看缓存统计
curl http://localhost:8080/admin/cache/stats

# 清理缓存
curl -X POST http://localhost:8080/admin/cache/clear

# 预热缓存
curl -X POST http://localhost:8080/admin/cache/warmup
```

### 数据库优化

#### 索引优化

```sql
-- 为常用查询添加索引
CREATE INDEX idx_request_timestamp ON requests(timestamp);
CREATE INDEX idx_cache_key ON cache_entries(cache_key);
```

#### 查询优化

```sql
-- 优化日志查询
SELECT * FROM logs 
WHERE timestamp >= NOW() - INTERVAL 1 DAY 
  AND level = 'ERROR'
ORDER BY timestamp DESC 
LIMIT 100;
```

## 故障处理

### 常见故障及解决方案

#### 1. Edge-TTS 服务不可用

**症状**：
- API 返回 503 错误
- 日志显示 "TTS_001" 错误码
- 健康检查显示 Edge-TTS 不可用

**解决步骤**：
1. 检查网络连接
   ```bash
   curl -I https://speech.platform.bing.com
   ```

2. 检查 DNS 解析
   ```bash
   nslookup speech.platform.bing.com
   ```

3. 重启服务
   ```bash
   docker-compose restart
   ```

4. 如果问题持续，配置代理或使用备用服务

#### 2. 内存不足

**症状**：
- 系统响应缓慢
- 日志显示内存相关错误
- 监控显示内存使用率 > 90%

**解决步骤**：
1. 清理缓存
   ```bash
   curl -X POST http://localhost:8080/admin/cache/clear
   ```

2. 调整缓存配置
   ```json
   {
     "cache": {
       "size_limit": 26214400,  // 减少到 25MB
       "max_entries": 500       // 减少条目数
     }
   }
   ```

3. 重启服务释放内存
   ```bash
   docker-compose restart
   ```

#### 3. 磁盘空间不足

**症状**：
- 日志写入失败
- 缓存无法保存
- 系统告警磁盘空间不足

**解决步骤**：
1. 清理旧日志
   ```bash
   find logs/ -name "*.log.*" -mtime +7 -delete
   ```

2. 清理缓存文件
   ```bash
   rm -rf cache/*
   ```

3. 配置日志轮转
   ```json
   {
     "logging": {
       "rotation": {
         "max_size": "5MB",
         "backup_count": 5
       }
     }
   }
   ```

#### 4. 配置文件损坏

**症状**：
- 服务启动失败
- 配置加载错误
- JSON 解析错误

**解决步骤**：
1. 验证配置文件格式
   ```bash
   python3 -c "import json; json.load(open('config.json'))"
   ```

2. 从备份恢复
   ```bash
   cp config.json.backup config.json
   ```

3. 重新生成配置
   ```bash
   python3 setup.py --init
   ```

### 故障诊断工具

#### 系统诊断脚本

```bash
#!/bin/bash
# diagnose.sh - 系统诊断脚本

echo "=== TTS 系统诊断报告 ==="
echo "时间: $(date)"
echo

echo "1. 服务状态检查"
curl -s http://localhost:8080/health | jq .

echo "2. 系统资源检查"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')"
echo "内存: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "磁盘: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo "3. 日志错误检查"
echo "最近错误数量: $(grep -c "ERROR" logs/app.log | tail -100)"

echo "4. 配置文件检查"
python3 -c "
import json
try:
    json.load(open('config.json'))
    print('配置文件格式正确')
except Exception as e:
    print(f'配置文件错误: {e}')
"

echo "5. 网络连接检查"
curl -s -I https://speech.platform.bing.com | head -1
```

#### 性能分析工具

```bash
#!/bin/bash
# performance.sh - 性能分析脚本

echo "=== 性能分析报告 ==="

echo "1. 请求统计"
echo "总请求数: $(grep -c 'request_id' logs/app.log)"
echo "成功请求: $(grep -c 'TTS 请求处理成功' logs/app.log)"
echo "失败请求: $(grep -c 'ERROR' logs/app.log)"

echo "2. 响应时间分析"
grep "duration_ms" logs/app.log | \
  awk -F'"duration_ms":' '{print $2}' | \
  awk -F',' '{
    sum+=$1; 
    count++; 
    if($1>max) max=$1; 
    if(min=="" || $1<min) min=$1
  } END {
    print "平均响应时间:", sum/count, "ms"
    print "最大响应时间:", max, "ms"
    print "最小响应时间:", min, "ms"
  }'

echo "3. 缓存统计"
cache_hits=$(grep -c '"cache_hit":true' logs/app.log)
cache_total=$(grep -c '"cache_hit"' logs/app.log)
if [ $cache_total -gt 0 ]; then
  hit_rate=$(echo "scale=2; $cache_hits * 100 / $cache_total" | bc)
  echo "缓存命中率: ${hit_rate}%"
fi
```

### 紧急恢复程序

#### 服务紧急重启

```bash
#!/bin/bash
# emergency_restart.sh - 紧急重启脚本

echo "开始紧急重启程序..."

# 1. 备份当前状态
echo "备份当前配置..."
cp config.json config.json.emergency.backup
cp dictionary/rules.json dictionary/rules.json.emergency.backup

# 2. 停止服务
echo "停止服务..."
docker-compose down

# 3. 清理临时文件
echo "清理临时文件..."
rm -rf /tmp/tts_*
rm -rf cache/temp_*

# 4. 验证配置
echo "验证配置文件..."
python3 -c "import json; json.load(open('config.json'))" || {
  echo "配置文件损坏，从备份恢复..."
  cp config.json.backup config.json
}

# 5. 启动服务
echo "启动服务..."
docker-compose up -d

# 6. 等待服务就绪
echo "等待服务启动..."
sleep 10

# 7. 验证服务状态
echo "验证服务状态..."
curl -f http://localhost:8080/health || {
  echo "服务启动失败，请检查日志"
  exit 1
}

echo "紧急重启完成"
```

## 维护计划

### 日常维护任务

#### 每日检查清单

- [ ] 检查系统健康状态
- [ ] 查看错误日志
- [ ] 监控资源使用情况
- [ ] 验证备份完成
- [ ] 检查缓存命中率

#### 每周维护任务

- [ ] 清理旧日志文件
- [ ] 更新字典规则
- [ ] 性能数据分析
- [ ] 安全检查
- [ ] 配置优化评估

#### 每月维护任务

- [ ] 系统性能评估
- [ ] 容量规划检查
- [ ] 安全更新检查
- [ ] 备份策略评估
- [ ] 用户反馈收集

### 维护脚本

#### 自动维护脚本

```bash
#!/bin/bash
# maintenance.sh - 自动维护脚本

# 设置维护模式
curl -X POST http://localhost:8080/admin/maintenance/enable

# 清理旧日志
find logs/ -name "*.log.*" -mtime +30 -delete

# 清理过期缓存
curl -X POST http://localhost:8080/admin/cache/cleanup

# 优化数据库
python3 scripts/optimize_db.py

# 生成维护报告
python3 scripts/generate_report.py

# 退出维护模式
curl -X POST http://localhost:8080/admin/maintenance/disable

echo "维护完成"
```

---

本手册涵盖了 TTS 系统管理的主要方面。如有其他问题，请参考技术文档或联系技术支持团队。