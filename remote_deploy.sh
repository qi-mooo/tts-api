#!/bin/bash

# 远程服务器部署脚本
# 用于在 SSH 服务器上部署 TTS API 服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 服务器配置
SERVER_HOST="10.0.0.129"
SERVER_USER="root"
SERVER_PATH="/vol1/1000/docker/tts-api"
GITHUB_REPO="https://github.com/qi-mooo/tts-api.git"

echo "🚀 TTS API 远程部署脚本"
echo "================================================"
echo "目标服务器: ${SERVER_USER}@${SERVER_HOST}"
echo "部署路径: ${SERVER_PATH}"
echo "GitHub 仓库: ${GITHUB_REPO}"
echo "================================================"

# 检查本地是否能连接到服务器
print_info "检查服务器连接..."
if ! ssh -o ConnectTimeout=10 ${SERVER_USER}@${SERVER_HOST} "echo '连接成功'" 2>/dev/null; then
    print_error "无法连接到服务器 ${SERVER_USER}@${SERVER_HOST}"
    echo "请检查："
    echo "1. 服务器是否在线"
    echo "2. SSH 密钥是否配置正确"
    echo "3. 网络连接是否正常"
    exit 1
fi
print_success "服务器连接正常"

# 执行远程部署
print_info "开始远程部署..."

ssh ${SERVER_USER}@${SERVER_HOST} << 'EOF'
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

PROJECT_PATH="/vol1/1000/docker/tts-api"
GITHUB_REPO="https://github.com/qi-mooo/tts-api.git"

print_info "在服务器上执行部署..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

print_success "Docker 环境检查通过"

# 创建项目目录
print_info "准备项目目录..."
mkdir -p $(dirname ${PROJECT_PATH})

# 检查项目是否已存在
if [ -d "${PROJECT_PATH}" ]; then
    print_info "项目目录已存在，更新代码..."
    cd ${PROJECT_PATH}
    
    # 停止现有服务
    print_info "停止现有服务..."
    docker-compose down 2>/dev/null || true
    
    # 拉取最新代码
    print_info "拉取最新代码..."
    git fetch origin
    git reset --hard origin/main
    git clean -fd
else
    print_info "克隆项目代码..."
    git clone ${GITHUB_REPO} ${PROJECT_PATH}
    cd ${PROJECT_PATH}
fi

print_success "代码更新完成"

# 检查端口配置
print_info "验证端口配置..."
if [ -f "verify_port_consistency.py" ]; then
    if command -v python3 &> /dev/null; then
        python3 verify_port_consistency.py || print_warning "端口配置检查失败，但继续部署"
    else
        print_warning "Python3 未安装，跳过端口配置检查"
    fi
fi

# 创建必要的目录
print_info "创建必要的目录..."
mkdir -p logs
mkdir -p audio_cache
mkdir -p database

# 检查配置文件
print_info "检查配置文件..."
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        print_info "创建环境配置文件..."
        cp .env.template .env
        
        # 更新端口配置
        sed -i 's/TTS_PORT=5000/TTS_PORT=8080/g' .env 2>/dev/null || true
        sed -i 's/SYSTEM_PORT=5000/SYSTEM_PORT=8080/g' .env 2>/dev/null || true
    else
        print_warning "未找到 .env.template，创建默认配置..."
        cat > .env << 'ENVEOF'
TTS_PORT=8080
TTS_ADMIN_USERNAME=admin
TTS_ADMIN_PASSWORD=admin123
TTS_NARRATION_VOICE=zh-CN-YunjianNeural
TTS_DIALOGUE_VOICE=zh-CN-XiaoyiNeural
TTS_DEFAULT_SPEED=1.2
TTS_LOG_LEVEL=INFO
FLASK_ENV=production
FLASK_DEBUG=0
ENVEOF
    fi
fi

if [ ! -f "config.json" ]; then
    if [ -f "config.json.template" ]; then
        print_info "创建配置文件..."
        cp config.json.template config.json
    fi
fi

print_success "配置文件准备完成"

# 构建和启动服务
print_info "构建 Docker 镜像..."
docker-compose build

print_info "启动服务..."
docker-compose up -d

# 等待服务启动
print_info "等待服务启动..."
sleep 10

# 检查服务状态
print_info "检查服务状态..."
if curl -f http://localhost:8080/health &> /dev/null; then
    print_success "TTS API 部署成功！"
    echo ""
    echo "🌐 服务信息："
    echo "  - 服务地址: http://$(hostname -I | awk '{print $1}'):8080"
    echo "  - 健康检查: http://$(hostname -I | awk '{print $1}'):8080/health"
    echo "  - 管理面板: http://$(hostname -I | awk '{print $1}'):8080/admin"
    echo "  - API 文档: http://$(hostname -I | awk '{print $1}'):8080/api/status"
    echo ""
    echo "📋 管理命令："
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 停止服务: docker-compose down"
    echo "  - 更新服务: git pull && docker-compose up -d --build"
else
    print_error "服务启动失败，检查日志："
    docker-compose logs --tail=20
    exit 1
fi

EOF

if [ $? -eq 0 ]; then
    print_success "远程部署完成！"
    
    # 获取服务器 IP 用于访问
    SERVER_IP=$(ssh ${SERVER_USER}@${SERVER_HOST} "hostname -I | awk '{print \$1}'" 2>/dev/null || echo ${SERVER_HOST})
    
    echo ""
    echo "🎉 部署成功！"
    echo "================================================"
    echo "🌐 服务访问地址："
    echo "  - 主服务: http://${SERVER_IP}:8080"
    echo "  - 健康检查: http://${SERVER_IP}:8080/health"
    echo "  - 管理面板: http://${SERVER_IP}:8080/admin"
    echo "  - API 状态: http://${SERVER_IP}:8080/api/status"
    echo ""
    echo "🔧 远程管理命令："
    echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'cd ${SERVER_PATH} && docker-compose logs -f'"
    echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'cd ${SERVER_PATH} && docker-compose restart'"
    echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'cd ${SERVER_PATH} && docker-compose down'"
    echo ""
    echo "📝 默认管理员账号："
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo "================================================"
else
    print_error "远程部署失败！"
    exit 1
fi