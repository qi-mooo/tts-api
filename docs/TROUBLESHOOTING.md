# TTS API 故障排除指南

## 概述

本文档提供 TTS API 项目的故障排除指南，涵盖常见问题的诊断和解决方案。

## 目录

1. [服务启动问题](#服务启动问题)
2. [API 端点问题](#api-端点问题)
3. [语音功能问题](#语音功能问题)
4. [部署问题](#部署问题)
5. [测试问题](#测试问题)
6. [性能问题](#性能问题)
7. [配置问题](#配置问题)

## 服务启动问题

### 问题：端口被占用
```bash
# 症状
Error: [Errno 48] Address already in use

# 诊断
lsof -i :8080

# 解决方案
kill $(lsof -t -i:8080)
# 或者修改配置使用其他端口
```

### 问题：虚拟环境未激活
```bash
# 症状
ModuleNotFoundError: No module named 'flask'

# 解决方案
# 使用虚拟环境中的 Python
./venv/bin/python3 start_server.py

# 或者检查虚拟环境
ls -la venv/bin/python3
```

### 问题：依赖缺失
```bash
# 诊断
./venv/bin/pip check

# 解决方案
./venv/bin/pip install -r requirements.txt
```

## API 端点问题

### 问题：404 错误但路由存在
```bash
# 症状
GET /api/status 返回 404

# 诊断步骤
1. 检查应用文件是否正确
2. 验证路由注册
3. 检查导入语句

# 解决方案
# 确保使用正确的应用文件
./venv/bin/python3 -c "from app_enhanced import app; print([rule.rule for rule in app.url_map.iter_rules()])"
```

### 问题：500 错误返回复杂堆栈跟踪
```bash
# 症状
访问不存在的路径返回 500 而不是 404

# 原因
错误处理器没有正确处理 HTTP 异常

# 解决方案
检查 error_handler/error_handler.py 中的 handle_error 方法
确保正确处理 HTTPException
```

### 问题：根路径返回 404
```bash
# 症状
GET / 返回 404

# 诊断
curl -v http://localhost:8080/

# 解决方案
确保 app_enhanced.py 中有根路径路由：
@app.route('/')
def index():
    return jsonify({...})
```

## 语音功能问题

### 问题：语音列表为空
```bash
# 症状
/api/voices 返回空列表

# 诊断
ls -la data/voices*.json

# 解决方案
./venv/bin/python3 scripts/install_voices.py
./venv/bin/python3 scripts/integrate_voice_manager.py
```

### 问题：TTS 生成失败
```bash
# 症状
/api?text=测试 返回错误

# 诊断步骤
1. 检查网络连接
2. 验证语音名称
3. 检查文本内容

# 解决方案
# 测试语音管理器
./venv/bin/python3 -c "from voice_manager import VoiceManager; vm = VoiceManager(); print(vm.get_chinese_voices()[:3])"

# 测试 edge-tts 连接
./venv/bin/python3 -c "import edge_tts; print('edge-tts 可用')"
```

### 问题：语音验证失败
```bash
# 症状
语音名称验证返回 False

# 解决方案
# 重新获取语音列表
./venv/bin/python3 scripts/update_voices.py

# 检查语音数据
./venv/bin/python3 -c "from voice_manager import VoiceManager; vm = VoiceManager(); print(vm.validate_voice('zh-CN-YunjianNeural'))"
```

## 部署问题

### 问题：Docker 构建失败
```bash
# 症状
docker build 过程中出错

# 常见原因和解决方案
1. 依赖安装失败
   - 检查 requirements.txt
   - 确保网络连接正常

2. 文件复制失败
   - 检查 Dockerfile 中的 COPY 指令
   - 确保文件路径正确

3. 权限问题
   - 检查文件权限
   - 使用 chmod 修复权限
```

### 问题：容器启动失败
```bash
# 诊断
docker logs <container_id>

# 常见问题
1. 端口冲突
   - 修改 docker-compose.yml 中的端口映射

2. 环境变量缺失
   - 检查 .env 文件
   - 验证环境变量设置

3. 文件挂载问题
   - 检查 volumes 配置
   - 确保挂载路径存在
```

### 问题：GitHub Actions 失败
```bash
# 诊断
# 检查 Actions 状态
curl -s "https://api.github.com/repos/qi-mooo/tts-api/actions/runs?per_page=1"

# 常见问题
1. 代码语法错误
   - 本地运行测试
   - 检查 Python 语法

2. 依赖冲突
   - 更新 requirements.txt
   - 测试依赖兼容性

3. Docker 构建超时
   - 优化 Dockerfile
   - 减少镜像大小
```

## 测试问题

### 重要说明：已清理的测试文件

项目已进行清理，删除了以下多余的测试和验证文件：

**已删除的测试文件：**
- `test_admin_basic.py` - 基础管理员测试（功能已合并到其他测试）
- `test_admin_interface.py` - 管理界面测试（功能已合并）
- `test_audio_cache_integration.py` - 音频缓存集成测试（已合并）
- `test_enhanced_api_simple.py` - 简单 API 测试（已合并）
- `test_password_setup.py` - 密码设置测试（已合并）
- `test_restart_functionality.py` - 重启功能测试（已合并）
- `test_root_path.py` - 根路径测试（已合并到集成测试）
- `test_routes.py` - 路由测试（已合并）

**已删除的验证文件：**
- `verify_deployment.py` - 部署验证脚本（功能已合并到测试文件）
- `verify_port_consistency.py` - 端口一致性验证（已合并）

如果您在旧文档或脚本中看到这些文件的引用，请使用当前的核心测试文件。

### 问题：测试文件找不到
```bash
# 症状
ModuleNotFoundError 或 FileNotFoundError

# 当前测试文件结构（已清理多余文件）
tts-api/
├── test_integration.py      # 集成测试 - 完整的端到端测试
├── test_quick.py           # 快速测试 - 基础功能验证
├── test_voice_api.py       # 语音 API 测试 - 语音相关功能测试
├── test_voice_manager.py   # 语音管理器测试 - 语音管理功能测试
└── tests/                  # 模块化测试目录
    ├── test_admin_controller.py        # 管理控制器测试
    ├── test_audio_cache.py             # 音频缓存测试
    ├── test_config_manager.py          # 配置管理器测试
    ├── test_dictionary_service.py      # 字典服务测试
    ├── test_end_to_end_integration.py  # 端到端集成测试
    ├── test_enhanced_tts_api.py        # 增强 TTS API 测试
    ├── test_error_handler.py           # 错误处理器测试
    ├── test_flask_integration.py       # Flask 集成测试
    ├── test_health_check.py            # 健康检查测试
    ├── test_integration_simple.py      # 简单集成测试
    ├── test_restart_controller.py      # 重启控制器测试
    ├── test_restart_flask_integration.py # 重启 Flask 集成测试
    └── test_structured_logger.py       # 结构化日志测试

# 运行测试的正确方法
./venv/bin/python3 test_quick.py                    # 快速测试
./venv/bin/python3 test_integration.py              # 集成测试
./venv/bin/python3 -m unittest discover tests -v   # 模块测试
```

### 问题：测试服务器连接失败
```bash
# 症状
Connection refused 或 timeout

# 解决方案
1. 确保服务正在运行
   ./venv/bin/python3 start_server.py

2. 检查端口配置
   curl http://localhost:8080/health

3. 等待服务启动
   sleep 5 && ./venv/bin/python3 test_quick.py
```

### 问题：测试数据不一致
```bash
# 症状
测试结果不稳定

# 解决方案
1. 清理测试环境
   rm -f test_*.webm test_*.wav

2. 重置配置
   ./venv/bin/python3 -c "from config.config_manager import config_manager; config_manager.reset_to_defaults()"

3. 重新初始化语音数据
   ./venv/bin/python3 scripts/install_voices.py
```

## 性能问题

### 问题：TTS 生成速度慢
```bash
# 诊断
# 检查网络延迟
ping speech.platform.bing.com

# 解决方案
1. 启用音频缓存
   - 检查 config.json 中的 cache 配置
   - 确保缓存目录可写

2. 优化文本处理
   - 减少不必要的文本预处理
   - 使用批量处理

3. 调整并发设置
   - 修改 gunicorn 配置
   - 增加 worker 数量
```

### 问题：内存使用过高
```bash
# 诊断
# 监控内存使用
ps aux | grep python3
top -p $(pgrep -f "python3.*app_enhanced")

# 解决方案
1. 清理音频缓存
   rm -rf audio_cache/*

2. 调整缓存大小
   - 修改 config.json 中的缓存配置

3. 重启服务
   ./venv/bin/python3 start_server.py --restart
```

## 配置问题

### 问题：配置文件损坏
```bash
# 症状
JSON decode error

# 诊断
./venv/bin/python3 -c "import json; json.load(open('config.json'))"

# 解决方案
1. 备份当前配置
   cp config.json config.json.backup

2. 重置为默认配置
   ./venv/bin/python3 -c "from config.config_manager import config_manager; config_manager.create_default_config()"

3. 手动修复 JSON 语法错误
```

### 问题：语音配置不生效
```bash
# 症状
使用默认语音而不是配置的语音

# 解决方案
1. 验证语音名称
   ./venv/bin/python3 -c "from voice_manager import VoiceManager; vm = VoiceManager(); print(vm.validate_voice('zh-CN-YunjianNeural'))"

2. 重新集成语音配置
   ./venv/bin/python3 scripts/integrate_voice_manager.py

3. 重启服务使配置生效
```

## 日志和调试

### 启用详细日志
```bash
# 开发模式启动（详细日志）
./venv/bin/python3 start_server.py --debug

# 查看日志文件
tail -f logs/app.log

# 搜索错误日志
grep -i "error\|exception" logs/app.log
```

### 调试特定模块
```bash
# 测试语音管理器
./venv/bin/python3 -c "
from voice_manager import VoiceManager
vm = VoiceManager()
print('语音数量:', len(vm.get_all_voices()))
print('中文语音:', len(vm.get_chinese_voices()))
"

# 测试 TTS 服务
./venv/bin/python3 -c "
from enhanced_tts_api import enhanced_tts_service
result = enhanced_tts_service.generate_audio('测试', speed=1.0)
print('TTS 测试结果:', type(result))
"

# 测试配置管理器
./venv/bin/python3 -c "
from config.config_manager import config_manager
print('当前配置:', config_manager.get_config_dict())
"
```

## 快速诊断命令

### 系统状态检查
```bash
# 一键检查脚本
./venv/bin/python3 -c "
print('=== TTS API 系统状态检查 ===')

# 检查虚拟环境
import sys
print(f'Python 路径: {sys.executable}')

# 检查关键模块
try:
    import flask
    print(f'Flask 版本: {flask.__version__}')
except ImportError as e:
    print(f'Flask 导入失败: {e}')

try:
    import edge_tts
    print('Edge-TTS: 可用')
except ImportError as e:
    print(f'Edge-TTS 导入失败: {e}')

# 检查配置文件
import os
if os.path.exists('config.json'):
    print('配置文件: 存在')
else:
    print('配置文件: 缺失')

# 检查语音数据
if os.path.exists('data/voices.json'):
    print('语音数据: 存在')
else:
    print('语音数据: 缺失')

print('=== 检查完成 ===')
"
```

### 服务健康检查
```bash
# 快速健康检查
curl -s http://localhost:8080/health | python3 -m json.tool

# API 状态检查
curl -s http://localhost:8080/api/status | python3 -m json.tool

# 语音列表检查
curl -s "http://localhost:8080/api/voices?chinese_only=true" | python3 -m json.tool | head -20
```

## 获取帮助

### 查看文档
- `docs/API_DOCUMENTATION.md` - API 文档
- `docs/DEPLOYMENT_GUIDE.md` - 部署指南
- `docs/DEVELOPMENT_GUIDE.md` - 开发指南

### 运行测试
```bash
# 快速功能测试
./venv/bin/python3 test_quick.py

# 完整集成测试
./venv/bin/python3 test_integration.py

# 语音功能测试
./venv/bin/python3 test_voice_api.py --test voices
```

### 联系支持
如果问题仍未解决：
1. 收集错误日志和系统信息
2. 记录重现步骤
3. 检查 GitHub Issues
4. 创建新的 Issue 并提供详细信息

---

*最后更新: 2024年8月*