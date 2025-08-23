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
        
        # 智能语速参数处理
        validated_speed_result = self._validate_speed_smart(args.get('speed', config_manager.tts.default_speed))
        validated['speed'] = validated_speed_result['speed']
        validated['speed_adjusted'] = validated_speed_result['adjusted']
        validated['original_speed'] = validated_speed_result['original']
        
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
    
    def _validate_speed_smart(self, speed_input: Any) -> Dict[str, Any]:
        """
        智能语速参数验证和调整
        
        Args:
            speed_input: 输入的语速值
            
        Returns:
            包含调整后语速信息的字典
        """
        result = {
            'speed': 1.0,
            'adjusted': False,
            'original': speed_input
        }
        
        try:
            # 尝试转换为浮点数
            speed = float(speed_input)
            result['original'] = speed
            
            # 智能调整语速范围
            if speed < 0.5:
                result['speed'] = 0.5
                result['adjusted'] = True
                self.logger.info(f"语速自动调整: {speed} -> 0.5 (低于最小值)")
            elif speed > 3.0:
                result['speed'] = 3.0
                result['adjusted'] = True
                self.logger.info(f"语速自动调整: {speed} -> 3.0 (超过最大值)")
            else:
                result['speed'] = speed
                
        except (ValueError, TypeError):
            # 无效输入，使用默认值
            result['speed'] = 1.0
            result['adjusted'] = True
            self.logger.warning(f"无效语速参数 '{speed_input}'，使用默认值 1.0")
            
        return result


class EnhancedVoiceSelector:
    """增强版语音选择器"""
    
    def __init__(self):
        self.logger = get_logger('voice_selector')
        
        # 语音缓存
        self._voice_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 缓存5分钟
        
        # 语言检测器
        try:
            from langdetect import detect
            self._detect_language = detect
        except ImportError:
            self.logger.warning("langdetect 未安装，将使用简单的语言检测")
            self._detect_language = self._simple_language_detect
        
        # 语音配置
        self.voice_config = {
            'zh': ['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural', 'zh-CN-YunjianNeural'],
            'en': ['en-US-AriaNeural', 'en-US-JennyNeural', 'en-US-GuyNeural'],
            'ja': ['ja-JP-NanamiNeural', 'ja-JP-KeitaNeural'],
            'ko': ['ko-KR-SunHiNeural', 'ko-KR-InJoonNeural'],
            'default': 'zh-CN-XiaoxiaoNeural'
        }
    
    def select_voice(self, requested_voice: Optional[str], text: str, language: str = 'auto') -> Optional[str]:
        """
        智能语音选择（增强版）
        
        Args:
            requested_voice: 用户请求的语音
            text: 要合成的文本
            language: 语言代码
            
        Returns:
            选择的语音名称，如果没有找到合适的语音则返回None
        """
        try:
            # 获取可用语音列表
            available_voices = self.get_available_voices()
            if not available_voices:
                self.logger.error("没有可用的语音")
                return None
            
            # 如果指定了语音，先验证是否可用
            if requested_voice:
                # 精确匹配
                if requested_voice in available_voices:
                    self.logger.info(f"使用指定语音: {requested_voice}")
                    return requested_voice
                
                # 模糊匹配（忽略大小写）
                for voice in available_voices:
                    if voice.lower() == requested_voice.lower():
                        self.logger.info(f"使用指定语音（模糊匹配）: {voice}")
                        return voice
                
                # 部分匹配
                for voice in available_voices:
                    if requested_voice.lower() in voice.lower() or voice.lower() in requested_voice.lower():
                        self.logger.info(f"使用指定语音（部分匹配）: {voice}")
                        return voice
                
                self.logger.warning(f"指定语音不可用: {requested_voice}，将自动选择")
            
            # 自动检测语言
            if language == 'auto':
                language = self.detect_language(text)
                self.logger.debug(f"检测到语言: {language}")
            
            # 根据语言选择合适的语音
            suitable_voices = self.get_voices_by_language(language)
            
            # 过滤出实际可用的语音
            available_suitable_voices = [v for v in suitable_voices if v in available_voices]
            
            if available_suitable_voices:
                # 从合适的语音中选择最佳的
                best_voice = self.select_best_voice(available_suitable_voices, text)
                if best_voice:
                    self.logger.info(f"选择最佳语音: {best_voice}")
                    return best_voice
                
                # 如果没有最佳语音，选择第一个可用的
                selected_voice = available_suitable_voices[0]
                self.logger.info(f"选择合适语音: {selected_voice}")
                return selected_voice
            
            # 如果没有找到对应语言的语音，使用默认语音
            default_voice = self.get_default_voice()
            if default_voice and default_voice in available_voices:
                self.logger.info(f"使用默认语音: {default_voice}")
                return default_voice
            
            # 最后的回退：使用第一个可用语音
            if available_voices:
                fallback_voice = available_voices[0]
                self.logger.info(f"使用备用语音: {fallback_voice}")
                return fallback_voice
            
            self.logger.error("没有找到任何可用的语音")
            return None
            
        except Exception as e:
            self.logger.error(f"语音选择失败: {e}")
            # 紧急回退
            try:
                fallback_voices = self._get_fallback_voices()
                if fallback_voices:
                    emergency_voice = fallback_voices[0]
                    self.logger.warning(f"使用紧急备用语音: {emergency_voice}")
                    return emergency_voice
            except Exception as fallback_error:
                self.logger.error(f"紧急回退也失败: {fallback_error}")
            return None
    
    def get_available_voices(self) -> List[str]:
        """
        获取所有可用的语音（带缓存）
        
        Returns:
            可用语音列表
        """
        try:
            import time
            current_time = time.time()
            
            # 检查缓存是否有效
            if (self._voice_cache is not None and 
                self._cache_timestamp is not None and 
                current_time - self._cache_timestamp < self._cache_ttl):
                self.logger.debug("使用缓存的语音列表")
                return self._voice_cache
            
            # 从TTS引擎获取实际可用的语音
            try:
                from tts.enhanced_tts_engine import EnhancedTTSEngine
            except ImportError:
                # 如果TTS模块不存在，使用备用列表
                self.logger.warning("TTS引擎模块不可用，使用备用语音列表")
                fallback_voices = self._get_fallback_voices()
                self._voice_cache = fallback_voices
                self._cache_timestamp = current_time - self._cache_ttl + 60
                return fallback_voices
            
            # 创建TTS引擎实例
            tts_engine = EnhancedTTSEngine()
            
            # 获取可用语音
            voices = tts_engine.get_available_voices()
            
            if voices:
                self.logger.info(f"获取到 {len(voices)} 个可用语音")
                # 更新缓存
                self._voice_cache = voices
                self._cache_timestamp = current_time
                return voices
            else:
                # 如果无法获取实际语音，返回备用列表
                self.logger.warning("无法获取实际语音列表，使用备用列表")
                fallback_voices = self._get_fallback_voices()
                # 缓存备用列表（较短的TTL）
                self._voice_cache = fallback_voices
                self._cache_timestamp = current_time - self._cache_ttl + 60  # 1分钟后重试
                return fallback_voices
                
        except Exception as e:
            self.logger.error(f"获取可用语音失败: {e}，使用备用列表")
            fallback_voices = self._get_fallback_voices()
            # 缓存备用列表（较短的TTL）
            if self._voice_cache is None:
                self._voice_cache = fallback_voices
                self._cache_timestamp = current_time - self._cache_ttl + 60  # 1分钟后重试
            return fallback_voices
    
    def detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 输入文本
            
        Returns:
            语言代码
        """
        try:
            # 使用langdetect库检测语言
            detected = self._detect_language(text)
            
            # 映射到支持的语言
            language_mapping = {
                'zh-cn': 'zh',
                'zh': 'zh',
                'en': 'en',
                'ja': 'ja',
                'ko': 'ko'
            }
            
            return language_mapping.get(detected, 'zh')  # 默认中文
            
        except Exception as e:
            self.logger.warning(f"语言检测失败: {e}，使用默认语言")
            return 'zh'
    
    def _simple_language_detect(self, text: str) -> str:
        """
        简单的语言检测（当langdetect不可用时）
        
        Args:
            text: 输入文本
            
        Returns:
            语言代码
        """
        # 统计中文字符
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        # 统计英文字符
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        # 统计日文字符
        japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
        # 统计韩文字符
        korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        
        total_chars = len(text)
        if total_chars == 0:
            return 'zh'
        
        # 计算比例
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        japanese_ratio = japanese_chars / total_chars
        korean_ratio = korean_chars / total_chars
        
        # 选择比例最高的语言
        ratios = {
            'zh': chinese_ratio,
            'en': english_ratio,
            'ja': japanese_ratio,
            'ko': korean_ratio
        }
        
        detected_lang = max(ratios, key=ratios.get)
        
        # 如果最高比例太低，默认为中文
        if ratios[detected_lang] < 0.1:
            return 'zh'
        
        return detected_lang
    
    def get_voices_by_language(self, language: str) -> List[str]:
        """
        根据语言获取合适的语音
        
        Args:
            language: 语言代码
            
        Returns:
            语音列表
        """
        return self.voice_config.get(language, self.voice_config.get('zh', []))
    
    def select_best_voice(self, voices: List[str], text: str) -> Optional[str]:
        """
        从候选语音中选择最佳语音
        
        Args:
            voices: 候选语音列表
            text: 文本内容
            
        Returns:
            最佳语音名称
        """
        if not voices:
            return None
        
        # 简单策略：返回第一个语音
        # 可以根据需要实现更复杂的选择逻辑
        return voices[0]
    
    def get_default_voice(self) -> str:
        """获取默认语音"""
        return self.voice_config['default']
    
    def _get_fallback_voices(self) -> List[str]:
        """
        获取备用语音列表
        
        Returns:
            备用语音列表
        """
        return [
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-YunxiNeural", 
            "zh-CN-YunjianNeural",
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunyangNeural",
            "en-US-AriaNeural",
            "en-US-JennyNeural",
            "en-US-GuyNeural"
        ]
    
    def refresh_voice_cache(self) -> bool:
        """
        刷新语音缓存
        
        Returns:
            是否成功刷新
        """
        try:
            self._voice_cache = None
            self._cache_timestamp = None
            
            # 重新获取语音列表
            voices = self.get_available_voices()
            
            if voices:
                self.logger.info(f"语音缓存刷新成功，获取到 {len(voices)} 个语音")
                return True
            else:
                self.logger.warning("语音缓存刷新失败")
                return False
                
        except Exception as e:
            self.logger.error(f"刷新语音缓存失败: {e}")
            return False
    
    def get_voice_cache_info(self) -> Dict[str, Any]:
        """
        获取语音缓存信息
        
        Returns:
            缓存信息字典
        """
        import time
        current_time = time.time()
        
        cache_info = {
            'cached_voices_count': len(self._voice_cache) if self._voice_cache else 0,
            'cache_timestamp': self._cache_timestamp,
            'cache_age_seconds': current_time - self._cache_timestamp if self._cache_timestamp else None,
            'cache_ttl_seconds': self._cache_ttl,
            'is_cache_valid': (
                self._voice_cache is not None and 
                self._cache_timestamp is not None and 
                current_time - self._cache_timestamp < self._cache_ttl
            )
        }
        
        return cache_info


class EnhancedSpeechRule:
    """增强版语音规则处理器"""
    
    def __init__(self):
        self.logger = get_logger('speech_rule')
        self.voice_selector = EnhancedVoiceSelector()
    
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
            
            # 准备响应头
            response_headers = {
                'X-Audio-Duration': str(len(combined_audio)),
                'X-Request-ID': request_id,
                'X-Processing-Time': f"{duration:.3f}s",
                'X-Speed-Used': str(validated_params['speed'])
            }
            
            # 如果语速被调整，添加相关信息
            if validated_params.get('speed_adjusted', False):
                response_headers['X-Speed-Adjusted'] = 'true'
                response_headers['X-Speed-Original'] = str(validated_params.get('original_speed', 'unknown'))
                
                self.logger.info(
                    "语速参数已自动调整",
                    request_id=request_id,
                    original_speed=validated_params.get('original_speed'),
                    adjusted_speed=validated_params['speed']
                )
            
            return Response(
                output_io,
                mimetype='audio/webm',
                headers=response_headers
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
        """获取段落对应的语音（增强版）"""
        # 如果指定了统一语音，直接使用
        if params.get('all_voice'):
            selected_voice = self.speech_rule.voice_selector.select_voice(
                requested_voice=params['all_voice'],
                text=segment['text'],
                language=params.get('language', 'auto')
            )
            return selected_voice or params['all_voice']
        
        # 根据段落类型选择语音
        requested_voice = (
            params.get('narr_voice') if segment['tag'] == 'narration' 
            else params.get('dlg_voice')
        )
        
        # 使用智能语音选择
        if requested_voice:
            selected_voice = self.speech_rule.voice_selector.select_voice(
                requested_voice=requested_voice,
                text=segment['text'],
                language=params.get('language', 'auto')
            )
            return selected_voice or requested_voice
        
        # 如果没有指定语音，自动选择
        selected_voice = self.speech_rule.voice_selector.select_voice(
            requested_voice=None,
            text=segment['text'],
            language=params.get('language', 'auto')
        )
        
        return selected_voice or self.speech_rule.voice_selector.get_default_voice()
    
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