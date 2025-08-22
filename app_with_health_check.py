"""
集成健康检查功能的TTS应用示例

演示如何将健康检查功能集成到现有的Flask TTS应用中
"""

from flask import Flask, request, jsonify, Response
import io
from concurrent.futures import ThreadPoolExecutor
import time
import logging
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import traceback
import asyncio
import edge_tts

# 导入健康检查模块
from health_check.flask_integration import setup_health_monitoring
from config.config_manager import config_manager
from logger.structured_logger import get_logger

# 创建Flask应用
app = Flask(__name__)

# 设置日志
logger = get_logger('tts_app', config_manager.get_config_dict()['logging'])

# 默认语音名称和参数（从配置管理器获取）
NARRATION_VOICE_NAME = config_manager.tts.narration_voice
DIALOGUE_VOICE_NAME = config_manager.tts.dialogue_voice
SPEED = config_manager.tts.default_speed
CACHE_SIZE_LIMIT = config_manager.tts.cache_size_limit
CACHE_TIME_LIMIT = config_manager.tts.cache_time_limit


class AudioCache:
    """音频缓存类"""
    
    def __init__(self, size_limit=CACHE_SIZE_LIMIT, time_limit=CACHE_TIME_LIMIT):
        self.cache = []  # 存储音频段及其时间戳的列表
        self.size_limit = size_limit
        self.time_limit = time_limit
        self.current_size = 0  # 跟踪当前缓存的总大小

    def add(self, audio_segment):
        current_time = time.time()
        audio_size = len(audio_segment.raw_data)  # 获取音频段的大小（字节）

        # 移除过期的音频段
        self.cache = [(seg, ts) for seg, ts in self.cache if (current_time - ts) <= self.time_limit]
        self.current_size = sum(len(seg.raw_data) for seg, _ in self.cache)  # 更新当前大小

        # 移除音频段直到有足够的空间添加新段
        while self.current_size + audio_size > self.size_limit and self.cache:
            oldest_segment, _ = self.cache.pop(0)  # 移除最旧的音频段
            self.current_size -= len(oldest_segment.raw_data)  # 减少总大小

        # 添加新音频段
        self.cache.append((audio_segment, current_time))
        self.current_size += audio_size  # 增加总大小

    def combine(self):
        if not self.cache:
            return None
        # 仅组合未过期的音频段
        valid_segments = [seg for seg, ts in self.cache if (time.time() - ts) <= self.time_limit]
        return sum(valid_segments) if valid_segments else None


# 创建音频缓存实例
audio_cache = AudioCache()


class SpeechRule:
    """语音规则处理类"""
    
    def handle_text(self, text):
        result = []
        tmp_str = ""
        end_tag = "narration"

        for char in text:
            if char in ['"', '"']:
                if tmp_str.strip():
                    result.append({"text": tmp_str.strip(), "tag": end_tag})
                tmp_str = ""
                end_tag = "dialogue" if char == '"' else "narration"
            else:
                tmp_str += char

        if tmp_str.strip():
            result.append({"text": tmp_str.strip(), "tag": end_tag})

        return result


def fetch_audio(segment, speed, voice_name):
    """
    使用 edge-tts 生成音频，返回 pydub.AudioSegment
    """
    text = segment['text']
    rate = f"{float(speed) * 100 - 100:+.0f}%"  # edge-tts 语速格式，如+20%
    try:
        logger.info(f"edge-tts 合成: {text}")
        communicate = edge_tts.Communicate(text, voice_name, rate=rate)
        audio_bytes = b''
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_audio():
            nonlocal audio_bytes
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
        
        loop.run_until_complete(get_audio())
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        audio_cache.add(audio_segment)
        return audio_segment
    except Exception as e:
        logger.error(f"edge-tts 合成失败: {e}", error=e)
        return None


@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器"""
    logger.error(f"全局异常捕获: {e}", error=e)
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


@app.route('/api', methods=['GET'])
def api():
    """TTS API端点"""
    try:
        text = request.args.get('text')
        speed = request.args.get('speed', default=SPEED)  # 默认语速
        narr_voice = request.args.get('narr', default=NARRATION_VOICE_NAME)  # 默认旁白语音
        dlg_voice = request.args.get('dlg', default=DIALOGUE_VOICE_NAME)  # 默认对话语音
        all_voice = request.args.get('all')  # 不分旁白对话覆盖发声人

        logger.info(f"收到请求: {text}")

        if not text:
            return jsonify({"error": "Missing 'text' parameter"}), 400

        speech_rule = SpeechRule()
        handled_text = speech_rule.handle_text(text)

        audio_segments = []
        with ThreadPoolExecutor(max_workers=config_manager.system.max_workers) as executor:
            futures = {}
            for item in handled_text:
                # 确定使用的语音名称
                voice_name = all_voice if all_voice else (narr_voice if item['tag'] == "narration" else dlg_voice)
                futures[executor.submit(fetch_audio, item, speed, voice_name)] = item
            
            for future in futures:
                try:
                    audio_segment = future.result()
                    if audio_segment:
                        audio_segments.append(audio_segment)
                except Exception as e:
                    logger.error(f"音频生成子任务异常: {e}", error=e)

        if audio_segments:
            combined_audio = sum(audio_segments)
            output_io = io.BytesIO()
            combined_audio.export(output_io, format="webm")
            output_io.seek(0)
            return Response(output_io, mimetype='audio/webm', headers={'X-Audio-Duration': '0'})

        return jsonify({"error": "No audio generated", "text": text}), 404
    except Exception as e:
        logger.error(f"/api 路由异常: {e}", error=e)
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


@app.route('/audio', methods=['GET'])
def get_audio():
    """获取缓存音频端点"""
    combined_audio = audio_cache.combine()
    if combined_audio is None:
        return jsonify({"error": "No audio generated yet"}), 404

    output_io = io.BytesIO()
    combined_audio.export(output_io, format="webm")
    output_io.seek(0)

    return output_io.getvalue(), 200, {'Content-Type': 'audio/webm'}


@app.route('/')
def index():
    """首页"""
    return jsonify({
        "message": "TTS服务运行中",
        "version": "1.0.0",
        "endpoints": {
            "tts_api": "/api?text=你好世界",
            "health_check": "/health",
            "detailed_health": "/health/detailed",
            "readiness": "/health/ready",
            "liveness": "/health/live"
        }
    })


if __name__ == '__main__':
    # 设置健康监控
    setup_health_monitoring(
        app=app,
        cache_instance=audio_cache,
        app_version="1.0.0"
    )
    
    logger.info("TTS应用启动，健康检查功能已启用")
    
    # 启动应用
    app.run(
        host=config_manager.system.host,
        port=config_manager.system.port,
        debug=config_manager.system.debug
    )