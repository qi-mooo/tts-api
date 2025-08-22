"""
集成管理控制台的 TTS 应用

在原有 TTS 功能基础上，集成了 Web 管理控制台、错误处理、日志系统等功能
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

# 导入新的模块
from config.config_manager import config_manager
from dictionary.dictionary_service import DictionaryService
from logger.structured_logger import get_logger
from error_handler.error_handler import ErrorHandler, error_handler_middleware
from admin.flask_integration import init_admin_app

# 创建 Flask 应用
app = Flask(__name__)

# 初始化日志系统
logger = get_logger('tts_app', config_manager.logging.__dict__)

# 初始化错误处理器
error_handler = ErrorHandler(logger.logger)

# 初始化字典服务
dictionary_service = DictionaryService(config_manager.dictionary.rules_file)

# 初始化管理控制台
init_admin_app(app)

# 注册全局错误处理器
app.register_error_handler(Exception, error_handler_middleware(error_handler))


class AudioCache:
    def __init__(self, size_limit=None, time_limit=None):
        self.size_limit = size_limit or config_manager.tts.cache_size_limit
        self.time_limit = time_limit or config_manager.tts.cache_time_limit
        self.cache = []  # 存储音频段及其时间戳的列表
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
    def handle_text(self, text):
        # 首先通过字典服务处理文本
        if config_manager.dictionary.enabled:
            text = dictionary_service.process_text(text)
        
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
        logger.info(f"edge-tts 合成: {text}", 
                   voice=voice_name, speed=speed, text_length=len(text))
        
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
        
        logger.info(f"音频生成成功", 
                   text_length=len(text), audio_duration=len(audio_segment))
        
        return audio_segment
        
    except Exception as e:
        logger.error(f"edge-tts 合成失败: {text}", error=e, 
                    voice=voice_name, speed=speed)
        raise


@app.route('/api', methods=['GET'])
def api():
    """TTS API 端点"""
    request_start_time = time.time()
    
    try:
        # 设置请求ID用于日志追踪
        import uuid
        request_id = str(uuid.uuid4())[:8]
        logger.set_request_id(request_id)
        
        text = request.args.get('text')
        speed = request.args.get('speed', default=config_manager.tts.default_speed)
        narr_voice = request.args.get('narr', default=config_manager.tts.narration_voice)
        dlg_voice = request.args.get('dlg', default=config_manager.tts.dialogue_voice)
        all_voice = request.args.get('all')  # 不分旁白对话覆盖发声人

        logger.info(f"收到 TTS 请求", 
                   text_preview=text[:50] if text else None,
                   speed=speed, narr_voice=narr_voice, dlg_voice=dlg_voice)

        if not text:
            raise ValueError("Missing 'text' parameter")

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
                    logger.error(f"音频生成子任务异常", error=e)

        if audio_segments:
            combined_audio = sum(audio_segments)
            output_io = io.BytesIO()
            combined_audio.export(output_io, format="webm")
            output_io.seek(0)
            
            # 记录性能日志
            duration = time.time() - request_start_time
            logger.performance('tts_request', duration,
                             text_length=len(text),
                             segments_count=len(audio_segments),
                             audio_duration=len(combined_audio))
            
            return Response(output_io, mimetype='audio/webm', 
                          headers={'X-Audio-Duration': str(len(combined_audio))})

        raise ValueError("No audio generated")
        
    except Exception as e:
        duration = time.time() - request_start_time
        logger.error(f"TTS 请求处理失败", error=e, duration=duration)
        return error_handler.handle_error(e, {
            'request_id': getattr(logger, '_request_local', {}).get('request_id', 'unknown'),
            'text_length': len(text) if text else 0
        })


@app.route('/audio', methods=['GET'])
def get_audio():
    """获取缓存的音频"""
    try:
        combined_audio = audio_cache.combine()
        if combined_audio is None:
            return jsonify({"error": "No audio generated yet"}), 404

        output_io = io.BytesIO()
        combined_audio.export(output_io, format="webm")
        output_io.seek(0)

        logger.info("返回缓存音频", audio_duration=len(combined_audio))
        
        return output_io.getvalue(), 200, {'Content-Type': 'audio/webm'}
        
    except Exception as e:
        logger.error("获取缓存音频失败", error=e)
        return error_handler.handle_error(e)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 检查各个组件状态
        status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0',
            'uptime': time.time() - app.config.get('START_TIME', time.time()),
            'components': {
                'config': config_manager.validate(),
                'dictionary': config_manager.dictionary.enabled,
                'cache': len(audio_cache.cache) > 0 if audio_cache.cache else True,
                'edge_tts': True  # 这里可以实现实际的 edge-tts 检查
            }
        }
        
        # 如果所有组件都正常，返回 200，否则返回 503
        all_healthy = all(status['components'].values())
        status_code = 200 if all_healthy else 503
        
        if not all_healthy:
            status['status'] = 'unhealthy'
        
        logger.info("健康检查", status=status['status'], components=status['components'])
        
        return jsonify(status), status_code
        
    except Exception as e:
        logger.error("健康检查失败", error=e)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 503


if __name__ == '__main__':
    # 记录应用启动时间
    app.config['START_TIME'] = time.time()
    
    logger.info("TTS 应用启动", 
               host=config_manager.system.host,
               port=config_manager.system.port,
               debug=config_manager.system.debug)
    
    app.run(
        host=config_manager.system.host,
        port=config_manager.system.port,
        debug=config_manager.system.debug
    )