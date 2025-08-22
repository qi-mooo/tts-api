# TTS API 快速部署指南

## 🚀 一键部署

### 前提条件
- 已安装 Docker 和 Docker Compose
- 系统支持 curl 命令

### 部署步骤

1. **下载部署文件**
```bash
# 创建部署目录
mkdir tts-api-deploy && cd tts-api-deploy

# 下载必要文件
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/deploy.sh
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/qi-mooo/tts-api/main/.env.template
```

2. **配置环境**
```bash
# 复制环境配置
cp .env.template .env

# 编辑配置文件（可选）
nano .env
```

3. **运行部署**
```bash
# 给脚本执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

4. **验证部署**
```bash
# 检查服务状态
curl http://localhost:8080/health

# 访问管理界面
open http://localhost:8080/admin
```

## 🔧 管理命令

```bash
# 查看服务日志
docker-compose logs -f tts-api

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新到最新版本
docker pull ghcr.io/qi-mooo/tts-api:latest && docker-compose up -d
```

## 🌐 访问地址

- **API 服务**: http://localhost:8080
- **健康检查**: http://localhost:8080/health  
- **管理控制台**: http://localhost:8080/admin
- **API 文档**: http://localhost:8080/api?text=测试

## 🔒 安全配置

默认管理员账号：
- 用户名: `admin`
- 密码: `admin123`

**⚠️ 生产环境请务必修改默认密码！**

编辑 `.env` 文件中的 `TTS_ADMIN_PASSWORD` 变量。

## 📞 技术支持

如遇问题，请查看：
1. 服务日志: `docker-compose logs tts-api`
2. 系统资源: `docker stats`
3. 网络连接: `curl -I https://speech.platform.bing.com`

更多详细信息请参考 [完整文档](README.md)。