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

app = Flask(__name__)

# gunicorn 会自动管理日志，这里不再配置 logging.basicConfig

# 默认语音名称和参数
NARRATION_VOICE_NAME = "zh-CN-YunjianNeural"
DIALOGUE_VOICE_NAME = "zh-CN-XiaoyiNeural"
SPEED = 1.2  # 语速 1.0 为正常速度
CACHE_SIZE_LIMIT = 10 * 1024 * 1024  # 最大缓存大小（字节），这里设置为 10 MB
CACHE_TIME_LIMIT = 20 * 60  # 缓存音频段的有效时间（秒）

class AudioCache:
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

audio_cache = AudioCache()

class SpeechRule:
    def handle_text(self, text):
        result = []
        tmp_str = ""
        end_tag = "narration"

        for char in text:
            if char in ['“', '”']:
                if tmp_str.strip():
                    result.append({"text": tmp_str.strip(), "tag": end_tag})
                tmp_str = ""
                end_tag = "dialogue" if char == '“' else "narration"
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
        logging.info(f"edge-tts 合成: {text}")
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
        logging.error(f"edge-tts 合成失败: {e}\n{traceback.format_exc()}")
        return None

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"全局异常捕获: {e}\n{traceback.format_exc()}")
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500

@app.route('/api', methods=['GET'])
def api():
    try:
        text = request.args.get('text')
        speed = request.args.get('speed', default=SPEED)  # 默认语速
        narr_voice = request.args.get('narr', default=NARRATION_VOICE_NAME)  # 默认旁白语音
        dlg_voice = request.args.get('dlg', default=DIALOGUE_VOICE_NAME)  # 默认对话语音
        all_voice = request.args.get('all')  # 不分旁白对话覆盖发声人

        logging.info(f"收到请求: {text}")

        if not text:
            return jsonify({"error": "Missing 'text' parameter"}), 400

        speech_rule = SpeechRule()
        handled_text = speech_rule.handle_text(text)

        audio_segments = []
        with ThreadPoolExecutor(max_workers=10) as executor:
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
                    logging.error(f"音频生成子任务异常: {e}\n{traceback.format_exc()}")

        if audio_segments:
            combined_audio = sum(audio_segments)
            output_io = io.BytesIO()
            combined_audio.export(output_io, format="webm")
            output_io.seek(0)
            return Response(output_io, mimetype='audio/webm', headers={'X-Audio-Duration': '0'})

        return jsonify({"error": "No audio generated", "text": text}), 404
    except Exception as e:
        logging.error(f"/api 路由异常: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

@app.route('/audio', methods=['GET'])
def get_audio():
    combined_audio = audio_cache.combine()
    if combined_audio is None:
        return jsonify({"error": "No audio generated yet"}), 404

    output_io = io.BytesIO()
    combined_audio.export(output_io, format="webm")
    output_io.seek(0)

    return output_io.getvalue(), 200, {'Content-Type': 'audio/webm'}

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "TTS API",
        "timestamp": time.time(),
        "cache_size": len(audio_cache.cache),
        "cache_memory": f"{audio_cache.current_size / 1024 / 1024:.2f} MB"
    }), 200

@app.route('/admin', methods=['GET'])
def admin_panel():
    """简单的管理面板"""
    return jsonify({
        "message": "TTS API 管理面板",
        "service": "TTS API",
        "status": "running",
        "endpoints": {
            "/api": "TTS 音频生成",
            "/audio": "获取缓存音频",
            "/health": "健康检查",
            "/admin": "管理面板"
        },
        "cache_info": {
            "segments": len(audio_cache.cache),
            "memory_usage": f"{audio_cache.current_size / 1024 / 1024:.2f} MB",
            "memory_limit": f"{audio_cache.size_limit / 1024 / 1024:.2f} MB"
        }
    }), 200

@app.route('/favicon.ico')
def favicon():
    """处理 favicon 请求"""
    return '', 204

@app.route('/')
def index():
    """首页"""
    return jsonify({
        "service": "TTS API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/api": "TTS 音频生成 - GET ?text=文本&speed=语速&narr=旁白语音&dlg=对话语音&all=统一语音",
            "/audio": "获取缓存音频 - GET",
            "/health": "健康检查 - GET",
            "/admin": "管理面板 - GET"
        },
        "example": "/api?text=你好世界&speed=1.2"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
