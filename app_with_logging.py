"""
集成结构化日志系统的 Flask 应用

这是原始 app.py 的增强版本，集成了新的结构化日志系统
"""

from flask import Flask, request, jsonify, Response
import io
from concurrent.futures import ThreadPoolExecutor
import time
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import traceback
import asyncio
import edge_tts

# 导入新的日志系统
from logger import get_logger, LoggingConfig
from logger.flask_integration import FlaskLoggerIntegration, log_api_call, log_function_call

app = Flask(__name__)

# 配置日志系统
logging_config = LoggingConfig.from_env()
flask_logger = FlaskLoggerIntegration(app, logging_config)

# 获取应用日志记录器
app_logger = get_logger('tts_app', logging_config)
audio_logger = get_logger('audio_processing', logging_config)
cache_logger = get_logger('audio_cache', logging_config)

# 默认语音名称和参数
NARRATION_VOICE_NAME = "zh-CN-YunjianNeural"
DIALOGUE_VOICE_NAME = "zh-CN-XiaoyiNeural"
SPEED = 1.2  # 语速 1.0 为正常速度
CACHE_SIZE_LIMIT = 10 * 1024 * 1024  # 最大缓存大小（字节），这里设置为 10 MB
CACHE_TIME_LIMIT = 20 * 60  # 缓存音频段的有效时间（秒）


class AudioCache:
    """音频缓存类 - 增强版本带日志"""
    
    def __init__(self, size_limit=CACHE_SIZE_LIMIT, time_limit=CACHE_TIME_LIMIT):
        self.cache = []  # 存储音频段及其时间戳的列表
        self.size_limit = size_limit
        self.time_limit = time_limit
        self.current_size = 0  # 跟踪当前缓存的总大小
        
        cache_logger.info(
            "Audio cache initialized",
            size_limit_mb=size_limit / (1024 * 1024),
            time_limit_seconds=time_limit
        )

    @log_function_call("audio_cache_add")
    def add(self, audio_segment):
        """添加音频段到缓存"""
        current_time = time.time()
        audio_size = len(audio_segment.raw_data)  # 获取音频段的大小（字节）

        # 移除过期的音频段
        original_count = len(self.cache)
        self.cache = [(seg, ts) for seg, ts in self.cache if (current_time - ts) <= self.time_limit]
        expired_count = original_count - len(self.cache)
        
        if expired_count > 0:
            cache_logger.debug(f"Removed {expired_count} expired audio segments")
        
        self.current_size = sum(len(seg.raw_data) for seg, _ in self.cache)  # 更新当前大小

        # 移除音频段直到有足够的空间添加新段
        removed_count = 0
        while self.current_size + audio_size > self.size_limit and self.cache:
            oldest_segment, _ = self.cache.pop(0)  # 移除最旧的音频段
            self.current_size -= len(oldest_segment.raw_data)  # 减少总大小
            removed_count += 1

        if removed_count > 0:
            cache_logger.info(f"Removed {removed_count} segments due to size limit")

        # 添加新音频段
        self.cache.append((audio_segment, current_time))
        self.current_size += audio_size  # 增加总大小
        
        cache_logger.debug(
            "Audio segment added to cache",
            segment_size_bytes=audio_size,
            total_segments=len(self.cache),
            total_size_mb=round(self.current_size / (1024 * 1024), 2)
        )

    @log_function_call("audio_cache_combine")
    def combine(self):
        """合并缓存中的音频段"""
        if not self.cache:
            cache_logger.warning("No audio segments in cache to combine")
            return None
            
        # 仅组合未过期的音频段
        current_time = time.time()
        valid_segments = [seg for seg, ts in self.cache if (current_time - ts) <= self.time_limit]
        
        if not valid_segments:
            cache_logger.warning("No valid audio segments found in cache")
            return None
            
        cache_logger.info(
            "Combining audio segments",
            segment_count=len(valid_segments),
            total_duration_estimate=len(valid_segments) * 2  # 估算秒数
        )
        
        return sum(valid_segments)


audio_cache = AudioCache()


class SpeechRule:
    """语音规则处理类 - 增强版本带日志"""
    
    @log_function_call("speech_rule_handle_text")
    def handle_text(self, text):
        """处理文本，分离旁白和对话"""
        app_logger.debug("Processing text with speech rules", text_length=len(text))
        
        result = []
        tmp_str = ""
        end_tag = "narration"
        quote_count = 0

        for char in text:
            if char in ['"', '"']:
                if tmp_str.strip():
                    result.append({"text": tmp_str.strip(), "tag": end_tag})
                tmp_str = ""
                end_tag = "dialogue" if char == '"' else "narration"
                quote_count += 1
            else:
                tmp_str += char

        if tmp_str.strip():
            result.append({"text": tmp_str.strip(), "tag": end_tag})

        app_logger.info(
            "Text processing completed",
            segments_count=len(result),
            quote_pairs=quote_count // 2,
            narration_segments=sum(1 for r in result if r['tag'] == 'narration'),
            dialogue_segments=sum(1 for r in result if r['tag'] == 'dialogue')
        )

        return result


@log_function_call("fetch_audio")
def fetch_audio(segment, speed, voice_name):
    """
    使用 edge-tts 生成音频，返回 pydub.AudioSegment
    """
    text = segment['text']
    rate = f"{float(speed) * 100 - 100:+.0f}%"  # edge-tts 语速格式，如+20%
    
    audio_logger.info(
        "Starting audio synthesis",
        text_preview=text[:50] + "..." if len(text) > 50 else text,
        text_length=len(text),
        voice_name=voice_name,
        speed_rate=rate,
        segment_tag=segment.get('tag', 'unknown')
    )
    
    try:
        communicate = edge_tts.Communicate(text, voice_name, rate=rate)
        audio_bytes = b''
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_audio():
            nonlocal audio_bytes
            chunk_count = 0
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
                    chunk_count += 1
            
            audio_logger.debug(f"Received {chunk_count} audio chunks")
        
        loop.run_until_complete(get_audio())
        
        if not audio_bytes:
            raise Exception("No audio data received from edge-tts")
        
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        audio_cache.add(audio_segment)
        
        audio_logger.info(
            "Audio synthesis completed successfully",
            audio_size_bytes=len(audio_bytes),
            audio_duration_ms=len(audio_segment),
            voice_name=voice_name
        )
        
        return audio_segment
        
    except Exception as e:
        audio_logger.error(
            "Audio synthesis failed",
            error=e,
            text_preview=text[:100],
            voice_name=voice_name,
            speed_rate=rate
        )
        return None


@app.route('/api', methods=['GET'])
@log_api_call
def api():
    """TTS API 端点 - 增强版本"""
    try:
        text = request.args.get('text')
        speed = request.args.get('speed', default=SPEED)  # 默认语速
        narr_voice = request.args.get('narr', default=NARRATION_VOICE_NAME)  # 默认旁白语音
        dlg_voice = request.args.get('dlg', default=DIALOGUE_VOICE_NAME)  # 默认对话语音
        all_voice = request.args.get('all')  # 不分旁白对话覆盖发声人

        app_logger.info(
            "TTS API request received",
            text_length=len(text) if text else 0,
            speed=speed,
            narr_voice=narr_voice,
            dlg_voice=dlg_voice,
            all_voice=all_voice,
            client_ip=request.remote_addr
        )

        if not text:
            app_logger.warning("Missing text parameter in request")
            return jsonify({"error": "Missing 'text' parameter"}), 400

        speech_rule = SpeechRule()
        handled_text = speech_rule.handle_text(text)

        audio_segments = []
        failed_segments = 0
        
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
                    else:
                        failed_segments += 1
                except Exception as e:
                    failed_segments += 1
                    audio_logger.error(
                        "Audio generation subtask failed",
                        error=e,
                        segment_text=futures[future]['text'][:50]
                    )

        if failed_segments > 0:
            app_logger.warning(f"{failed_segments} audio segments failed to generate")

        if audio_segments:
            app_logger.info(
                "Combining audio segments",
                successful_segments=len(audio_segments),
                failed_segments=failed_segments
            )
            
            combined_audio = sum(audio_segments)
            output_io = io.BytesIO()
            combined_audio.export(output_io, format="webm")
            output_io.seek(0)
            
            app_logger.info(
                "TTS request completed successfully",
                total_segments=len(audio_segments),
                output_size_bytes=len(output_io.getvalue()),
                audio_duration_ms=len(combined_audio)
            )
            
            return Response(output_io, mimetype='audio/webm', headers={'X-Audio-Duration': str(len(combined_audio))})

        app_logger.error("No audio generated for request", original_text=text[:100])
        return jsonify({"error": "No audio generated", "text": text}), 404
        
    except Exception as e:
        app_logger.error("Unhandled exception in /api endpoint", error=e)
        from flask import g
        return jsonify({
            "error": "Internal server error", 
            "detail": str(e),
            "request_id": getattr(g, 'request_id', 'unknown')
        }), 500


@app.route('/audio', methods=['GET'])
@log_api_call
def get_audio():
    """获取缓存音频端点"""
    app_logger.info("Audio cache request received")
    
    combined_audio = audio_cache.combine()
    if combined_audio is None:
        app_logger.warning("No audio available in cache")
        return jsonify({"error": "No audio generated yet"}), 404

    output_io = io.BytesIO()
    combined_audio.export(output_io, format="webm")
    output_io.seek(0)
    
    app_logger.info(
        "Cache audio served",
        audio_size_bytes=len(output_io.getvalue()),
        audio_duration_ms=len(combined_audio)
    )

    return output_io.getvalue(), 200, {'Content-Type': 'audio/webm'}


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    app_logger.debug("Health check requested")
    
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "cache_segments": len(audio_cache.cache),
        "cache_size_mb": round(audio_cache.current_size / (1024 * 1024), 2)
    }
    
    return jsonify(status), 200


if __name__ == '__main__':
    app_logger.info(
        "TTS application starting",
        narration_voice=NARRATION_VOICE_NAME,
        dialogue_voice=DIALOGUE_VOICE_NAME,
        default_speed=SPEED,
        cache_size_limit_mb=CACHE_SIZE_LIMIT / (1024 * 1024),
        cache_time_limit_minutes=CACHE_TIME_LIMIT / 60
    )
    
    app.run(host='0.0.0.0', port=8080, debug=False)