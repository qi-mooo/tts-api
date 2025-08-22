# TTS API

一个功能完善的文本转语音（TTS）API 系统，基于 Microsoft Edge-TTS 服务，支持 322+ 个语音，包括 14 个中文语音。

## ✨ 主要特性

- 🎤 **语音合成**: 基于 Microsoft Edge-TTS 的高质量语音合成
- 🌍 **多语音支持**: 支持 322+ 个语音，包括 14 个中文语音
- 🚀 **智能缓存**: 音频缓存系统，提升响应速度
- 🎛️ **Web 控制台**: 响应式管理界面，支持配置管理和系统监控
- 📝 **字典功能**: 支持发音替换和内容净化
- 🔍 **语音管理**: 完整的语音搜索、验证和管理功能
- 📊 **系统监控**: 结构化日志记录和健康检查
- 🐳 **容器化**: 完整的 Docker 支持和一键部署

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/qi-mooo/tts-api.git
cd tts-api

# 2. 启动服务
docker-compose up -d

# 3. 访问服务
curl http://localhost:8080/health
```

### 本地开发

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化语音系统
./venv/bin/python3 scripts/install_voices.py

# 4. 启动服务
./venv/bin/python3 app_enhanced.py
```

## 📖 API 使用示例

### 基础 TTS 转换

```bash
# 基本用法
curl "http://localhost:8080/api?text=你好世界"

# 自定义语速和语音
curl "http://localhost:8080/api?text=你好世界&speed=1.5&narr=zh-CN-YunjianNeural"
```

### 语音管理

```bash
# 获取所有中文语音
curl "http://localhost:8080/api/voices"

# 搜索女性语音
curl "http://localhost:8080/api/voices?gender=Female"

# 验证语音是否有效
curl -X POST "http://localhost:8080/api/voices/validate" \
  -H "Content-Type: application/json" \
  -d '{"voice_name": "zh-CN-YunjianNeural"}'
```

## 🎛️ Web 管理控制台

访问 `http://localhost:8080/admin` 进入管理控制台：

- **配置管理**: 实时修改语音参数和系统设置
- **字典管理**: 添加、编辑发音规则
- **系统监控**: 查看服务状态和性能指标
- **语音预览**: 测试配置效果

默认登录信息：
- 用户名：`admin`
- 密码：`admin123`（请及时修改）

## 📚 文档

- [📋 完整安装指南](docs/installation.md)
- [🔧 配置说明](docs/configuration.md)
- [📖 API 文档](docs/api-reference.md)
- [🎤 语音管理指南](docs/voice-management.md)
- [🚀 部署指南](docs/deployment.md)
- [🛠️ 开发指南](docs/development.md)
- [❓ 故障排除](docs/troubleshooting.md)

## 🎤 支持的语音

### 中文语音（14个）

| 语音名称 | 性别 | 地区 | 描述 |
|---------|------|------|------|
| zh-CN-YunjianNeural | 男性 | 中国大陆 | 默认旁白语音 ⭐ |
| zh-CN-XiaoyiNeural | 女性 | 中国大陆 | 默认对话语音 ⭐ |
| zh-CN-XiaoxiaoNeural | 女性 | 中国大陆 | 标准普通话 |
| zh-HK-HiuGaaiNeural | 女性 | 香港 | 粤语 |
| zh-TW-HsiaoChenNeural | 女性 | 台湾 | 台湾官话 |
| ... | ... | ... | [查看完整列表](docs/voice-management.md#supported-voices) |

**总计**: 322+ 个语音，覆盖 142 个地区

## 🔧 系统要求

- **Python**: 3.8+
- **内存**: 2GB+（推荐 4GB+）
- **存储**: 5GB+
- **网络**: 稳定的互联网连接

## 📊 项目状态

- ✅ **稳定版本**: v2.1.0
- 🎤 **语音支持**: 322+ 个语音
- 🌍 **语言支持**: 142 个地区
- 📈 **API 响应**: < 100ms
- 🐳 **Docker**: 支持
- 📱 **移动端**: 响应式设计

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Microsoft Edge-TTS](https://github.com/rany2/edge-tts) - 语音合成服务
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [pydub](https://github.com/jiaaro/pydub) - 音频处理库

---

⭐ 如果这个项目对你有帮助，请给个 Star！

📧 有问题或建议？[提交 Issue](https://github.com/qi-mooo/tts-api/issues) 或联系项目维护者。