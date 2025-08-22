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

# 创建配置文件（如果不存在）
if [ ! -f "config.json" ]; then
    echo "📝 创建默认配置文件..."
    cp config.json.template config.json
    echo "⚠️  请编辑 config.json 文件以配置您的 TTS 服务"
fi

# 创建日志目录
mkdir -p logs

# 拉取最新镜像
echo "📦 拉取最新的 Docker 镜像..."
docker pull ghcr.io/qi-mooo/tts-api:latest

# 停止现有服务（如果存在）
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# 启动服务
echo "🔄 启动 TTS API 服务..."
docker-compose -f docker-compose.prod.yml up -d

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
    docker-compose -f docker-compose.prod.yml logs tts-api
    exit 1
fi

echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f tts-api"
echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
echo "  更新镜像: docker pull ghcr.io/qi-mooo/tts-api:latest && docker-compose -f docker-compose.prod.yml up -d"