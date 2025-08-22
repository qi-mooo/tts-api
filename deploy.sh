#!/bin/bash

# TTS API 快速部署脚本
# 使用 GitHub Packages 中的预构建镜像

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

# 读取用户输入的函数
read_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        if [ -z "$input" ]; then
            input="$default"
        fi
    else
        read -p "$prompt: " input
        while [ -z "$input" ]; do
            print_warning "此项不能为空，请重新输入"
            read -p "$prompt: " input
        done
    fi
    
    eval "$var_name='$input'"
}

# 读取密码输入的函数（可选）
read_password() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo "$prompt [默认: $default]"
    echo "留空使用默认密码，或输入新密码（至少6位）："
    
    while true; do
        read -s -p "密码: " password
        echo
        
        # 如果密码为空，使用默认值
        if [ -z "$password" ]; then
            eval "$var_name='$default'"
            print_info "使用默认密码"
            break
        fi
        
        # 检查密码长度
        if [ ${#password} -lt 6 ]; then
            print_warning "密码长度至少6位，请重新输入（或留空使用默认）"
            continue
        fi
        
        read -s -p "确认密码: " password_confirm
        echo
        if [ "$password" = "$password_confirm" ]; then
            eval "$var_name='$password'"
            break
        else
            print_warning "两次密码不一致，请重新输入（或留空使用默认）"
        fi
    done
}

echo "🚀 欢迎使用 TTS API 部署脚本！"
echo "================================================"

# 检查系统依赖
print_info "检查系统依赖..."

if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装，请先安装 Docker"
    echo "安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose 未安装，请先安装 Docker Compose"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "系统依赖检查通过"
echo

# 交互式配置
print_info "开始配置 TTS API 服务..."
echo

# 服务端口配置
read_input "请输入服务端口" "5000" "TTS_PORT"

# 管理员账号配置
print_info "配置管理员账号..."
read_input "管理员用户名" "admin" "TTS_ADMIN_USERNAME"
read_password "管理员密码（至少6位）" "TTS_ADMIN_PASSWORD"

echo

# 语音配置
print_info "配置语音参数..."
echo "常用中文语音："
echo "  1. zh-CN-YunjianNeural (云健-男声)"
echo "  2. zh-CN-XiaoyiNeural (晓伊-女声)"
echo "  3. zh-CN-YunxiNeural (云希-男声)"
echo "  4. zh-CN-XiaoxiaoNeural (晓晓-女声)"
echo

read_input "旁白语音" "zh-CN-YunjianNeural" "TTS_NARRATION_VOICE"
read_input "对话语音" "zh-CN-XiaoyiNeural" "TTS_DIALOGUE_VOICE"
read_input "默认语速 (0.5-2.0)" "1.2" "TTS_DEFAULT_SPEED"

echo

# 高级配置
print_info "高级配置（可选）..."
echo "是否配置高级选项？(y/N)"
read -n 1 -r advanced_config
echo

if [[ $advanced_config =~ ^[Yy]$ ]]; then
    read_input "日志级别 (DEBUG/INFO/WARNING/ERROR)" "INFO" "TTS_LOG_LEVEL"
    
    echo "是否启用开发模式？(y/N)"
    read -n 1 -r dev_mode
    echo
    
    if [[ $dev_mode =~ ^[Yy]$ ]]; then
        FLASK_ENV="development"
        FLASK_DEBUG="1"
        print_warning "开发模式已启用，将使用本地构建的镜像"
    else
        FLASK_ENV="production"
        FLASK_DEBUG="0"
    fi
else
    TTS_LOG_LEVEL="INFO"
    FLASK_ENV="production"
    FLASK_DEBUG="0"
fi

echo

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
docker-compose down 2>/dev/null || true

# 启动服务
echo "🔄 启动 TTS API 服务..."
docker-compose up -d

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
    docker-compose logs tts-api
    exit 1
fi

echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f tts-api"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  更新镜像: docker pull ghcr.io/qi-mooo/tts-api:latest && docker-compose up -d"