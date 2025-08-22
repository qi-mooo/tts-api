# TTS 系统故障排除指南

## 概述

本文档提供 TTS 系统常见问题的诊断和解决方案，帮助管理员快速定位和解决系统故障。

## 快速诊断

### 系统健康检查

首先执行基本的系统健康检查：

```bash
# 1. 检查服务状态
curl http://localhost:8080/health

# 2. 检查容器状态（Docker 环境）
docker-compose ps

# 3. 检查系统资源
free -h && df -h

# 4. 检查最近的错误日志
tail -50 logs/app.log | grep ERROR
```

### 常见问题快速检查表

| 问题类型 | 检查命令 | 正常状态 |
|----------|----------|----------|
| 服务可用性 | `curl -I http://localhost:8080/health` | HTTP/1.1 200 OK |
| Edge-TTS 连接 | `curl -I https://speech.platform.bing.com` | HTTP/2 200 |
| 磁盘空间 | `df -h /` | 使用率 < 90% |
| 内存使用 | `free -h` | 可用内存 > 500MB |
| 配置文件 | `python3 -c "import json; json.load(open('config.json'))"` | 无错误输出 |

## 服务相关问题

### 问题1：服务无法启动

#### 症状
- 访问 API 端点返回连接拒绝错误
- Docker 容器状态为 Exited
- 日志显示启动失败

#### 诊断步骤

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看启动日志
docker-compose logs tts-api

# 3. 检查端口占用
netstat -tlnp | grep 5000

# 4. 检查配置文件
python3 -c "
import json
try:
    config = json.load(open('config.json'))
    print('配置文件格式正确')
    print('TTS配置:', config.get('tts', {}))
except Exception as e:
    print(f'配置文件错误: {e}')
"
```

#### 解决方案

1. **配置文件问题**
   ```bash
   # 验证并修复配置文件
   cp config.json.template config.json
   python3 setup.py --init
   ```

2. **端口冲突**
   ```bash
   # 查找占用端口的进程
   sudo lsof -i :8080
   # 终止冲突进程或修改配置端口
   ```

3. **权限问题**
   ```bash
   # 修复文件权限
   chmod 644 config.json
   chmod 755 logs/
   chown -R $(whoami):$(whoami) .
   ```

### 问题2：Edge-TTS 连接失败

#### 症状
- API 返回 "TTS_001" 错误
- 日志显示连接超时
- 健康检查显示 Edge-TTS 不可用

#### 诊断步骤

```bash
# 1. 测试网络连接
curl -I https://speech.platform.bing.com

# 2. 检查 DNS 解析
nslookup speech.platform.bing.com

# 3. 测试网络延迟
ping -c 5 speech.platform.bing.com

# 4. 检查防火墙规则
sudo iptables -L | grep -i drop
```

#### 解决方案

1. **配置代理**
   ```bash
   # 设置环境变量
   export http_proxy=http://proxy.company.com:8080
   export https_proxy=http://proxy.company.com:8080
   ```

2. **DNS 配置**
   ```bash
   # 修改 DNS 服务器
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   ```

3. **防火墙配置**
   ```bash
   # 允许 HTTPS 出站连接
   sudo ufw allow out 443
   ```

## 性能问题

### 问题3：API 响应缓慢

#### 症状
- API 请求响应时间 > 10 秒
- 用户反馈系统卡顿
- 监控显示高延迟

#### 诊断步骤

```bash
# 1. 测试 API 响应时间
time curl "http://localhost:8080/api?text=测试文本"

# 2. 检查系统负载
uptime && iostat 1 3

# 3. 分析慢查询
grep "duration_ms" logs/app.log | awk -F'"duration_ms":' '{print $2}' | awk -F',' '$1>5000{print}'
```

#### 解决方案

1. **优化缓存配置**
   ```json
   {
     "tts": {
       "cache_size_limit": 52428800,
       "cache_time_limit": 7200
     }
   }
   ```

2. **增加并发处理**
   ```json
   {
     "system": {
       "max_workers": 8,
       "request_timeout": 60
     }
   }
   ```

### 问题4：内存不足

#### 症状
- 内存使用率持续增长
- 系统变慢或崩溃
- OOM (Out of Memory) 错误

#### 解决方案

1. **限制缓存大小**
   ```json
   {
     "cache": {
       "size_limit": 10485760,
       "max_entries": 100,
       "cleanup_interval": 300
     }
   }
   ```

2. **重启策略**
   ```yaml
   # docker-compose.yml
   services:
     tts-api:
       restart: unless-stopped
       deploy:
         resources:
           limits:
             memory: 1G
   ```

## 配置问题

### 问题5：配置文件损坏

#### 症状
- 服务启动时报配置错误
- JSON 解析失败
- 配置项缺失或格式错误

#### 解决方案

1. **从备份恢复**
   ```bash
   # 恢复最近的备份
   cp config.json.backup config.json
   
   # 或从模板重新生成
   cp config.json.template config.json
   python3 setup.py --init
   ```

2. **手动修复**
   ```bash
   # 使用 jq 验证和格式化
   jq . config.json > config.json.tmp && mv config.json.tmp config.json
   ```

### 问题6：权限配置错误

#### 症状
- 管理员无法登录
- 密码验证失败
- 会话过期异常

#### 解决方案

1. **重置管理员密码**
   ```bash
   # 使用设置脚本
   python3 setup.py --password new-password
   ```

2. **修复会话配置**
   ```json
   {
     "admin": {
       "session_timeout": 3600,
       "max_sessions": 5,
       "secure_cookies": true
     }
   }
   ```

## 存储问题

### 问题7：磁盘空间不足

#### 症状
- 日志写入失败
- 缓存无法保存
- 系统告警磁盘空间不足

#### 解决方案

1. **清理日志文件**
   ```bash
   # 清理旧日志
   find logs/ -name "*.log.*" -mtime +7 -delete
   
   # 压缩当前日志
   gzip logs/app.log
   ```

2. **清理缓存**
   ```bash
   # 清理过期缓存
   curl -X POST http://localhost:8080/admin/cache/cleanup
   
   # 完全清理缓存
   rm -rf cache/*
   ```

## 诊断工具

### 系统诊断脚本

```bash
#!/bin/bash
# system_diagnosis.sh - 系统全面诊断

echo "=== TTS 系统诊断工具 ==="
echo "开始时间: $(date)"

# 1. 基础环境检查
echo "1. 基础环境检查"
echo "操作系统: $(uname -a)"
echo "Python 版本: $(python3 --version)"
echo "Docker 版本: $(docker --version 2>/dev/null || echo '未安装')"

# 2. 服务状态检查
echo "2. 服务状态检查"
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✓ TTS API 服务正常"
else
    echo "✗ TTS API 服务异常"
fi

# 3. 系统资源检查
echo "3. 系统资源检查"
echo "CPU 使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "内存使用: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "磁盘使用: $(df -h / | awk 'NR==2{printf "%s", $5}')"

# 4. 网络连接检查
echo "4. 网络连接检查"
if curl -s -I https://speech.platform.bing.com | head -1 | grep -q "200"; then
    echo "✓ Edge-TTS 服务可达"
else
    echo "✗ Edge-TTS 服务不可达"
fi

# 5. 配置文件检查
echo "5. 配置文件检查"
if python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "✓ 配置文件格式正确"
else
    echo "✗ 配置文件格式错误"
fi

echo "诊断完成: $(date)"
```

## 紧急处理程序

### 紧急重启程序

```bash
#!/bin/bash
# emergency_restart.sh - 紧急重启程序

echo "=== TTS 系统紧急重启程序 ==="
echo "开始时间: $(date)"

# 1. 创建紧急备份
echo "1. 创建紧急备份..."
backup_dir="emergency_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $backup_dir
cp config.json $backup_dir/ 2>/dev/null
cp dictionary/rules.json $backup_dir/ 2>/dev/null
echo "备份已保存到: $backup_dir"

# 2. 停止服务
echo "2. 停止服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose down
else
    pkill -f "python.*enhanced_tts_api"
fi

# 3. 清理临时文件
echo "3. 清理临时文件..."
rm -rf /tmp/tts_*
rm -rf cache/temp_*

# 4. 检查配置文件
echo "4. 检查配置文件..."
if ! python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "配置文件损坏，从备份恢复..."
    if [ -f "config.json.backup" ]; then
        cp config.json.backup config.json
    else
        echo "警告: 没有找到配置备份文件"
    fi
fi

# 5. 启动服务
echo "5. 启动服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    nohup python3 enhanced_tts_api.py > logs/app.log 2>&1 &
fi

# 6. 等待服务就绪
echo "6. 等待服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "服务启动成功"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

# 7. 验证服务状态
echo "7. 验证服务状态..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "✓ 服务运行正常"
else
    echo "✗ 服务启动失败，请检查日志"
    tail -20 logs/app.log
    exit 1
fi

echo "紧急重启完成: $(date)"
```

---

本故障排除指南涵盖了 TTS 系统的主要问题和解决方案。如遇到未涵盖的问题，请参考系统日志进行进一步诊断。