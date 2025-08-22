"""
增强版 Flask 应用 - 集成新的错误处理、日志系统和 TTS API

这是主应用文件，集成了所有增强功能模块。
"""

from flask import Flask, request, jsonify
import uuid
import time
from typing import Dict, Any

# 导入增强模块
from enhanced_tts_api import enhanced_tts_service
from error_handler.error_handler import ErrorHandler, error_handler_middleware
from logger.structured_logger import get_logger, performance_timer
from config.config_manager import config_manager
from health_check.health_monitor import HealthMonitor
from admin.admin_controller import AdminController


def create_enhanced_app() -> Flask:
    """创建增强版 Flask 应用"""
    
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = config_manager.admin.secret_key or 'dev-secret-key'
    app.config['DEBUG'] = config_manager.system.debug
    
    # 初始化日志
    logger = get_logger('enhanced_app', config_manager.logging.__dict__)
    
    # 初始化错误处理器
    error_handler = ErrorHandler(logger.logger)
    
    # 注册全局错误处理器
    app.register_error_handler(Exception, error_handler_middleware(error_handler))
    
    # 请求前处理
    @app.before_request
    def before_request():
        """请求前处理 - 设置请求ID和开始时间"""
        request.id = str(uuid.uuid4())[:8]
        request.start_time = time.time()
        logger.set_request_id(request.id)
        
        # 过滤掉不需要记录的请求
        skip_paths = ['/health', '/favicon.ico', '/static/']
        if any(request.path.startswith(skip) for skip in skip_paths):
            return
        
        # 记录请求开始（只记录重要信息）
        log_data = {
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
        
        # 只在有查询参数时记录
        if request.query_string:
            query = request.query_string.decode('utf-8')
            # 截断过长的查询字符串
            if len(query) > 200:
                query = query[:200] + '...'
            log_data['query_string'] = query
        
        # 只在有请求体时记录
        if request.content_length and request.content_length > 0:
            log_data['content_type'] = request.content_type
            log_data['content_length'] = request.content_length
        
        logger.info(
            f"→ {request.method} {request.path}",
            **log_data
        )
    
    # 请求后处理
    @app.after_request
    def after_request(response):
        """请求后处理 - 记录响应信息"""
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # 过滤掉不需要记录的请求
        skip_paths = ['/health', '/favicon.ico', '/static/']
        if not any(request.path.startswith(skip) for skip in skip_paths):
            # 构建响应日志
            status_emoji = "✓" if response.status_code < 400 else "✗"
            duration_ms = round(duration * 1000, 2)
            
            log_data = {
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'method': request.method,
                'path': request.path
            }
            
            # 添加响应大小信息
            if response.content_length:
                log_data['response_size_bytes'] = response.content_length
                if response.content_length > 1024:
                    size_kb = response.content_length / 1024
                    log_data['response_size_display'] = f"{size_kb:.1f}KB"
                else:
                    log_data['response_size_display'] = f"{response.content_length}B"
            
            # 根据状态码和耗时选择日志级别
            if response.status_code >= 500:
                logger.error(f"← {status_emoji} {response.status_code} {request.method} {request.path} ({duration_ms}ms)", **log_data)
            elif response.status_code >= 400:
                logger.warning(f"← {status_emoji} {response.status_code} {request.method} {request.path} ({duration_ms}ms)", **log_data)
            elif duration_ms > 1000:  # 慢请求
                logger.warning(f"← {status_emoji} {response.status_code} {request.method} {request.path} ({duration_ms}ms) [SLOW]", **log_data)
            else:
                logger.info(f"← {status_emoji} {response.status_code} {request.method} {request.path} ({duration_ms}ms)", **log_data)
        
        # 添加响应头
        response.headers['X-Request-ID'] = getattr(request, 'id', 'unknown')
        response.headers['X-Processing-Time'] = f"{duration:.3f}s"
        
        return response
    
    # 增强版 TTS API 端点
    @app.route('/api', methods=['GET'])
    def enhanced_api():
        """增强版 TTS API 端点"""
        try:
            with performance_timer(logger, 'api_request_processing'):
                return enhanced_tts_service.process_request(request.args.to_dict())
        except Exception as e:
            logger.error("API 请求处理异常", error=e)
            raise
    
    # 音频缓存端点
    @app.route('/audio', methods=['GET'])
    def get_cached_audio():
        """获取缓存的音频"""
        try:
            combined_audio = enhanced_tts_service.audio_cache.combine()
            if combined_audio is None:
                return jsonify({
                    "success": False,
                    "error": "没有可用的缓存音频",
                    "cache_stats": enhanced_tts_service.audio_cache.get_stats()
                }), 404
            
            import io
            output_io = io.BytesIO()
            combined_audio.export(output_io, format="webm")
            output_io.seek(0)
            
            from flask import Response
            return Response(
                output_io.getvalue(),
                mimetype='audio/webm',
                headers={
                    'X-Cache-Hit': 'true',
                    'X-Audio-Duration': str(len(combined_audio))
                }
            )
            
        except Exception as e:
            logger.error("获取缓存音频失败", error=e)
            return jsonify({
                "success": False,
                "error": "获取缓存音频失败",
                "details": str(e)
            }), 500
    
    # API 状态端点
    @app.route('/api/status', methods=['GET'])
    def api_status():
        """API 状态信息"""
        try:
            cache_stats = enhanced_tts_service.audio_cache.get_stats()
            
            status_info = {
                "success": True,
                "service": "Enhanced TTS API",
                "version": "2.0.0",
                "timestamp": time.time(),
                "cache_stats": cache_stats,
                "config": {
                    "max_workers": config_manager.system.max_workers,
                    "cache_size_limit": config_manager.tts.cache_size_limit,
                    "cache_time_limit": config_manager.tts.cache_time_limit,
                    "default_voices": {
                        "narration": config_manager.tts.narration_voice,
                        "dialogue": config_manager.tts.dialogue_voice
                    }
                }
            }
            
            return jsonify(status_info)
            
        except Exception as e:
            logger.error("获取 API 状态失败", error=e)
            return jsonify({
                "success": False,
                "error": "获取状态信息失败",
                "details": str(e)
            }), 500
    
    # 字典管理端点
    @app.route('/api/dictionary/rules', methods=['GET'])
    def get_dictionary_rules():
        """获取字典规则"""
        try:
            rules = enhanced_tts_service.dictionary_service.get_all_rules()
            return jsonify({
                "success": True,
                "rules": [rule.to_dict() for rule in rules],
                "total": len(rules)
            })
        except Exception as e:
            logger.error("获取字典规则失败", error=e)
            return jsonify({
                "success": False,
                "error": "获取字典规则失败",
                "details": str(e)
            }), 500
    
    @app.route('/api/dictionary/rules', methods=['POST'])
    def add_dictionary_rule():
        """添加字典规则"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "请求体不能为空"
                }), 400
            
            rule_id = enhanced_tts_service.dictionary_service.add_rule(
                pattern=data.get('pattern'),
                replacement=data.get('replacement'),
                rule_type=data.get('type'),
                rule_id=data.get('id')
            )
            
            logger.audit(
                action="add_dictionary_rule",
                user=request.remote_addr,
                rule_id=rule_id,
                rule_data=data
            )
            
            return jsonify({
                "success": True,
                "message": "规则添加成功",
                "rule_id": rule_id
            })
            
        except Exception as e:
            logger.error("添加字典规则失败", error=e)
            return jsonify({
                "success": False,
                "error": "添加字典规则失败",
                "details": str(e)
            }), 500
    
    @app.route('/api/dictionary/test', methods=['POST'])
    def test_dictionary():
        """测试字典处理"""
        try:
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({
                    "success": False,
                    "error": "请提供要测试的文本"
                }), 400
            
            original_text = data['text']
            processed_text = enhanced_tts_service.dictionary_service.process_text(original_text)
            
            return jsonify({
                "success": True,
                "original_text": original_text,
                "processed_text": processed_text,
                "changed": original_text != processed_text
            })
            
        except Exception as e:
            logger.error("测试字典处理失败", error=e)
            return jsonify({
                "success": False,
                "error": "测试字典处理失败",
                "details": str(e)
            }), 500
    
    # 配置管理端点
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """获取当前配置"""
        try:
            config_dict = config_manager.get_config_dict()
            # 隐藏敏感信息
            if 'admin' in config_dict:
                config_dict['admin'].pop('password_hash', None)
                config_dict['admin'].pop('secret_key', None)
            
            return jsonify({
                "success": True,
                "config": config_dict
            })
            
        except Exception as e:
            logger.error("获取配置失败", error=e)
            return jsonify({
                "success": False,
                "error": "获取配置失败",
                "details": str(e)
            }), 500
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        """更新配置"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "请求体不能为空"
                }), 400
            
            # 更新配置
            for key, value in data.items():
                if key not in ['admin']:  # 禁止通过此端点更新管理员配置
                    config_manager.set(key, value)
            
            # 保存配置
            config_manager.save()
            
            logger.audit(
                action="update_config",
                user=request.remote_addr,
                config_changes=data
            )
            
            return jsonify({
                "success": True,
                "message": "配置更新成功"
            })
            
        except Exception as e:
            logger.error("更新配置失败", error=e)
            return jsonify({
                "success": False,
                "error": "更新配置失败",
                "details": str(e)
            }), 500
    
    # 健康检查端点（集成现有的健康检查模块）
    try:
        health_monitor = HealthMonitor()
        
        @app.route('/health', methods=['GET'])
        def health_check():
            """健康检查端点"""
            return health_monitor.get_health_summary()
            
    except ImportError:
        logger.warning("健康检查模块不可用，使用简化版本")
        
        @app.route('/health', methods=['GET'])
        def simple_health_check():
            """简化版健康检查"""
            return jsonify({
                "status": "healthy",
                "timestamp": time.time(),
                "service": "Enhanced TTS API"
            })
    
    # 管理控制台端点（集成现有的管理模块）
    try:
        from admin.flask_integration import init_admin_app
        init_admin_app(app)
        logger.info("管理控制台已集成")
    except ImportError as e:
        logger.warning(f"管理控制台模块不可用: {e}")
    
    # 根路径
    @app.route('/')
    def index():
        """根路径 - API 信息"""
        return jsonify({
            "service": "Enhanced TTS API",
            "version": "2.0.0",
            "endpoints": {
                "tts": "/api",
                "cached_audio": "/audio",
                "status": "/api/status",
                "health": "/health",
                "dictionary": "/api/dictionary/*",
                "config": "/api/config",
                "admin": "/admin"
            },
            "documentation": "https://github.com/your-repo/tts-api"
        })
    
    logger.info("增强版 Flask 应用初始化完成")
    return app


# 创建应用实例
app = create_enhanced_app()

if __name__ == '__main__':
    logger = get_logger('main')
    logger.info(
        "启动增强版 TTS 服务",
        host=config_manager.system.host,
        port=config_manager.system.port,
        debug=config_manager.system.debug
    )
    
    app.run(
        host=config_manager.system.host,
        port=config_manager.system.port,
        debug=config_manager.system.debug
    )