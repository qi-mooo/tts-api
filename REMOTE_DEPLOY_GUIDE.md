# 远程服务器部署指南

## 自动部署（推荐）

运行自动部署脚本：

```bash
./remote_deploy.sh
```

## 手动部署步骤

如果自动部署脚本遇到问题，可以按照以下步骤手动部署：

### 1. 连接到服务器

```bash
ssh root@10.0.0.129
```

### 2. 准备项目目录

```bash
# 创建项目目录
mkdir -p /vol1/1000/docker/tts-api
cd /vol1/1000/docker/tts-api
```

### 3. 克隆或更新代码

如果是首次部署：
```bash
git clone https://github.com/qi-mooo/tts-api.git .
```

如果是更新部署：
```bash
# 停止现有服务
docker-compose down 2>/dev/null || true

# 更新代码
git fetch origin
git reset --hard origin/main
git clean -fd
```

### 4. 准备配置文件

```bash
# 创建环境配置文件
cp .env.template .env

# 编辑配置（可选）
nano .env
```

确保 `.env` 文件中的端口配置正确：
```
TTS_PORT=8080
TTS_ADMIN_USERNAME=admin
TTS_ADMIN_PASSWORD=admin123
```

### 5. 创建必要目录

```bash
mkdir -p logs
mkdir -p audio_cache
mkdir -p database
```

### 6. 构建和启动服务

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 7. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 检查日志
docker-compose logs -f

# 测试健康检查
curl http://localhost:8080/health
```

## 服务访问

部署成功后，可以通过以下地址访问服务：

- **主服务**: http://10.0.0.129:8080
- **健康检查**: http://10.0.0.129:8080/health
- **管理面板**: http://10.0.0.129:8080/admin
- **API 状态**: http://10.0.0.129:8080/api/status

## 常用管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新服务
git pull && docker-compose up -d --build

# 查看资源使用
docker stats
```

## 故障排除

### 端口被占用

```bash
# 检查端口占用
netstat -tulpn | grep :8080
lsof -i :8080

# 停止占用端口的进程
sudo kill $(lsof -t -i:8080)
```

### 服务启动失败

```bash
# 查看详细日志
docker-compose logs --tail=50

# 检查容器状态
docker ps -a

# 重新构建镜像
docker-compose build --no-cache
docker-compose up -d
```

### 磁盘空间不足

```bash
# 清理 Docker 资源
docker system prune -f

# 清理旧镜像
docker image prune -a -f

# 检查磁盘使用
df -h
```

## 配置优化

### 生产环境配置

编辑 `.env` 文件：

```bash
# 生产环境设置
FLASK_ENV=production
FLASK_DEBUG=0
TTS_LOG_LEVEL=INFO

# 性能优化
TTS_CACHE_SIZE_LIMIT=52428800  # 50MB
TTS_CACHE_TIME_LIMIT=3600      # 1小时

# 安全设置
TTS_ADMIN_PASSWORD=your_secure_password_here
```

### 资源限制

编辑 `docker-compose.yml` 添加资源限制：

```yaml
services:
  tts-api:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

## 监控和维护

### 设置日志轮转

```bash
# 创建 logrotate 配置
sudo tee /etc/logrotate.d/tts-api << EOF
/vol1/1000/docker/tts-api/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

### 设置自动重启

```bash
# 添加到 crontab
crontab -e

# 添加以下行（每天凌晨2点重启服务）
0 2 * * * cd /vol1/1000/docker/tts-api && docker-compose restart
```

### 健康检查脚本

创建健康检查脚本：

```bash
cat > /vol1/1000/docker/tts-api/health_check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8080/health &> /dev/null; then
    echo "$(date): TTS API 服务异常，尝试重启..."
    cd /vol1/1000/docker/tts-api
    docker-compose restart
fi
EOF

chmod +x /vol1/1000/docker/tts-api/health_check.sh

# 添加到 crontab（每5分钟检查一次）
echo "*/5 * * * * /vol1/1000/docker/tts-api/health_check.sh" | crontab -
```

## 备份和恢复

### 备份配置

```bash
# 创建备份目录
mkdir -p /vol1/1000/backup/tts-api

# 备份配置文件
tar -czf /vol1/1000/backup/tts-api/config-$(date +%Y%m%d).tar.gz \
    .env config.json dictionary/rules.json

# 备份数据库（如果有）
cp -r database /vol1/1000/backup/tts-api/database-$(date +%Y%m%d)
```

### 恢复配置

```bash
# 恢复配置文件
cd /vol1/1000/docker/tts-api
tar -xzf /vol1/1000/backup/tts-api/config-YYYYMMDD.tar.gz

# 重启服务
docker-compose restart
```