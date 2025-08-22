# 部署指南

本指南详细介绍如何在不同环境中部署 TTS API 系统。

## 部署方式概览

| 部署方式 | 适用场景 | 复杂度 | 推荐指数 |
|----------|----------|--------|----------|
| Docker Compose | 开发、测试、小规模生产 | 低 | ⭐⭐⭐⭐⭐ |
| GitHub Packages | 快速部署、CI/CD | 低 | ⭐⭐⭐⭐⭐ |
| 手动部署 | 自定义环境、学习 | 中 | ⭐⭐⭐ |
| Kubernetes | 大规模生产、微服务 | 高 | ⭐⭐⭐⭐ |

## Docker Compose 部署（推荐）

### 基础部署

```bash
# 1. 克隆项目
git clone https://github.com/qi-mooo/tts-api.git
cd tts-api

# 2. 配置环境变量
cp .env.template .env
nano .env

# 3. 启动服务
docker-compose up -d

# 4. 验证部署
curl http://localhost:8080/health
```

### 环境变量配置

编辑 `.env` 文件：

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
TTS_MAX_WORKERS=10

# 缓存配置
TTS_CACHE_SIZE_LIMIT=10485760
TTS_CACHE_TIME_LIMIT=1200
```

### 高级 Docker Compose 配置

```yaml
version: '3.8'

services:
  tts-api:
    image: ghcr.io/qi-mooo/tts-api:latest
    container_name: tts-api
    ports:
      - "8080:8080"
    environment:
      - TTS_ADMIN_PASSWORD=${TTS_ADMIN_PASSWORD}
      - TTS_NARRATION_VOICE=${TTS_NARRATION_VOICE}
      - TTS_DIALOGUE_VOICE=${TTS_DIALOGUE_VOICE}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config.json:/app/config.json:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: tts-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - tts-api
    restart: unless-stopped
    profiles:
      - with-nginx

  redis:
    image: redis:alpine
    container_name: tts-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    profiles:
      - with-redis

volumes:
  redis_data:
```

### 启动不同配置

```bash
# 基础服务
docker-compose up -d

# 包含 Nginx
docker-compose --profile with-nginx up -d

# 包含 Redis 和 Nginx
docker-compose --profile with-redis --profile with-nginx up -d
```

## GitHub Packages 部署

### 快速部署

```bash
# 1. 创建部署目录
mkdir tts-api-deploy
cd tts-api-deploy

# 2. 下载配置文件
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/.env.template

# 3. 配置环境
cp .env.template .env
nano .env

# 4. 启动服务
docker-compose up -d

# 5. 验证部署
curl http://localhost:8080/health
```

### 自动部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash
set -e

echo "=== TTS API 自动部署脚本 ==="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "请重新登录以应用 Docker 权限"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose 未安装，正在安装..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 创建部署目录
DEPLOY_DIR="/opt/tts-api"
sudo mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# 下载配置文件
echo "下载配置文件..."
sudo curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/docker-compose.yml
sudo curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/.env.template

# 配置环境变量
if [ ! -f .env ]; then
    sudo cp .env.template .env
    echo "请编辑 .env 文件设置管理员密码"
    echo "sudo nano $DEPLOY_DIR/.env"
    exit 1
fi

# 启动服务
echo "启动 TTS API 服务..."
sudo docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 验证部署
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ TTS API 部署成功！"
    echo "访问地址: http://$(hostname -I | awk '{print $1}'):8080"
    echo "管理控制台: http://$(hostname -I | awk '{print $1}'):8080/admin"
else
    echo "❌ 部署失败，请检查日志："
    sudo docker-compose logs
fi
```

## 手动部署

### 系统准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip nginx supervisor

# CentOS/RHEL
sudo yum install python3 python3-pip nginx supervisor

# macOS
brew install python3 nginx supervisor
```

### 应用部署

```bash
# 1. 创建应用用户
sudo useradd -r -s /bin/false tts-api

# 2. 创建应用目录
sudo mkdir -p /opt/tts-api
sudo chown tts-api:tts-api /opt/tts-api

# 3. 切换到应用用户
sudo -u tts-api -s

# 4. 克隆项目
cd /opt/tts-api
git clone https://github.com/qi-mooo/tts-api.git .

# 5. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt

# 7. 初始化语音系统
./venv/bin/python3 scripts/install_voices.py

# 8. 配置系统
cp config.json.template config.json
nano config.json

# 9. 测试启动
./venv/bin/python3 app_enhanced.py
```

### Supervisor 配置

创建 `/etc/supervisor/conf.d/tts-api.conf`：

```ini
[program:tts-api]
command=/opt/tts-api/venv/bin/gunicorn -c gunicorn_config.py app_enhanced:app
directory=/opt/tts-api
user=tts-api
group=tts-api
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/tts-api.log
environment=PATH="/opt/tts-api/venv/bin"
```

启动服务：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start tts-api
sudo supervisorctl status tts-api
```

### Nginx 配置

创建 `/etc/nginx/sites-available/tts-api`：

```nginx
upstream tts_api {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 配置
    ssl_certificate /etc/ssl/certs/tts-api.crt;
    ssl_certificate_key /etc/ssl/private/tts-api.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # 日志
    access_log /var/log/nginx/tts-api.access.log;
    error_log /var/log/nginx/tts-api.error.log;

    # 主要配置
    location / {
        proxy_pass http://tts_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        proxy_pass http://tts_api;
        access_log off;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/tts-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Kubernetes 部署

### 基础 Kubernetes 配置

创建 `k8s/namespace.yaml`：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tts-api
```

创建 `k8s/configmap.yaml`：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tts-api-config
  namespace: tts-api
data:
  TTS_HOST: "0.0.0.0"
  TTS_PORT: "8080"
  TTS_DEBUG: "false"
  TTS_MAX_WORKERS: "10"
  TTS_NARRATION_VOICE: "zh-CN-YunjianNeural"
  TTS_DIALOGUE_VOICE: "zh-CN-XiaoyiNeural"
  TTS_DEFAULT_SPEED: "1.3"
```

创建 `k8s/secret.yaml`：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tts-api-secret
  namespace: tts-api
type: Opaque
data:
  TTS_ADMIN_PASSWORD: eW91ci1zZWN1cmUtcGFzc3dvcmQ=  # base64 encoded
```

创建 `k8s/deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tts-api
  namespace: tts-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tts-api
  template:
    metadata:
      labels:
        app: tts-api
    spec:
      containers:
      - name: tts-api
        image: ghcr.io/qi-mooo/tts-api:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: tts-api-config
        - secretRef:
            name: tts-api-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
```

创建 `k8s/service.yaml`：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: tts-api-service
  namespace: tts-api
spec:
  selector:
    app: tts-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

创建 `k8s/ingress.yaml`：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tts-api-ingress
  namespace: tts-api
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - tts-api.your-domain.com
    secretName: tts-api-tls
  rules:
  - host: tts-api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tts-api-service
            port:
              number: 80
```

### 部署到 Kubernetes

```bash
# 应用配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n tts-api
kubectl get services -n tts-api
kubectl get ingress -n tts-api

# 查看日志
kubectl logs -f deployment/tts-api -n tts-api
```

## 云平台部署

### AWS ECS 部署

创建 `aws/task-definition.json`：

```json
{
  "family": "tts-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "tts-api",
      "image": "ghcr.io/qi-mooo/tts-api:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "TTS_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "TTS_PORT",
          "value": "8080"
        }
      ],
      "secrets": [
        {
          "name": "TTS_ADMIN_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:tts-api-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/tts-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Google Cloud Run 部署

```bash
# 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT-ID/tts-api

# 部署到 Cloud Run
gcloud run deploy tts-api \
  --image gcr.io/PROJECT-ID/tts-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars TTS_HOST=0.0.0.0,TTS_PORT=8080 \
  --set-secrets TTS_ADMIN_PASSWORD=tts-api-password:latest \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

## 监控和维护

### 健康检查

创建 `scripts/health_check.sh`：

```bash
#!/bin/bash
HEALTH_URL="http://localhost:8080/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "$(date): TTS API is healthy"
    exit 0
else
    echo "$(date): TTS API is unhealthy (HTTP $RESPONSE)"
    # 可以添加重启逻辑
    # systemctl restart tts-api
    exit 1
fi
```

### 监控脚本

创建 `scripts/monitor.sh`：

```bash
#!/bin/bash
LOG_FILE="/var/log/tts-api-monitor.log"

# 检查服务状态
check_service() {
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        echo "$(date): Service OK" >> $LOG_FILE
    else
        echo "$(date): Service DOWN - Restarting..." >> $LOG_FILE
        systemctl restart tts-api
        sleep 30
        if curl -f http://localhost:8080/health > /dev/null 2>&1; then
            echo "$(date): Service restarted successfully" >> $LOG_FILE
        else
            echo "$(date): Service restart failed" >> $LOG_FILE
        fi
    fi
}

# 检查磁盘空间
check_disk() {
    USAGE=$(df /opt/tts-api | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $USAGE -gt 80 ]; then
        echo "$(date): Disk usage high: ${USAGE}%" >> $LOG_FILE
        # 清理日志
        find /opt/tts-api/logs -name "*.log" -mtime +7 -delete
    fi
}

# 检查内存使用
check_memory() {
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
    if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
        echo "$(date): Memory usage high: ${MEMORY_USAGE}%" >> $LOG_FILE
    fi
}

check_service
check_disk
check_memory
```

### 自动备份

创建 `scripts/backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/backup/tts-api"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/tts-api-backup-$DATE.tar.gz"

mkdir -p $BACKUP_DIR

# 备份配置和数据
tar -czf $BACKUP_FILE \
  -C /opt/tts-api \
  config.json \
  data/ \
  logs/

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup completed: $BACKUP_FILE"
```

### Crontab 配置

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下任务
# 每5分钟检查服务状态
*/5 * * * * /opt/tts-api/scripts/health_check.sh

# 每小时运行监控脚本
0 * * * * /opt/tts-api/scripts/monitor.sh

# 每天凌晨2点备份
0 2 * * * /opt/tts-api/scripts/backup.sh

# 每周日凌晨3点更新语音列表
0 3 * * 0 cd /opt/tts-api && ./venv/bin/python3 scripts/update_voices.py
```

## 故障排除

### 常见部署问题

#### 1. 容器启动失败

```bash
# 查看容器日志
docker logs tts-api

# 检查配置
docker exec -it tts-api cat /app/config.json

# 检查环境变量
docker exec -it tts-api env | grep TTS_
```

#### 2. 服务无法访问

```bash
# 检查端口绑定
docker port tts-api

# 检查防火墙
sudo ufw status
sudo firewall-cmd --list-ports

# 检查网络连接
curl -v http://localhost:8080/health
```

#### 3. 性能问题

```bash
# 检查资源使用
docker stats tts-api

# 检查系统资源
htop
df -h
free -h

# 调整配置
# 减少 max_workers 或增加内存限制
```

#### 4. SSL/TLS 问题

```bash
# 检查证书
openssl x509 -in /etc/ssl/certs/tts-api.crt -text -noout

# 测试 SSL 连接
openssl s_client -connect your-domain.com:443

# 更新证书（Let's Encrypt）
sudo certbot renew
```

### 性能调优

#### 1. 容器资源限制

```yaml
# Docker Compose
services:
  tts-api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### 2. Nginx 优化

```nginx
# 增加工作进程
worker_processes auto;
worker_connections 1024;

# 启用 gzip 压缩
gzip on;
gzip_types text/plain application/json application/javascript text/css;

# 缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=tts_cache:10m max_size=1g inactive=60m;
```

#### 3. 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 1024" >> /etc/sysctl.conf
sysctl -p
```

---

部署完成后，请查看 [配置说明](configuration.md) 和 [API 文档](api-reference.md) 了解更多使用方法。