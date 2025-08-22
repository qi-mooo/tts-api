#!/bin/bash
"""
部署脚本 - 包含语音列表更新
在部署前自动获取最新的语音列表
"""

set -e  # 遇到错误时退出

echo "=== TTS 项目部署脚本（包含语音管理） ==="

# 检查虚拟环境
if [ ! -f "./venv/bin/python3" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

echo "✅ 虚拟环境检查通过"

# 安装/更新依赖
echo "📦 安装依赖..."
./venv/bin/pip install -r requirements.txt

# 获取语音列表
echo "🎤 获取最新语音列表..."
./venv/bin/python3 scripts/install_voices.py

# 集成语音管理器
echo "🔧 集成语音管理器..."
./venv/bin/python3 scripts/integrate_voice_manager.py

# 运行测试
echo "🧪 运行语音管理器测试..."
./venv/bin/python3 test_voice_manager.py

if [ $? -eq 0 ]; then
    echo "✅ 语音管理器测试通过"
else
    echo "❌ 语音管理器测试失败"
    exit 1
fi

# 运行应用测试（如果存在）
if [ -f "test_quick.py" ]; then
    echo "🧪 运行应用快速测试..."
    ./venv/bin/python3 test_quick.py --test health
    if [ $? -eq 0 ]; then
        echo "✅ 应用测试通过"
    else
        echo "❌ 应用测试失败"
        exit 1
    fi
fi

echo ""
echo "🎉 部署准备完成！"
echo ""
echo "语音统计信息:"
./venv/bin/python3 -c "
from voice_manager import voice_manager
stats = voice_manager.get_voice_stats()
print(f'  总语音数: {stats[\"total_voices\"]}')
print(f'  中文语音数: {stats[\"chinese_voices\"]}')
print(f'  支持地区数: {stats[\"chinese_locales\"]}')
"

echo ""
echo "下一步:"
echo "1. 启动服务: ./venv/bin/python3 start_server.py"
echo "2. 或使用 Docker: docker-compose up -d"
echo "3. 测试语音功能: ./venv/bin/python3 test_quick.py --test tts"