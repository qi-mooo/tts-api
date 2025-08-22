# 安装指南

本指南将详细介绍如何安装和配置 TTS API 系统。

## 系统要求

### 最低要求
- **操作系统**: Linux, macOS, Windows
- **Python**: 3.8+
- **内存**: 2GB RAM
- **存储**: 5GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **Python**: 3.10+
- **内存**: 4GB+ RAM
- **存储**: 10GB+ SSD
- **Docker**: 20.10+（如果使用容器部署）

## 安装方式

### 方式一：Docker 部署（推荐）

#### 1. 使用 Docker Compose

```bash
# 克隆项目
git clone https://github.com/qi-mooo/tts-api.git
cd tts-api

# 启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps
curl http://localhost:8080/health
```

#### 2. 使用预构建镜像

```bash
# 拉取最新镜像
docker pull ghcr.io/qi-mooo/tts-api:latest

# 运行容器
docker run -d \
  --name tts-api \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -e TTS_ADMIN_PASSWORD=your-password \
  ghcr.io/qi-mooo/tts-api:latest

# 验证安装
curl http://localhost:8080/health
```

### 方式二：Python 环境安装

#### 1. 创建虚拟环境

```bash
# 克隆项目
git clone https://github.com/qi-mooo/tts-api.git
cd tts-api

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### 2. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
python3 -c "import edge_tts; print('Edge-TTS 安装成功')"
```

#### 3. 初始化语音系统

```bash
# 获取语音列表
./venv/bin/python3 scripts/install_voices.py

# 集成语音管理器
./venv/bin/python3 scripts/integrate_voice_manager.py

# 验证语音系统
./venv/bin/python3 test_voice_manager.py
```

#### 4. 配置系统

```bash
# 复制配置模板
cp config.json.template config.json

# 设置管理员密码
./venv/bin/python3 -c "
import bcrypt
password = 'your-secure-password'
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f'Password hash: {hash.decode()}')
"

# 编辑配置文件
nano config.json
```

#### 5. 启动服务

```bash
# 开发模式
./venv/bin/python3 app_enhanced.py

# 生产模式（使用 gunicorn）
./venv/bin/gunicorn -c gunicorn_config.py app_enhanced:app
```

### 方式三：快速部署脚本

```bash
# 下载部署脚本
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/deploy.sh

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 脚本会自动：
# 1. 检查系统要求
# 2. 安装 Docker（如果需要）
# 3. 下载配置文件
# 4. 启动服务
# 5. 验证安装
```

## 详细配置

### 环境变量配置

创建 `.env` 文件：

```bash
# 管理员配置
TTS_ADMIN_USERNAME=admin
TTS_ADMIN_PASSWORD=your-secure-password

# 语音配置
TTS_NARRATION_VOICE=zh-CN-YunjianNeural
TTS_DIALOGUE_VOICE=zh-CN-XiaoyiNeural
TTS_DEFAULT_SPEED=1.3

# 系统配置
TTS_HOST=0.0.0.0
TTS_PORT=8080
TTS_DEBUG=false
TTS_LOG_LEVEL=INFO
TTS_MAX_WORKERS=10

# 缓存配置
TTS_CACHE_SIZE_LIMIT=10485760
TTS_CACHE_TIME_LIMIT=1200
```

### 配置文件设置

编辑 `config.json`：

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
    "default_speed": 1.3,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200
  },
  "admin": {
    "username": "admin",
    "password_hash": "$2b$12$...",
    "session_timeout": 3600,
    "secret_key": "your-secret-key"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
```

## 验证安装

### 1. 基础功能测试

```bash
# 健康检查
curl http://localhost:8080/health

# API 状态
curl http://localhost:8080/api/status

# 语音统计
curl http://localhost:8080/api/voices/stats

# 基础 TTS 测试
curl "http://localhost:8080/api?text=测试安装" --output test.webm
```

### 2. 运行测试套件

```bash
# 语音管理器测试
./venv/bin/python3 test_voice_manager.py

# 语音 API 测试
./venv/bin/python3 test_voice_api.py

# 集成测试
./venv/bin/python3 test_integration.py --quick
```

### 3. Web 控制台测试

1. 访问 `http://localhost:8080/admin`
2. 使用配置的用户名和密码登录
3. 检查各个功能模块是否正常

## 生产环境部署

### 1. 使用 Nginx 反向代理

创建 `/etc/nginx/sites-available/tts-api`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间（用于长文本转换）
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/tts-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. 配置 HTTPS

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 系统服务配置

创建 `/etc/systemd/system/tts-api.service`：

```ini
[Unit]
Description=TTS API Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/tts-api
Environment=PATH=/opt/tts-api/venv/bin
ExecStart=/opt/tts-api/venv/bin/gunicorn -c gunicorn_config.py app_enhanced:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable tts-api
sudo systemctl start tts-api
sudo systemctl status tts-api
```

### 4. 日志轮转配置

创建 `/etc/logrotate.d/tts-api`：

```
/opt/tts-api/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload tts-api
    endscript
}
```

## 故障排除

### 常见安装问题

#### 1. Python 版本不兼容

```bash
# 检查 Python 版本
python3 --version

# 如果版本过低，升级 Python
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-pip

# macOS:
brew install python@3.10
```

#### 2. 依赖安装失败

```bash
# 升级 pip 和 setuptools
pip install --upgrade pip setuptools wheel

# 清理缓存重新安装
pip cache purge
pip install -r requirements.txt --no-cache-dir

# 如果仍然失败，尝试使用系统包管理器
# Ubuntu/Debian:
sudo apt install python3-dev build-essential
```

#### 3. 权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER .
chmod +x scripts/*.py
chmod +x scripts/*.sh

# 创建日志目录
mkdir -p logs
chmod 755 logs
```

#### 4. 端口占用

```bash
# 检查端口占用
lsof -i :8080

# 杀死占用进程
sudo kill -9 $(lsof -t -i:8080)

# 或者修改配置使用其他端口
```

#### 5. 网络连接问题

```bash
# 测试 Edge-TTS 连接
curl -I https://speech.platform.bing.com

# 如果需要代理
export https_proxy=http://proxy.example.com:8080
export http_proxy=http://proxy.example.com:8080
```

### 性能优化

#### 1. 内存优化

```json
{
  "system": {
    "max_workers": 4
  },
  "tts": {
    "cache_size_limit": 52428800
  }
}
```

#### 2. 磁盘优化

```bash
# 使用 SSD 存储
# 定期清理日志
find logs/ -name "*.log" -mtime +30 -delete

# 配置日志轮转
sudo logrotate -f /etc/logrotate.d/tts-api
```

#### 3. 网络优化

```bash
# 调整系统参数
echo 'net.core.somaxconn = 1024' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 1024' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 升级指南

### 从旧版本升级

```bash
# 备份配置和数据
cp config.json config.json.backup
cp -r data data.backup

# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 更新语音数据
./venv/bin/python3 scripts/update_voices.py

# 重启服务
sudo systemctl restart tts-api
```

### Docker 升级

```bash
# 拉取最新镜像
docker pull ghcr.io/qi-mooo/tts-api:latest

# 重启容器
docker-compose down
docker-compose up -d

# 验证升级
curl http://localhost:8080/api/status
```

## 监控和维护

### 1. 健康检查脚本

创建 `health_check.sh`：

```bash
#!/bin/bash
HEALTH_URL="http://localhost:8080/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "TTS API is healthy"
    exit 0
else
    echo "TTS API is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### 2. 监控脚本

```bash
# 添加到 crontab
*/5 * * * * /opt/tts-api/health_check.sh || systemctl restart tts-api
```

### 3. 备份脚本

```bash
#!/bin/bash
BACKUP_DIR="/backup/tts-api/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份配置和数据
cp config.json $BACKUP_DIR/
cp -r data $BACKUP_DIR/
cp -r logs $BACKUP_DIR/

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz -C /backup/tts-api $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR

# 清理旧备份（保留30天）
find /backup/tts-api -name "*.tar.gz" -mtime +30 -delete
```

---

安装完成后，请查看 [配置说明](configuration.md) 和 [API 文档](api-reference.md) 了解更多使用方法。