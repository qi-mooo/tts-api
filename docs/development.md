# 开发指南

本指南面向希望参与 TTS API 项目开发或基于此项目进行二次开发的开发者。

## 开发环境设置

### 系统要求

- **Python**: 3.8+（推荐 3.10+）
- **Git**: 最新版本
- **IDE**: VS Code, PyCharm 或其他 Python IDE
- **操作系统**: Linux, macOS, Windows

### 环境准备

```bash
# 1. 克隆项目
git clone https://github.com/qi-mooo/tts-api.git
cd tts-api

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 初始化语音系统
./venv/bin/python3 scripts/install_voices.py

# 5. 配置开发环境
cp config.json.template config.json
# 编辑 config.json 设置开发配置

# 6. 运行测试
./venv/bin/python3 -m pytest tests/ -v
```

### 开发工具配置

#### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.pylintEnabled": false,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        "venv/": true
    }
}
```

创建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: TTS API",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app_enhanced.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "TTS_DEBUG": "true"
            }
        },
        {
            "name": "Python: Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

#### Git 配置

创建 `.gitignore`：

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Configuration
config.json
.env

# Data
data/
cache/

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Temporary
tmp/
temp/
```

## 项目架构

### 目录结构

```
tts-api/
├── admin/                  # Web 管理控制台
│   ├── admin_controller.py
│   ├── flask_integration.py
│   └── templates/
├── audio_cache/           # 音频缓存模块
│   ├── audio_cache.py
│   └── cache_manager.py
├── config/                # 配置管理
│   ├── config_manager.py
│   └── config_models.py
├── dictionary/            # 字典服务
│   ├── dictionary_service.py
│   └── rules/
├── error_handler/         # 错误处理
│   ├── error_handler.py
│   └── exceptions.py
├── health_check/          # 健康检查
│   ├── health_monitor.py
│   └── checks/
├── logger/                # 日志系统
│   ├── structured_logger.py
│   ├── flask_integration.py
│   └── formatters.py
├── restart/               # 重启功能
│   ├── restart_controller.py
│   └── restart_manager.py
├── scripts/               # 工具脚本
│   ├── install_voices.py
│   ├── update_voices.py
│   └── deploy_with_voices.sh
├── tests/                 # 测试文件
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                  # 文档
├── data/                  # 语音数据
├── logs/                  # 日志文件
├── app_enhanced.py        # 主应用文件
├── voice_manager.py       # 语音管理器
├── enhanced_tts_api.py    # TTS 服务
└── requirements.txt       # 依赖列表
```

### 核心模块

#### 1. 主应用 (app_enhanced.py)

```python
def create_enhanced_app() -> Flask:
    """创建增强版 Flask 应用"""
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = config_manager.admin.secret_key
    
    # 初始化组件
    error_handler = ErrorHandler(logger.logger)
    app.register_error_handler(Exception, error_handler_middleware(error_handler))
    
    # 注册路由
    register_routes(app)
    
    return app
```

#### 2. 语音管理器 (voice_manager.py)

```python
class VoiceManager:
    """语音管理器类"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._voices_data = None
        self._chinese_map = None
    
    def get_chinese_voices(self) -> List[Dict[str, Any]]:
        """获取中文语音列表"""
        data = self._load_voices_data()
        return data.get('chinese_voices', [])
    
    def validate_voice(self, voice_name: str) -> bool:
        """验证语音名称是否有效"""
        return self.get_voice_by_name(voice_name) is not None
```

#### 3. TTS 服务 (enhanced_tts_api.py)

```python
class EnhancedTTSService:
    """增强版 TTS 服务"""
    
    def __init__(self):
        self.audio_cache = AudioCache()
        self.dictionary_service = DictionaryService()
        self.logger = get_logger('tts_service')
    
    async def process_request(self, params: Dict[str, str]) -> Response:
        """处理 TTS 请求"""
        # 参数验证
        # 文本预处理
        # 语音合成
        # 缓存管理
        # 返回响应
```

## 开发工作流

### 双终端开发模式

#### 终端 1: 服务运行

```bash
# 开发模式启动
./venv/bin/python3 app_enhanced.py

# 或使用调试模式
TTS_DEBUG=true ./venv/bin/python3 app_enhanced.py

# 或使用 gunicorn（生产模式测试）
./venv/bin/gunicorn -c gunicorn_config.py app_enhanced:app --reload
```

#### 终端 2: 测试和开发

```bash
# 运行测试
./venv/bin/python3 -m pytest tests/ -v

# 运行特定测试
./venv/bin/python3 -m pytest tests/test_voice_manager.py -v

# 代码质量检查
./venv/bin/flake8 . --exclude=venv
./venv/bin/black . --exclude=venv

# 快速 API 测试
curl "http://localhost:8080/api/voices/stats"
./venv/bin/python3 test_voice_api.py --test voices
```

### 功能开发流程

#### 1. 创建功能分支

```bash
git checkout -b feature/new-voice-feature
```

#### 2. 编写测试（TDD）

```python
# tests/test_new_feature.py
import pytest
from voice_manager import VoiceManager

class TestNewFeature:
    def test_new_voice_feature(self):
        vm = VoiceManager()
        result = vm.new_voice_feature()
        assert result is not None
        assert len(result) > 0
```

#### 3. 实现功能

```python
# voice_manager.py
def new_voice_feature(self) -> List[Dict[str, Any]]:
    """新的语音功能"""
    # 实现逻辑
    return []
```

#### 4. 添加 API 端点

```python
# app_enhanced.py
@app.route('/api/voices/new-feature', methods=['GET'])
def new_voice_feature():
    """新语音功能 API"""
    try:
        vm = get_voice_manager()
        result = vm.new_voice_feature()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error("新功能失败", error=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

#### 5. 运行测试

```bash
# 运行新测试
./venv/bin/python3 -m pytest tests/test_new_feature.py -v

# 运行所有测试
./venv/bin/python3 -m pytest tests/ -v

# 测试 API 端点
curl "http://localhost:8080/api/voices/new-feature"
```

#### 6. 提交代码

```bash
git add .
git commit -m "feat: 添加新的语音功能

- 实现新语音功能逻辑
- 添加对应的 API 端点
- 添加单元测试和集成测试
- 更新文档"

git push origin feature/new-voice-feature
```

## 测试指南

### 测试结构

```
tests/
├── unit/                  # 单元测试
│   ├── test_voice_manager.py
│   ├── test_config_manager.py
│   └── test_tts_service.py
├── integration/           # 集成测试
│   ├── test_api_endpoints.py
│   ├── test_voice_api.py
│   └── test_admin_interface.py
├── fixtures/              # 测试数据
│   ├── sample_voices.json
│   └── test_config.json
└── conftest.py           # pytest 配置
```

### 编写测试

#### 单元测试示例

```python
# tests/unit/test_voice_manager.py
import pytest
from unittest.mock import Mock, patch
from voice_manager import VoiceManager

class TestVoiceManager:
    @pytest.fixture
    def voice_manager(self):
        return VoiceManager(data_dir="tests/fixtures")
    
    def test_get_chinese_voices(self, voice_manager):
        voices = voice_manager.get_chinese_voices()
        assert isinstance(voices, list)
        assert len(voices) > 0
        
        # 验证语音结构
        for voice in voices:
            assert 'ShortName' in voice
            assert 'Gender' in voice
            assert 'Locale' in voice
            assert voice['Locale'].startswith('zh-')
    
    def test_validate_voice_valid(self, voice_manager):
        result = voice_manager.validate_voice("zh-CN-YunjianNeural")
        assert result is True
    
    def test_validate_voice_invalid(self, voice_manager):
        result = voice_manager.validate_voice("invalid-voice")
        assert result is False
    
    @patch('voice_manager.Path.exists')
    def test_load_voices_data_file_not_exists(self, mock_exists, voice_manager):
        mock_exists.return_value = False
        data = voice_manager._load_voices_data()
        assert data == {'all_voices': [], 'chinese_voices': []}
```

#### 集成测试示例

```python
# tests/integration/test_voice_api.py
import pytest
import requests
from app_enhanced import create_enhanced_app

class TestVoiceAPI:
    @pytest.fixture
    def app(self):
        app = create_enhanced_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    def test_get_voices_success(self, client):
        response = client.get('/api/voices')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'voices' in data
        assert 'count' in data
        assert isinstance(data['voices'], list)
    
    def test_get_voices_with_filter(self, client):
        response = client.get('/api/voices?gender=Female')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        
        # 验证筛选结果
        for voice in data['voices']:
            assert voice['gender'] == 'Female'
    
    def test_validate_voice_success(self, client):
        response = client.post('/api/voices/validate', 
                             json={'voice_name': 'zh-CN-YunjianNeural'})
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['valid'] is True
        assert data['voice_info'] is not None
```

### 运行测试

```bash
# 运行所有测试
./venv/bin/python3 -m pytest tests/ -v

# 运行特定测试文件
./venv/bin/python3 -m pytest tests/unit/test_voice_manager.py -v

# 运行特定测试类
./venv/bin/python3 -m pytest tests/unit/test_voice_manager.py::TestVoiceManager -v

# 运行特定测试方法
./venv/bin/python3 -m pytest tests/unit/test_voice_manager.py::TestVoiceManager::test_get_chinese_voices -v

# 生成覆盖率报告
./venv/bin/python3 -m pytest tests/ --cov=. --cov-report=html

# 并行运行测试
./venv/bin/python3 -m pytest tests/ -n auto
```

## 代码质量

### 代码风格

项目使用以下工具确保代码质量：

- **Black**: 代码格式化
- **Flake8**: 代码检查
- **isort**: 导入排序
- **mypy**: 类型检查

#### 配置文件

创建 `pyproject.toml`：

```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["voice_manager", "config", "logger"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

创建 `.flake8`：

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist,
    *.egg-info
```

#### 运行代码质量检查

```bash
# 格式化代码
./venv/bin/black . --exclude=venv

# 排序导入
./venv/bin/isort . --skip=venv

# 代码检查
./venv/bin/flake8 . --exclude=venv

# 类型检查
./venv/bin/mypy voice_manager.py app_enhanced.py

# 一键运行所有检查
make lint  # 如果有 Makefile
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def get_voices_by_locale(self, locale: str) -> List[Dict[str, Any]]:
    """根据地区获取语音列表.

    Args:
        locale: 地区代码，如 'zh-CN'

    Returns:
        语音列表，每个语音包含名称、性别、地区等信息

    Raises:
        ValueError: 当地区代码格式不正确时

    Example:
        >>> vm = VoiceManager()
        >>> voices = vm.get_voices_by_locale('zh-CN')
        >>> len(voices) > 0
        True
    """
    if not locale or not isinstance(locale, str):
        raise ValueError("地区代码必须是非空字符串")
    
    all_voices = self.get_all_voices()
    return [voice for voice in all_voices if voice.get('Locale') == locale]
```

## 调试技巧

### 日志调试

```python
from logger.structured_logger import get_logger

logger = get_logger('debug')

def debug_function():
    logger.debug("开始处理", extra={'param': 'value'})
    
    try:
        # 业务逻辑
        result = process_data()
        logger.info("处理成功", extra={'result_count': len(result)})
        return result
    except Exception as e:
        logger.error("处理失败", error=e, extra={'context': 'debug_function'})
        raise
```

### 断点调试

```python
import pdb

def complex_function():
    data = get_data()
    
    # 设置断点
    pdb.set_trace()
    
    processed = process_data(data)
    return processed
```

### 性能分析

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 要分析的代码
    result = expensive_operation()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 显示前10个最耗时的函数
    
    return result
```

## 部署和发布

### 版本管理

使用语义化版本控制：

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

```bash
# 创建版本标签
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0
```

### CI/CD 配置

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 . --exclude=venv --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --exclude=venv --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Test with pytest
      run: |
        pytest tests/ -v --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Docker 构建

创建多阶段 Dockerfile：

```dockerfile
# 构建阶段
FROM python:3.10-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 运行阶段
FROM python:3.10-slim

WORKDIR /app

# 复制 Python 依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "app_enhanced.py"]
```

## 贡献指南

### 提交 Pull Request

1. **Fork 项目**
2. **创建功能分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 提交信息规范

使用 Conventional Commits 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(voice): 添加语音搜索功能

- 实现按关键词搜索语音
- 支持模糊匹配
- 添加搜索结果排序

Closes #123
```

### 代码审查清单

- [ ] 代码符合项目风格指南
- [ ] 添加了适当的测试
- [ ] 测试通过
- [ ] 文档已更新
- [ ] 没有引入安全漏洞
- [ ] 性能影响可接受
- [ ] 向后兼容性

## 常见问题

### 开发环境问题

#### 1. 虚拟环境问题

```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. 依赖冲突

```bash
# 清理 pip 缓存
pip cache purge

# 使用 pip-tools 管理依赖
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

#### 3. 测试失败

```bash
# 清理测试缓存
rm -rf .pytest_cache
rm -rf __pycache__

# 重新运行测试
pytest tests/ -v --tb=short
```

### 性能优化

#### 1. 代码性能分析

```python
import time
import functools

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

@timing_decorator
def slow_function():
    # 耗时操作
    pass
```

#### 2. 内存使用优化

```python
import tracemalloc

def memory_profile():
    tracemalloc.start()
    
    # 要分析的代码
    result = memory_intensive_operation()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    
    tracemalloc.stop()
    return result
```

---

更多开发相关信息请参考 [API 文档](api-reference.md) 和 [配置说明](configuration.md)。