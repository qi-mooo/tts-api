#!/bin/bash

# TTS API 快速部署脚本
# 使用 GitHub Packages 中的预构建镜像

set -e

echo "🚀 开始部署 TTS API..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录和文件
echo "📁 创建必要的目录..."
mkdir -p logs

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "📝 创建环境配置文件..."
    if [ -f ".env.template" ]; then
        cp .env.template .env
    else
        cat > .env << EOF
# TTS API 环境配置
TTS_ADMIN_USERNAME=admin
TTS_ADMIN_PASSWORD=admin123
TTS_NARRATION_VOICE=zh-CN-YunjianNeural
TTS_DIALOGUE_VOICE=zh-CN-XiaoyiNeural
TTS_DEFAULT_SPEED=1.2
TTS_LOG_LEVEL=INFO
FLASK_ENV=production
FLASK_DEBUG=0
EOF
    fi
    echo "⚠️  请编辑 .env 文件以配置您的 TTS 服务"
fi

# 加载环境变量
if [ -f ".env" ]; then
    echo "🔧 加载环境配置..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# 拉取最新镜像
echo "📦 拉取最新的 Docker 镜像..."
docker pull ghcr.io/qi-mooo/tts-api:latest

# 停止现有服务（如果存在）
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true

# 启动服务
echo "🔄 启动 TTS API 服务..."
docker-compose -f docker-compose.simple.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if curl -f http://localhost:5000/health &> /dev/null; then
    echo "✅ TTS API 部署成功！"
    echo "🌐 服务地址: http://localhost:5000"
    echo "🏥 健康检查: http://localhost:5000/health"
    echo "📊 管理面板: http://localhost:5000/admin"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose -f docker-compose.simple.yml logs tts-api
    exit 1
fi

echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose -f docker-compose.simple.yml logs -f tts-api"
echo "  停止服务: docker-compose -f docker-compose.simple.yml down"
echo "  重启服务: docker-compose -f docker-compose.simple.yml restart"
echo "  更新镜像: docker pull ghcr.io/qi-mooo/tts-api:latest && docker-compose -f docker-compose.simple.yml up -d"