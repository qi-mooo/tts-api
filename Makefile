# TTS API Makefile
# 简化常用操作的命令

.PHONY: help install setup build run test clean docker-build docker-run docker-compose-up docker-compose-down

# 默认目标
help:
	@echo "TTS API 项目管理命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  install          安装依赖包"
	@echo "  setup            初始化项目配置"
	@echo "  run              运行开发服务器"
	@echo "  test             运行测试"
	@echo "  clean            清理临时文件"
	@echo ""
	@echo "Docker 部署:"
	@echo "  docker-build     构建 Docker 镜像"
	@echo "  docker-run       运行 Docker 容器"
	@echo "  docker-compose-up    启动 Docker Compose 服务"
	@echo "  docker-compose-down  停止 Docker Compose 服务"
	@echo ""
	@echo "维护操作:"
	@echo "  logs             查看应用日志"
	@echo "  health           检查服务健康状态"
	@echo "  backup           备份配置文件"
	@echo ""

# 开发环境设置
install:
	@echo "安装依赖包..."
	./venv/bin/pip install -r requirements.txt

setup:
	@echo "初始化项目配置..."
	python3 setup.py --init
	@echo "请设置管理员密码: make password PASSWORD=your-password"

password:
	@if [ -z "$(PASSWORD)" ]; then \
		echo "请提供密码: make password PASSWORD=your-password"; \
		exit 1; \
	fi
	python3 setup.py --password $(PASSWORD)

verify:
	@echo "验证环境配置..."
	python3 setup.py --verify

# 运行服务
run:
	@echo "启动开发服务器..."
	./venv/bin/python3 enhanced_tts_api.py

run-prod:
	@echo "启动生产服务器..."
	./venv/bin/gunicorn -b 0.0.0.0:8080 enhanced_tts_api:app \
		--workers 4 --timeout 120 --log-level info

# 测试
test:
	@echo "运行单元测试..."
	./venv/bin/python3 -m unittest discover tests -v

test-coverage:
	@echo "运行测试覆盖率..."
	./venv/bin/coverage run -m unittest discover tests
	./venv/bin/coverage report
	./venv/bin/coverage html

# Docker 操作
docker-build:
	@echo "构建 Docker 镜像..."
	docker build -t tts-api .

docker-run:
	@echo "运行 Docker 容器..."
	docker run -d \
		--name tts-api \
		-p 8080:8080 \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/config.json:/app/config.json \
		-e TTS_ADMIN_PASSWORD=admin123 \
		tts-api

docker-stop:
	@echo "停止 Docker 容器..."
	docker stop tts-api || true
	docker rm tts-api || true

# Docker Compose 操作
docker-compose-up:
	@echo "启动 Docker Compose 服务..."
	docker-compose up -d

docker-compose-down:
	@echo "停止 Docker Compose 服务..."
	docker-compose down

docker-compose-logs:
	@echo "查看 Docker Compose 日志..."
	docker-compose logs -f

# 维护操作
logs:
	@if [ -f "logs/app.log" ]; then \
		tail -f logs/app.log; \
	else \
		echo "日志文件不存在"; \
	fi

health:
	@echo "检查服务健康状态..."
	@curl -s http://localhost:8080/health | python3 -m json.tool || echo "服务不可用"

backup:
	@echo "备份配置文件..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		config.json dictionary/rules.json .env 2>/dev/null || true
	@echo "备份完成: backups/"

# 清理操作
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -path "./logs/*" -mtime +7 -delete 2>/dev/null || true
	@echo "清理完成"

clean-all: clean
	@echo "清理所有生成文件..."
	rm -rf logs/*.log
	rm -rf backups/
	docker system prune -f

# 代码质量检查
lint:
	@echo "代码质量检查..."
	./venv/bin/flake8 . --exclude=venv,__pycache__ --max-line-length=88

format:
	@echo "代码格式化..."
	./venv/bin/black . --exclude=venv

# 开发工具
dev-install:
	@echo "安装开发依赖..."
	./venv/bin/pip install black flake8 coverage pytest

dev-setup: dev-install setup
	@echo "开发环境设置完成"

# 部署相关
deploy-check:
	@echo "部署前检查..."
	@make verify
	@make test
	@echo "部署检查完成"

# 监控
monitor:
	@echo "系统监控..."
	@while true; do \
		echo "=== $(shell date) ==="; \
		make health; \
		echo ""; \
		sleep 30; \
	done

# 快速启动（开发环境）
quick-start:
	@echo "快速启动开发环境..."
	@make setup
	@make install
	@echo "请设置管理员密码后运行: make run"

# 快速启动（Docker）
quick-docker:
	@echo "快速启动 Docker 环境..."
	@make docker-build
	@make docker-run
	@echo "服务已启动，访问 http://localhost:8080"