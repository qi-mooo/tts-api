"""
错误处理机制使用示例

演示如何在 TTS 系统中使用统一错误处理机制。
"""

import logging
from flask import Flask, request, jsonify
from error_handler import (
    ErrorHandler, ServiceUnavailableError, AudioGenerationError,
    ValidationError, error_handler_middleware
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)

# 创建错误处理器
error_handler = ErrorHandler(logger)

# 注册错误处理中间件
app.register_error_handler(Exception, error_handler_middleware(error_handler))


def simulate_tts_generation(text: str, voice: str) -> str:
    """模拟 TTS 音频生成"""
    if not text or not text.strip():
        raise ValidationError("text", "文本不能为空")
    
    if len(text) > 1000:
        raise ValidationError("text", "文本长度不能超过1000字符")
    
    if voice not in ["zh-CN-YunjianNeural", "zh-CN-XiaoyiNeural"]:
        raise ServiceUnavailableError("edge-tts", f"不支持的语音: {voice}")
    
    # 模拟随机失败
    import random
    if random.random() < 0.3:  # 30% 概率失败
        raise AudioGenerationError("音频生成服务暂时不可用")
    
    return f"generated_audio_for_{text[:10]}.mp3"


@app.route('/api/tts', methods=['POST'])
def tts_api():
    """TTS API 端点"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'zh-CN-YunjianNeural')
        
        # 使用重试机制生成音频
        audio_file = error_handler.retry_with_backoff(
            simulate_tts_generation, text, voice
        )
        
        return jsonify({
            'success': True,
            'audio_file': audio_file,
            'text': text,
            'voice': voice
        })
        
    except Exception as e:
        # 错误会被中间件自动处理
        raise e


@app.route('/api/tts_with_fallback', methods=['POST'])
def tts_api_with_fallback():
    """带降级策略的 TTS API 端点"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'zh-CN-YunjianNeural')
        
        # 使用降级语音策略
        audio_file = error_handler.with_fallback_voice(
            voice, simulate_tts_generation, text, voice=voice
        )
        
        return jsonify({
            'success': True,
            'audio_file': audio_file,
            'text': text,
            'voice': voice
        })
        
    except Exception as e:
        raise e


@app.route('/api/tts_with_circuit_breaker', methods=['POST'])
def tts_api_with_circuit_breaker():
    """带熔断器的 TTS API 端点"""
    
    @error_handler.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    def protected_tts_generation(text: str, voice: str) -> str:
        return simulate_tts_generation(text, voice)
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'zh-CN-YunjianNeural')
        
        audio_file = protected_tts_generation(text, voice)
        
        return jsonify({
            'success': True,
            'audio_file': audio_file,
            'text': text,
            'voice': voice
        })
        
    except Exception as e:
        raise e


@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'tts-api',
        'timestamp': time.time()
    })


if __name__ == '__main__':
    import time
    
    print("错误处理机制使用示例")
    print("=" * 50)
    
    # 测试基本异常功能
    print("\n1. 测试基本异常功能:")
    try:
        raise ServiceUnavailableError("edge-tts", "服务连接超时")
    except ServiceUnavailableError as e:
        print(f"捕获异常: {e}")
        print(f"错误详情: {e.to_dict()}")
    
    # 测试重试机制
    print("\n2. 测试重试机制:")
    def unreliable_function():
        import random
        if random.random() < 0.7:
            raise Exception("随机失败")
        return "成功"
    
    try:
        result = error_handler.retry_with_backoff(unreliable_function)
        print(f"重试成功: {result}")
    except Exception as e:
        print(f"重试失败: {e}")
    
    # 测试降级策略
    print("\n3. 测试降级策略:")
    def voice_function(text, voice):
        if voice == "zh-CN-YunjianNeural":
            raise Exception("主语音不可用")
        return f"使用 {voice} 生成: {text}"
    
    try:
        result = error_handler.with_fallback_voice(
            "zh-CN-YunjianNeural", voice_function, "测试文本", voice="zh-CN-YunjianNeural"
        )
        print(f"降级成功: {result}")
    except Exception as e:
        print(f"降级失败: {e}")
    
    print("\n启动 Flask 应用进行 API 测试...")
    print("可以使用以下命令测试 API:")
    print("curl -X POST http://localhost:8080/api/tts -H 'Content-Type: application/json' -d '{\"text\":\"你好世界\",\"voice\":\"zh-CN-YunjianNeural\"}'")
    
    app.run(debug=True, port=8080)