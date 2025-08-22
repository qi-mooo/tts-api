FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y wget xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 安装 FFmpeg
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-*-static ffmpeg-release-amd64-static.tar.xz && \
    apt-get remove --purge -y wget xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 创建必要的目录
RUN mkdir -p logs templates

# 复制应用代码和模块
COPY config/ ./config/
COPY error_handler/ ./error_handler/
COPY logger/ ./logger/
COPY dictionary/ ./dictionary/
COPY admin/ ./admin/
COPY health_check/ ./health_check/
COPY restart/ ./restart/
COPY audio_cache/ ./audio_cache/
COPY templates/ ./templates/
COPY *.py ./
COPY config.json.template ./config.json

# 设置环境变量
ENV FLASK_APP=enhanced_tts_api.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["gunicorn", "-b", "0.0.0.0:5000", "enhanced_tts_api:app", \
     "--workers=4", "--worker-class=sync", "--timeout=120", \
     "--log-level=info", "--capture-output", \
     "--access-logfile=-", "--error-logfile=-"]
