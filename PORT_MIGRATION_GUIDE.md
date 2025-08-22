# 端口配置迁移指南

## 概述

本文档描述了 TTS API 项目从端口 5000 迁移到端口 8080 的变更内容和迁移步骤。

## 变更摘要

### 主要变更
- **默认端口**: 从 5000 更改为 8080
- **Docker 配置**: 统一容器内外端口为 8080
- **文档更新**: 所有示例和说明使用端口 8080
- **配置文件**: 默认配置统一为端口 8080

### 影响范围
- Docker 部署配置
- 应用配置文件
- 文档和示例
- 测试脚本
- 部署脚本

## 迁移步骤

### 1. 现有部署迁移

#### Docker Compose 部署

如果您使用 Docker Compose 部署：

```bash
# 1. 停止现有服务
docker-compose down

# 2. 更新代码
git pull origin main

# 3. 更新环境配置
sed -i 's/TTS_PORT=5000/TTS_PORT=8080/g' .env
sed -i 's/SYSTEM_PORT=5000/SYSTEM_PORT=8080/g' .env

# 4. 重新构建和启动
docker-compose build
docker-compose up -d

# 5. 验证服务
curl http://localhost:8080/health
```

#### Docker 直接部署

如果您使用 Docker 直接部署：

```bash
# 1. 停止现有容器
docker stop tts-api
docker rm tts-api

# 2. 重新构建镜像
docker build -t tts-api .

# 3. 启动新容器（注意端口映射变更）
docker run -d \
  --name tts-api \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.json:/app/config.json \
  tts-api
```

#### 本地 Python 部署

如果您使用本地 Python 部署：

```bash
# 1. 更新代码
git pull origin main

# 2. 更新配置文件
# 编辑 config.json，将 system.port 改为 8080
sed -i 's/"port": 5000/"port": 8080/g' config.json

# 3. 重启服务
./venv/bin/python3 app_enhanced.py
```

### 2. 反向代理配置更新

#### Nginx 配置

如果您使用 Nginx 反向代理，需要更新配置：

```nginx
# 旧配置
upstream tts-api {
    server localhost:5000;
}

# 新配置
upstream tts-api {
    server localhost:8080;
}
```

更新后重新加载 Nginx：
```bash
sudo nginx -t
sudo nginx -s reload
```

#### Apache 配置

如果您使用 Apache 反向代理：

```apache
# 旧配置
ProxyPass /api/ http://localhost:5000/
ProxyPassReverse /api/ http://localhost:5000/

# 新配置
ProxyPass /api/ http://localhost:8080/
ProxyPassReverse /api/ http://localhost:8080/
```

### 3. 防火墙和安全组配置

#### 防火墙规则

```bash
# 移除旧端口规则
sudo ufw delete allow 5000

# 添加新端口规则
sudo ufw allow 8080
```

#### 云服务安全组

如果在云服务上部署，需要更新安全组规则：
- 移除端口 5000 的入站规则
- 添加端口 8080 的入站规则

### 4. 监控和健康检查更新

#### 监控系统

更新监控系统中的端点配置：

```yaml
# 旧配置
- url: http://localhost:5000/health
  
# 新配置  
- url: http://localhost:8080/health
```

#### 健康检查脚本

更新健康检查脚本：

```bash
# 旧脚本
curl -f http://localhost:5000/health

# 新脚本
curl -f http://localhost:8080/health
```

## 向后兼容性

### 环境变量支持

系统仍然支持通过环境变量覆盖端口配置：

```bash
# 使用环境变量指定端口
export TTS_PORT=8080
export SYSTEM_PORT=8080

# 或在 .env 文件中设置
echo "TTS_PORT=8080" >> .env
echo "SYSTEM_PORT=8080" >> .env
```

### 配置文件兼容性

现有的 `config.json` 文件会自动使用新的默认端口，但您也可以手动指定：

```json
{
  "system": {
    "port": 8080,
    "host": "0.0.0.0"
  }
}
```

## 验证迁移

### 1. 服务可用性检查

```bash
# 检查服务是否在新端口运行
curl -I http://localhost:8080/health

# 预期响应
HTTP/1.1 200 OK
Content-Type: application/json
```

### 2. API 功能测试

```bash
# 测试 TTS API
curl -X GET "http://localhost:8080/api?text=测试&speed=1.2"

# 测试管理界面
curl -I http://localhost:8080/admin
```

### 3. 端口配置一致性验证

使用项目提供的验证脚本：

```bash
./venv/bin/python3 verify_port_consistency.py
```

预期输出：
```
✅ 所有端口配置都正确！
一致性率: 100.0%
```

## 故障排除

### 常见问题

#### 1. 端口被占用

**问题**: 启动时提示端口 8080 被占用

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8080

# 停止占用进程
sudo kill $(lsof -t -i:8080)

# 或使用不同端口
export TTS_PORT=8081
```

#### 2. 旧端口仍在使用

**问题**: 服务仍在端口 5000 运行

**解决方案**:
```bash
# 检查配置文件
grep -r "5000" config.json .env

# 更新配置
sed -i 's/5000/8080/g' config.json
sed -i 's/5000/8080/g' .env

# 重启服务
```

#### 3. Docker 容器端口映射错误

**问题**: Docker 容器内外端口不一致

**解决方案**:
```bash
# 检查容器端口映射
docker port tts-api

# 重新创建容器
docker-compose down
docker-compose up -d
```

#### 4. 反向代理连接失败

**问题**: Nginx/Apache 无法连接到后端服务

**解决方案**:
```bash
# 检查后端服务状态
curl http://localhost:8080/health

# 检查代理配置
nginx -t
# 或
apache2ctl configtest

# 重新加载配置
sudo nginx -s reload
# 或
sudo systemctl reload apache2
```

### 日志分析

#### 查看服务日志

```bash
# Docker Compose 部署
docker-compose logs -f tts-api

# 本地部署
tail -f logs/app.log

# 查找端口相关错误
grep -i "port\|bind\|address" logs/app.log
```

#### 常见错误信息

1. **Address already in use**: 端口被占用
2. **Connection refused**: 服务未启动或端口错误
3. **Permission denied**: 权限不足（通常是绑定 1024 以下端口）

## 回滚步骤

如果迁移后遇到问题，可以临时回滚到旧端口：

### 1. 快速回滚

```bash
# 设置环境变量使用旧端口
export TTS_PORT=5000
export SYSTEM_PORT=5000

# 重启服务
docker-compose restart
# 或
./venv/bin/python3 app_enhanced.py
```

### 2. 完整回滚

```bash
# 1. 检出迁移前的版本
git log --oneline | grep -B5 -A5 "端口"
git checkout <commit_hash>

# 2. 重新部署
docker-compose down
docker-compose build
docker-compose up -d
```

## 最佳实践

### 1. 分阶段迁移

对于生产环境，建议分阶段迁移：

1. **测试环境**: 先在测试环境验证
2. **预生产环境**: 在预生产环境测试完整流程
3. **生产环境**: 在维护窗口期间迁移

### 2. 监控和告警

迁移期间加强监控：

```bash
# 监控脚本示例
#!/bin/bash
while true; do
    if ! curl -f http://localhost:8080/health &>/dev/null; then
        echo "$(date): 服务异常，尝试重启..."
        docker-compose restart
    fi
    sleep 30
done
```

### 3. 文档更新

更新相关文档：
- API 文档中的端点地址
- 部署文档中的端口配置
- 监控文档中的检查地址

## 支持和帮助

如果在迁移过程中遇到问题：

1. **查看日志**: 检查应用和系统日志
2. **验证配置**: 使用 `verify_port_consistency.py` 脚本
3. **测试连接**: 使用 `test_quick.py` 脚本测试服务
4. **检查文档**: 参考 `REMOTE_DEPLOY_GUIDE.md`

## 附录

### A. 配置文件模板

#### .env 文件模板
```bash
TTS_PORT=8080
TTS_ADMIN_USERNAME=admin
TTS_ADMIN_PASSWORD=admin123
TTS_NARRATION_VOICE=zh-CN-YunjianNeural
TTS_DIALOGUE_VOICE=zh-CN-XiaoyiNeural
TTS_DEFAULT_SPEED=1.2
TTS_LOG_LEVEL=INFO
FLASK_ENV=production
FLASK_DEBUG=0
```

#### config.json 文件模板
```json
{
  "system": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "max_workers": 10
  },
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
  }
}
```

### B. 验证脚本

#### 端口连通性测试
```bash
#!/bin/bash
# port_test.sh

PORT=8080
HOST=localhost

echo "测试端口 $HOST:$PORT 连通性..."

if nc -z $HOST $PORT; then
    echo "✅ 端口 $PORT 可访问"
else
    echo "❌ 端口 $PORT 不可访问"
    exit 1
fi

# 测试 HTTP 响应
if curl -f http://$HOST:$PORT/health &>/dev/null; then
    echo "✅ HTTP 服务正常"
else
    echo "❌ HTTP 服务异常"
    exit 1
fi

echo "🎉 端口迁移验证通过！"
```

### C. 自动化迁移脚本

```bash
#!/bin/bash
# migrate_port.sh

set -e

echo "🚀 开始端口迁移..."

# 1. 备份配置
echo "📦 备份当前配置..."
mkdir -p backup
cp .env backup/.env.backup 2>/dev/null || true
cp config.json backup/config.json.backup 2>/dev/null || true

# 2. 停止服务
echo "🛑 停止现有服务..."
docker-compose down 2>/dev/null || true

# 3. 更新配置
echo "🔧 更新端口配置..."
sed -i.bak 's/TTS_PORT=5000/TTS_PORT=8080/g' .env 2>/dev/null || true
sed -i.bak 's/"port": 5000/"port": 8080/g' config.json 2>/dev/null || true

# 4. 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 5. 验证迁移
echo "✅ 验证迁移..."
sleep 10
if curl -f http://localhost:8080/health &>/dev/null; then
    echo "🎉 端口迁移成功！"
    echo "服务现在运行在端口 8080"
else
    echo "❌ 迁移失败，正在回滚..."
    docker-compose down
    cp backup/.env.backup .env 2>/dev/null || true
    cp backup/config.json.backup config.json 2>/dev/null || true
    docker-compose up -d
    exit 1
fi
```

---

**注意**: 本迁移指南适用于 TTS API v2.0.0 及以上版本。如有疑问，请参考项目文档或联系技术支持。