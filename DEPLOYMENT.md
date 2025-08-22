# TTS API 部署指南

## 概述

本文档描述了如何部署和配置增强版 TTS API 系统。系统支持多种部署方式，包括 Docker、Docker Compose 和传统的 Python 环境部署。

## 系统要求

### 最低要求
- CPU: 2 核心
- 内存: 4GB RAM
- 存储: 10GB 可用空间
- 操作系统: Linux (推荐 Ubuntu 20.04+), macOS, Windows

### 推荐配置
- CPU: 4+ 核心
- 内存: 8GB+ RAM
- 存储: 20GB+ SSD
- 网络: 稳定的互联网连接（用于 Edge-TTS 服务）

## 部署方式

### 1. Docker Compose 部署（推荐）

#### 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd tts-optimization

# 2. 配置环境变量
cp .env.template .env
# 编辑 .env 文件，设置管理员密码等配置

# 3. 启动服务
docker-compose up -d

# 4. 检查服务状态
docker-compose ps
curl http://localhost:5000/health
```

#### 配置选项

```bash
# 基础服务
docker-compose up -d

# 包含 Redis 缓存
docker-compose --profile with-redis up -d

# 包含 Nginx 反向代理
docker-compose --profile with-nginx up -d

# 完整配置（包含所有服务）
docker-compose --profile with-redis --profile with-nginx up -d
```

### 2. Docker 单容器部署

```bash
# 1. 构建镜像
docker build -t tts-api .

# 2. 运行容器
docker run -d \
  --name tts-api \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.json:/app/config.json \
  -e TTS_ADMIN_PASSWORD=your-password \
  tts-api

# 3. 检查状态
docker logs tts-api
curl http://localhost:5000/health
```

### 3. Python 环境部署

#### 环境准备

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.template .env
cp config.json.template config.json
# 编辑配置文件
```

#### 启动服务

```bash
# 开发模式
export FLASK_ENV=development
python enhanced_tts_api.py

# 生产模式
gunicorn -b 0.0.0.0:5000 enhanced_tts_api:app \
  --workers 4 --timeout 120 \
  --log-level info
```

## 配置说明

### 环境变量配置

主要环境变量说明：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_ENV` | production | Flask 运行环境 |
| `TTS_ADMIN_USERNAME` | admin | 管理员用户名 |
| `TTS_ADMIN_PASSWORD` | - | 管理员密码（必须设置） |
| `TTS_LOG_LEVEL` | INFO | 日志级别 |
| `TTS_MAX_WORKERS` | 10 | 最大工作线程数 |
| `TTS_CACHE_SIZE_LIMIT` | 10485760 | 缓存大小限制（字节） |

### 配置文件

#### config.json 配置

```json
{
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.2,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "admin": {
    "username": "admin",
    "password_hash": "",
    "session_timeout": 3600
  },
  "dictionary": {
    "enabled": true,
    "rules_file": "dictionary/rules.json"
  },
  "system": {
    "max_workers": 10,
    "health_check_interval": 30,
    "restart_timeout": 60
  }
}
```

## 安全配置

### 1. 管理员密码设置

```bash
# 方法1：环境变量
export TTS_ADMIN_PASSWORD=your-secure-password

# 方法2：使用 bcrypt 生成密码哈希
python3 -c "
import bcrypt
password = 'your-password'
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hash.decode('utf-8'))
"
```

### 2. HTTPS 配置

使用 Nginx 反向代理配置 HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### 3. 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

## 监控和日志

### 1. 健康检查

```bash
# 基本健康检查
curl http://localhost:5000/health

# 详细状态信息
curl http://localhost:5000/health?detailed=true
```

### 2. 日志管理

```bash
# 查看应用日志
tail -f logs/app.log

# Docker 容器日志
docker logs -f tts-api

# Docker Compose 日志
docker-compose logs -f tts-api
```

### 3. 性能监控

推荐使用 Prometheus + Grafana 进行监控：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tts-api'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

## 故障排除

### 常见问题

#### 1. Edge-TTS 连接失败

```bash
# 检查网络连接
curl -I https://speech.platform.bing.com

# 检查 DNS 解析
nslookup speech.platform.bing.com

# 解决方案：配置代理或使用备用语音
```

#### 2. 内存不足

```bash
# 检查内存使用
free -h
docker stats

# 解决方案：
# - 减少 max_workers 配置
# - 降低 cache_size_limit
# - 增加系统内存
```

#### 3. 权限问题

```bash
# 检查文件权限
ls -la logs/
ls -la config.json

# 修复权限
chmod 755 logs/
chmod 644 config.json
```

### 日志分析

#### 错误日志示例

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "ERROR",
  "module": "tts_service",
  "message": "Edge-TTS 服务不可用",
  "error_code": "TTS_001",
  "request_id": "req_123456",
  "details": {
    "voice": "zh-CN-YunjianNeural",
    "text_length": 100
  }
}
```

## 性能优化

### 1. 缓存优化

```json
{
  "tts": {
    "cache_size_limit": 52428800,  // 50MB
    "cache_time_limit": 3600       // 1小时
  }
}
```

### 2. 并发优化

```bash
# Gunicorn 配置
gunicorn -b 0.0.0.0:5000 enhanced_tts_api:app \
  --workers 4 \
  --worker-class sync \
  --worker-connections 1000 \
  --timeout 120 \
  --keepalive 5
```

### 3. 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
sysctl -p
```

## 备份和恢复

### 1. 数据备份

```bash
# 备份配置文件
tar -czf backup-$(date +%Y%m%d).tar.gz \
  config.json \
  dictionary/rules.json \
  logs/

# 备份 Docker 卷
docker run --rm -v tts_logs:/data -v $(pwd):/backup \
  alpine tar czf /backup/logs-backup.tar.gz -C /data .
```

### 2. 恢复流程

```bash
# 恢复配置
tar -xzf backup-20240101.tar.gz

# 重启服务
docker-compose restart
```

## 升级指南

### 1. 版本升级

```bash
# 1. 备份当前配置
cp config.json config.json.backup

# 2. 停止服务
docker-compose down

# 3. 更新代码
git pull origin main

# 4. 重新构建镜像
docker-compose build

# 5. 启动服务
docker-compose up -d

# 6. 验证升级
curl http://localhost:5000/health
```

### 2. 配置迁移

升级时可能需要更新配置文件格式，请参考 `CHANGELOG.md` 中的迁移指南。

## 支持和联系

如遇到问题，请：

1. 查看日志文件：`logs/app.log`
2. 检查健康状态：`/health` 端点
3. 参考故障排除章节
4. 提交 Issue 到项目仓库

---

更多详细信息请参考项目文档和源代码注释。