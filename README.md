# TTS API （该项目基于ai开发）

一个功能完善的文本转语音（TTS）API 系统，基于 Microsoft Edge-TTS 服务，提供了完整的错误处理、Web 管理控制台、字典功能、结构化日志和系统监控等特性。

## 🚀 特性

### 核心功能
- **文本转语音**: 基于 Microsoft Edge-TTS 的高质量语音合成
- **多语音支持**: 支持旁白和对话不同语音配置
- **智能缓存**: 音频缓存系统，提升响应速度
- **文本预处理**: 字典服务支持发音替换和内容净化

### 系统增强
- **错误处理**: 完善的异常处理机制和重试策略
- **Web 控制台**: 响应式管理界面，支持配置管理和系统监控
- **结构化日志**: 多级别日志记录，支持轮转和归档
- **健康检查**: 系统状态监控和服务可用性检测
- **优雅重启**: 无损服务重启和配置热重载

### 部署支持
- **Docker 支持**: 完整的容器化部署方案
- **Docker Compose**: 一键启动完整服务栈
- **Nginx 集成**: 反向代理和负载均衡配置
- **环境配置**: 灵活的环境变量和配置文件管理

## 📋 系统要求

### 最低要求
- Python 3.8+
- 2GB RAM
- 5GB 存储空间
- 稳定的网络连接

### 推荐配置
- Python 3.10+
- 4GB+ RAM
- 10GB+ SSD 存储
- Docker 20.10+

## 🛠️ 快速开始

### 方式一：GitHub Packages 快速部署（推荐）

```bash
# 1. 下载部署脚本
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/deploy.sh
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/docker-compose.prod.yml
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/config.json.template

# 2. 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 3. 访问服务
curl http://localhost:5000/health
```

### 方式二：Docker Compose 开发环境

```bash
# 1. 克隆项目
git clone git@github.com:qi-mooo/tts-api.git
cd tts-api

# 2. 配置环境
cp .env.template .env
# 编辑 .env 文件，设置管理员密码

# 3. 启动服务
docker-compose up -d

# 4. 访问服务
curl http://localhost:5000/health
```

### 方式三：Python 环境

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化配置
python3 setup.py --init
python3 setup.py --password your-password

# 4. 启动服务
python3 enhanced_tts_api.py
```

### 方式四：使用 Makefile

```bash
# 快速开发环境设置
make quick-start

# 快速 Docker 部署
make quick-docker

# 查看所有可用命令
make help
```

## 🔧 配置说明

### 环境变量配置

主要环境变量：

```bash
# 管理员配置
TTS_ADMIN_USERNAME=admin
TTS_ADMIN_PASSWORD=your-password

# 语音配置
TTS_NARRATION_VOICE=zh-CN-YunjianNeural
TTS_DIALOGUE_VOICE=zh-CN-XiaoyiNeural
TTS_DEFAULT_SPEED=1.2

# 系统配置
TTS_LOG_LEVEL=INFO
TTS_MAX_WORKERS=10
```

### 配置文件

`config.json` 示例：

```json
{
  "tts": {
    "narration_voice": "zh-CN-YunjianNeural",
    "dialogue_voice": "zh-CN-XiaoyiNeural",
    "default_speed": 1.2,
    "cache_size_limit": 10485760,
    "cache_time_limit": 1200
  },
  "admin": {
    "username": "admin",
    "password_hash": "$2b$12$...",
    "session_timeout": 3600
  }
}
```

## 📚 API 文档

### 文本转语音 API

```bash
# 基本用法
GET /api?text=你好世界

# 自定义语速
GET /api?text=你好世界&speed=1.5

# 自定义语音
GET /api?text=你好世界&narr=zh-CN-YunjianNeural&dlg=zh-CN-XiaoyiNeural

# 统一语音
GET /api?text=你好世界&all=zh-CN-YunjianNeural
```

### 管理 API

```bash
# 健康检查
GET /health

# 管理控制台
GET /admin

# 系统重启
POST /admin/restart
```

## 🎛️ Web 管理控制台

访问 `http://localhost:5000/admin` 进入管理控制台：

### 功能特性
- **配置管理**: 实时修改语音参数和系统设置
- **字典管理**: 添加、编辑、删除发音规则和内容过滤
- **系统监控**: 查看服务状态、性能指标和日志
- **语音预览**: 测试配置效果
- **优雅重启**: 无损重启服务

### 登录认证
- 默认用户名：`admin`
- 密码：通过环境变量或配置文件设置

## 📊 监控和日志

### 健康检查

```bash
# 基本健康检查
curl http://localhost:5000/health

# 详细状态信息
curl "http://localhost:5000/health?detailed=true"
```

### 日志管理

```bash
# 查看应用日志
tail -f logs/app.log

# 使用 Makefile
make logs

# Docker 环境
docker-compose logs -f tts-api
```

### 性能监控

日志包含详细的性能指标：

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "module": "tts_service",
  "message": "TTS 请求处理成功",
  "request_id": "req_12345",
  "total_duration_ms": 1500,
  "cache_stats": {
    "hit_rate": 0.85,
    "cache_size": 15
  }
}
```

## 🔒 安全配置

### 管理员密码设置

```bash
# 使用设置脚本
python3 setup.py --password your-secure-password

# 使用 Makefile
make password PASSWORD=your-secure-password

# 使用 bcrypt 生成哈希
python3 -c "
import bcrypt
password = 'your-password'
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hash.decode('utf-8'))
"
```

### HTTPS 配置

使用 Nginx 反向代理配置 HTTPS，参考 `nginx.conf` 文件。

## 🧪 测试

### 运行测试

```bash
# 单元测试
make test

# 测试覆盖率
make test-coverage

# 使用 Python 直接运行
./venv/bin/python3 -m unittest discover tests -v
```

### 集成测试

```bash
# 测试 API 端点
python3 test_enhanced_api_simple.py

# 测试管理界面
python3 test_admin_interface.py

# 测试音频缓存
python3 test_audio_cache_integration.py
```

## 🚀 部署

### GitHub Packages 部署（推荐）

使用预构建的 Docker 镜像快速部署：

```bash
# 1. 使用快速部署脚本
./deploy.sh

# 2. 或手动部署
docker pull ghcr.io/qi-mooo/tts-api:latest
docker-compose -f docker-compose.prod.yml up -d

# 3. 更新到最新版本
docker pull ghcr.io/qi-mooo/tts-api:latest
docker-compose -f docker-compose.prod.yml up -d
```

### 本地构建部署

```bash
# 构建镜像
docker build -t tts-api .

# 运行容器
docker run -d \
  --name tts-api \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -e TTS_ADMIN_PASSWORD=your-password \
  tts-api
```

### Docker Compose 部署

```bash
# 基础服务
docker-compose up -d

# 包含 Redis 和 Nginx
docker-compose --profile with-redis --profile with-nginx up -d
```

### 生产环境部署

详细的部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 🛠️ 开发

### 开发环境设置

```bash
# 安装开发依赖
make dev-install

# 代码格式化
make format

# 代码质量检查
make lint

# 完整开发环境设置
make dev-setup
```

### 项目结构

```
├── config/              # 配置管理模块
├── error_handler/       # 错误处理模块
├── logger/             # 日志系统模块
├── dictionary/         # 字典服务模块
├── admin/              # Web 管理控制台
├── health_check/       # 健康检查模块
├── restart/            # 重启功能模块
├── audio_cache/        # 音频缓存模块
├── templates/          # HTML 模板
├── tests/              # 测试文件
├── logs/               # 日志文件
├── enhanced_tts_api.py # 主应用文件
├── config.json         # 配置文件
├── docker-compose.yml  # Docker Compose 配置
├── Dockerfile          # Docker 镜像配置
├── Makefile           # 项目管理命令
└── setup.py           # 系统设置脚本
```

## 🔧 故障排除

### 常见问题

1. **Edge-TTS 连接失败**
   ```bash
   # 检查网络连接
   curl -I https://speech.platform.bing.com
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   # 调整配置中的 max_workers 和 cache_size_limit
   ```

3. **权限问题**
   ```bash
   # 修复日志目录权限
   chmod 755 logs/
   chmod 644 config.json
   ```

### 日志分析

查看详细的错误信息：

```bash
# 应用日志
tail -f logs/app.log

# 系统日志
journalctl -u tts-api -f

# Docker 日志
docker logs -f tts-api
```

## 📈 性能优化

### 缓存优化

```json
{
  "tts": {
    "cache_size_limit": 52428800,  // 50MB
    "cache_time_limit": 3600       // 1小时
  }
}
```

### 并发优化

```bash
# Gunicorn 配置
gunicorn -b 0.0.0.0:5000 enhanced_tts_api:app \
  --workers 4 \
  --worker-class sync \
  --timeout 120
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 运行测试
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [Microsoft Edge-TTS](https://github.com/rany2/edge-tts) - 语音合成服务
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [pydub](https://github.com/jiaaro/pydub) - 音频处理库

---

如有问题或建议，请提交 Issue 或联系项目维护者。
