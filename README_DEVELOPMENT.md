# TTS 项目开发指南

## 双终端开发工作流程

本项目推荐使用双终端开发模式，一个终端运行服务，另一个终端进行测试和开发。

### 🚀 快速开始

#### 终端 1: 启动服务
```bash
# 进入项目目录
cd /path/to/tts-project

# 启动服务（自动检查环境和端口）
./venv/bin/python3 start_server.py
```

#### 终端 2: 运行测试
```bash
# 进入项目目录
cd /path/to/tts-project

# 运行快速测试
./venv/bin/python3 test_quick.py
```

### 📋 服务信息

- **端口**: 8080
- **管理界面**: http://localhost:8080/admin
- **API 端点**: http://localhost:8080/api
- **健康检查**: http://localhost:8080/health
- **API 状态**: http://localhost:8080/api/status
- **默认账号**: admin / admin123

### 🛠️ 启动选项

```bash
# 基础启动
./venv/bin/python3 start_server.py

# 调试模式
./venv/bin/python3 start_server.py --debug

# 生产模式（使用 gunicorn）
./venv/bin/python3 start_server.py --production

# 自定义端口
./venv/bin/python3 start_server.py --port 9000

# 跳过环境检查
./venv/bin/python3 start_server.py --skip-checks
```

### 🧪 测试选项

```bash
# 运行所有测试
./venv/bin/python3 test_quick.py

# 只测试健康检查
./venv/bin/python3 test_quick.py --test health

# 只测试 API 状态
./venv/bin/python3 test_quick.py --test api

# 只测试 TTS 功能
./venv/bin/python3 test_quick.py --test tts

# 只测试管理登录
./venv/bin/python3 test_quick.py --test admin

# 只测试字典功能
./venv/bin/python3 test_quick.py --test dict

# 自定义测试文本和语速
./venv/bin/python3 test_quick.py --test tts --text "你好世界" --speed 1.5

# 测试其他服务器
./venv/bin/python3 test_quick.py --url http://localhost:8080
```

### 📊 测试输出示例

```
🎯 TTS 服务快速测试工具
📍 目标服务: http://localhost:8080
⏰ 测试时间: 2025-08-23 00:59:15
==================================================
🚀 开始运行所有测试...

🔍 测试健康检查...
   状态码: 200
   响应时间: 0.023s
   服务状态: healthy

🔍 测试 API 状态...
   状态码: 200
   响应时间: 0.015s
   服务版本: 2.0.0
   缓存状态: 1 项

🔍 测试 TTS API (文本: '你好', 语速: 1.0)...
   状态码: 200
   响应时间: 2.456s
   内容类型: audio/webm
   内容大小: 12345 字节
   ✅ 音频已保存到: test_audio_1755881955.webm

📊 测试结果汇总:
   health: ✅ 成功
   api_status: ✅ 成功
   tts_simple: ✅ 成功
   tts_complex: ✅ 成功
   admin_login: ✅ 成功
   dictionary: ✅ 成功

✅ 成功: 6/6
❌ 失败: 0/6
```

### 🔧 开发工具

#### 代码质量检查
```bash
# 检查代码风格
./venv/bin/flake8 . --exclude=venv

# 格式化代码
./venv/bin/black . --exclude=venv

# 检查依赖
./venv/bin/pip check
```

#### 日志查看
```bash
# 实时查看日志
tail -f logs/app.log

# 查看最近的日志
tail -n 100 logs/app.log

# 搜索错误日志
grep -i error logs/app.log
```

#### 端口管理
```bash
# 检查端口占用
lsof -i :8080

# 停止占用端口的进程
kill $(lsof -t -i:8080)
```

### 🐛 故障排除

#### 常见问题

1. **端口被占用**
   ```bash
   # 启动脚本会自动检查并提示处理
   ./venv/bin/python3 start_server.py
   ```

2. **依赖缺失**
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```

3. **虚拟环境问题**
   ```bash
   # 重新创建虚拟环境
   rm -rf venv
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```

4. **配置文件错误**
   ```bash
   # 验证配置文件
   ./venv/bin/python3 -c "import json; print(json.load(open('config.json')))"
   ```

#### 调试模式

启用调试模式可以获得更详细的日志信息：

```bash
# 启动调试模式
./venv/bin/python3 start_server.py --debug
```

调试模式特性：
- 更详细的错误信息
- 自动重载代码变更
- 详细的请求日志
- 堆栈跟踪信息

### 📝 开发最佳实践

1. **始终使用虚拟环境**: `./venv/bin/python3` 而不是系统 `python3`
2. **定期运行测试**: 使用 `test_quick.py` 验证功能
3. **监控日志**: 关注 `logs/app.log` 中的错误和警告
4. **代码质量**: 定期运行 `flake8` 和 `black`
5. **配置管理**: 通过 `config.json` 管理所有配置
6. **版本控制**: 提交前运行完整测试

### 🚀 部署

#### 开发环境
```bash
./venv/bin/python3 start_server.py --debug
```

#### 生产环境
```bash
./venv/bin/python3 start_server.py --production
```

#### Docker 部署
```bash
docker build -t tts-service .
docker run -p 8080:8080 tts-service
```

### 📚 更多信息

- 详细的开发工作流程请参考: `.kiro/steering/development-workflow.md`
- API 文档: 访问管理界面查看
- 配置说明: 查看 `config.json` 文件注释