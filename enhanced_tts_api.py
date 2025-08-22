"""
增强版 TTS API - 集成错误处理、参数验证、字典服务和性能监控

重构现有的 /api 端点，提供更好的错误处理、参数验证和用户体验。
"""

from flask import Flask, request, jsonify, Response
import io
import time
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Tuple
from pydub import AudioSegment
import edge_tts

# 导入自定义模块
from error_handler.error_handler import ErrorHandler, error_handler_middleware
from error_handler.exceptions import (
    TTSError, ServiceUnavailableError, AudioGenerationError,
    ValidationError, SystemResourceError
)
from dictionary.dictionary_service import DictionaryService
from logger.structured_logger import get_logger, performance_timer
from config.config_manager import config_manager


class RequestValidator:
    """请求参数验证器"""
    
    def __init__(self):
        self.logger = get_logger('request_validator')
    
    def validate_tts_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证 TTS 请求参数
        
        Args:
            args: 请求参数字典
            
        Returns:
            验证后的参数字典
            
        Raises:
            ValidationError: 参数验证失败时
        """
        validated = {}
        
        # 验证文本参数
        text = args.get('text', '').strip()
        if not text:
            raise ValidationError(
                field_name='text',
                message='文本参数不能为空',
                details={'provided_value': args.get('text')}
            )
        
        if len(text) > 5000:  # 限制文本长度
            raise ValidationError(
                field_name='text',
                message='文本长度不能超过5000个字符',
                details={'text_length': len(text), 'max_length': 5000}
            )
        
        validated['text'] = text
        
        # 验证语速参数
        try:
            speed = float(args.get('speed', config_manager.tts.default_speed))
            if not (0.1 <= speed <= 3.0):
                raise ValidationError(
                    field_name='speed',
                    message='语速必须在0.1到3.0之间',
                    details={'provided_value': speed, 'valid_range': [0.1, 3.0]}
                )
            validated['speed'] = speed
        except (ValueError, TypeError):
            raise ValidationError(
                field_name='speed',
                message='语速参数必须是有效的数字',
                details={'provided_value': args.get('speed')}
            )
        
        # 验证语音参数
        narr_voice = args.get('narr', config_manager.tts.narration_voice)
        dlg_voice = args.get('dlg', config_manager.tts.dialogue_voice)
        all_voice = args.get('all')
        
        # 验证语音名称格式（简单验证）
        valid_voice_pattern = r'^[a-zA-Z]{2}-[a-zA-Z]{2}-\w+$'
        import re
        
        if narr_voice and not re.match(valid_voice_pattern, narr_voice):
            raise ValidationError(
                field_name='narr',
                message='旁白语音名称格式无效',
                details={'provided_value': narr_voice, 'expected_pattern': valid_voice_pattern}
            )
        
        if dlg_voice and not re.match(valid_voice_pattern, dlg_voice):
            raise ValidationError(
                field_name='dlg',
                message='对话语音名称格式无效',
                details={'provided_value': dlg_voice, 'expected_pattern': valid_voice_pattern}
            )
        
        if all_voice and not re.match(valid_voice_pattern, all_voice):
            raise ValidationError(
                field_name='all',
                message='统一语音名称格式无效',
                details={'provided_value': all_voice, 'expected_pattern': valid_voice_pattern}
            )
        
        validated['narr_voice'] = narr_voice
        validated['dlg_voice'] = dlg_voice
        validated['all_voice'] = all_voice
        
        return validated


class EnhancedSpeechRule:
    """增强版语音规则处理器"""
    
    def __init__(self):
        self.logger = get_logger('speech_rule')
    
    def handle_text(self, text: str) -> List[Dict[str, str]]:
        """
        处理文本，分离旁白和对话
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的文本段列表
        """
        with performance_timer(self.logger, 'text_parsing', text_length=len(text)):
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

            self.logger.info(f"文本解析完成，生成 {len(result)} 个语音段")
            return result


class EnhancedAudioCache:
    """增强版音频缓存"""
    
    def __init__(self, size_limit: int = None, time_limit: int = None):
        self.size_limit = size_limit or config_manager.tts.cache_size_limit
        self.time_limit = time_limit or config_manager.tts.cache_time_limit
        self.cache = []
        self.current_size = 0
        self.logger = get_logger('audio_cache')
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def add(self, audio_segment: AudioSegment) -> None:
        """添加音频段到缓存"""
        current_time = time.time()
        audio_size = len(audio_segment.raw_data)
        
        # 移除过期的音频段
        self._cleanup_expired(current_time)
        
        # 移除音频段直到有足够的空间
        while self.current_size + audio_size > self.size_limit and self.cache:
            self._evict_oldest()
        
        # 添加新音频段
        self.cache.append((audio_segment, current_time))
        self.current_size += audio_size
        
        self.logger.debug(f"缓存添加音频段，大小: {audio_size} 字节")
    
    def combine(self) -> Optional[AudioSegment]:
        """组合缓存中的音频段"""
        self.stats['total_requests'] += 1
        
        if not self.cache:
            self.stats['misses'] += 1
            return None
        
        current_time = time.time()
        valid_segments = [
            seg for seg, ts in self.cache 
            if (current_time - ts) <= self.time_limit
        ]
        
        if not valid_segments:
            self.stats['misses'] += 1
            return None
        
        self.stats['hits'] += 1
        return sum(valid_segments)
    
    def _cleanup_expired(self, current_time: float) -> None:
        """清理过期的音频段"""
        original_count = len(self.cache)
        self.cache = [
            (seg, ts) for seg, ts in self.cache 
            if (current_time - ts) <= self.time_limit
        ]
        self.current_size = sum(len(seg.raw_data) for seg, _ in self.cache)
        
        evicted = original_count - len(self.cache)
        if evicted > 0:
            self.stats['evictions'] += evicted
            self.logger.debug(f"清理 {evicted} 个过期音频段")
    
    def _evict_oldest(self) -> None:
        """移除最旧的音频段"""
        if self.cache:
            oldest_segment, _ = self.cache.pop(0)
            self.current_size -= len(oldest_segment.raw_data)
            self.stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        hit_rate = (
            self.stats['hits'] / self.stats['total_requests'] 
            if self.stats['total_requests'] > 0 else 0
        )
        
        return {
            'cache_size': len(self.cache),
            'current_size_bytes': self.current_size,
            'size_limit_bytes': self.size_limit,
            'hit_rate': round(hit_rate, 3),
            'stats': self.stats.copy()
        }


class EnhancedTTSService:
    """增强版 TTS 服务"""
    
    def __init__(self):
        self.logger = get_logger('tts_service')
        self.error_handler = ErrorHandler(self.logger.logger)
        self.validator = RequestValidator()
        self.speech_rule = EnhancedSpeechRule()
        self.dictionary_service = DictionaryService()
        self.audio_cache = EnhancedAudioCache()
        
        # 配置线程池
        self.executor = ThreadPoolExecutor(
            max_workers=config_manager.system.max_workers,
            thread_name_prefix='tts_worker'
        )
    
    def process_request(self, request_args: Dict[str, Any]) -> Response:
        """
        处理 TTS 请求
        
        Args:
            request_args: 请求参数
            
        Returns:
            Flask Response 对象
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.set_request_id(request_id)
        
        start_time = time.time()
        
        try:
            # 记录请求开始
            self.logger.info(
                "TTS 请求开始处理",
                request_id=request_id,
                request_args=request_args
            )
            
            # 参数验证
            with performance_timer(self.logger, 'parameter_validation'):
                validated_params = self.validator.validate_tts_request(request_args)
            
            # 文本预处理（字典服务）
            with performance_timer(self.logger, 'text_preprocessing'):
                processed_text = self.dictionary_service.process_text(validated_params['text'])
                self.logger.info(
                    "文本预处理完成",
                    original_text=validated_params['text'][:100] + "..." if len(validated_params['text']) > 100 else validated_params['text'],
                    processed_text=processed_text[:100] + "..." if len(processed_text) > 100 else processed_text
                )
            
            # 文本分段处理
            with performance_timer(self.logger, 'text_segmentation'):
                text_segments = self.speech_rule.handle_text(processed_text)
            
            # 音频生成
            with performance_timer(self.logger, 'audio_generation'):
                audio_segments = self._generate_audio_segments(text_segments, validated_params)
            
            if not audio_segments:
                raise AudioGenerationError(
                    message="未能生成任何音频段",
                    details={'text_segments': len(text_segments)}
                )
            
            # 音频合成
            with performance_timer(self.logger, 'audio_combination'):
                combined_audio = sum(audio_segments)
                self.audio_cache.add(combined_audio)
            
            # 导出音频
            with performance_timer(self.logger, 'audio_export'):
                output_io = io.BytesIO()
                combined_audio.export(output_io, format="webm")
                output_io.seek(0)
            
            # 记录成功
            duration = time.time() - start_time
            self.logger.info(
                "TTS 请求处理成功",
                request_id=request_id,
                total_duration_ms=round(duration * 1000, 2),
                audio_segments_count=len(audio_segments),
                cache_stats=self.audio_cache.get_stats()
            )
            
            return Response(
                output_io,
                mimetype='audio/webm',
                headers={
                    'X-Audio-Duration': str(len(combined_audio)),
                    'X-Request-ID': request_id,
                    'X-Processing-Time': f"{duration:.3f}s"
                }
            )
            
        except Exception as e:
            # 错误处理
            duration = time.time() - start_time
            context = {
                'request_id': request_id,
                'processing_duration': duration,
                'request_args': request_args
            }
            
            self.logger.error(
                "TTS 请求处理失败",
                error=e,
                request_id=request_id,
                duration_ms=round(duration * 1000, 2)
            )
            
            return self.error_handler.handle_error(e, context)
    
    def _generate_audio_segments(self, text_segments: List[Dict[str, str]], 
                               params: Dict[str, Any]) -> List[AudioSegment]:
        """
        生成音频段
        
        Args:
            text_segments: 文本段列表
            params: 验证后的参数
            
        Returns:
            音频段列表
        """
        audio_segments = []
        futures = {}
        
        # 提交所有音频生成任务
        for segment in text_segments:
            voice_name = self._get_voice_for_segment(segment, params)
            future = self.executor.submit(
                self._fetch_audio_with_retry,
                segment,
                params['speed'],
                voice_name
            )
            futures[future] = segment
        
        # 收集结果
        for future in futures:
            segment = futures[future]
            try:
                audio_segment = future.result(timeout=30)  # 30秒超时
                if audio_segment:
                    audio_segments.append(audio_segment)
                    self.logger.debug(f"音频段生成成功: {segment['text'][:50]}...")
                else:
                    self.logger.warning(f"音频段生成失败: {segment['text'][:50]}...")
            except Exception as e:
                self.logger.error(
                    f"音频段生成异常: {segment['text'][:50]}...",
                    error=e
                )
        
        return audio_segments
    
    def _get_voice_for_segment(self, segment: Dict[str, str], 
                              params: Dict[str, Any]) -> str:
        """获取段落对应的语音"""
        if params['all_voice']:
            return params['all_voice']
        
        return (
            params['narr_voice'] if segment['tag'] == 'narration' 
            else params['dlg_voice']
        )
    
    def _fetch_audio_with_retry(self, segment: Dict[str, str], 
                               speed: float, voice_name: str) -> Optional[AudioSegment]:
        """
        使用重试机制获取音频
        
        Args:
            segment: 文本段
            speed: 语速
            voice_name: 语音名称
            
        Returns:
            音频段或None
        """
        def fetch_audio():
            return self._fetch_audio(segment, speed, voice_name)
        
        try:
            # 使用错误处理器的重试机制
            return self.error_handler.retry_with_backoff(fetch_audio)
        except Exception as e:
            # 尝试降级语音
            try:
                return self.error_handler.with_fallback_voice(
                    voice_name, 
                    self._fetch_audio,
                    segment, 
                    speed, 
                    voice=voice_name
                )
            except Exception as fallback_error:
                self.logger.error(
                    f"音频生成完全失败: {segment['text'][:50]}...",
                    error=fallback_error,
                    original_error=str(e)
                )
                return None
    
    def _fetch_audio(self, segment: Dict[str, str], speed: float, 
                    voice: str) -> AudioSegment:
        """
        使用 edge-tts 生成音频
        
        Args:
            segment: 文本段
            speed: 语速
            voice: 语音名称
            
        Returns:
            音频段
            
        Raises:
            ServiceUnavailableError: 服务不可用
            AudioGenerationError: 音频生成失败
        """
        text = segment['text']
        rate = f"{float(speed) * 100 - 100:+.0f}%"
        
        try:
            self.logger.debug(f"开始生成音频: {text[:50]}... (语音: {voice})")
            
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            audio_bytes = b''
            
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def get_audio():
                nonlocal audio_bytes
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
            
            loop.run_until_complete(get_audio())
            loop.close()
            
            if not audio_bytes:
                raise AudioGenerationError(
                    message="Edge-TTS 返回空音频数据",
                    details={'text': text, 'voice': voice, 'rate': rate}
                )
            
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            return audio_segment
            
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(
                    service_name="edge-tts",
                    message=f"Edge-TTS 服务连接失败: {str(e)}",
                    details={'text': text, 'voice': voice, 'error': str(e)}
                )
            else:
                raise AudioGenerationError(
                    message=f"音频生成失败: {str(e)}",
                    details={'text': text, 'voice': voice, 'error': str(e)}
                )


# 创建增强版 TTS 服务实例
enhanced_tts_service = EnhancedTTSService()