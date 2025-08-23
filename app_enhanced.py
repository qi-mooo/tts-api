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
from user_settings.settings_controller import settings_controller
from voice_manager import get_voice_manager


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
    
    # 语音管理端点
    @app.route('/api/voices', methods=['GET'])
    def get_voices():
        """获取可用语音列表"""
        try:
            vm = get_voice_manager()
            
            # 获取查询参数
            chinese_only = request.args.get('chinese_only', 'true').lower() == 'true'
            locale = request.args.get('locale')
            gender = request.args.get('gender')
            
            # 获取语音列表
            if chinese_only:
                voices = vm.get_chinese_voices()
            else:
                voices = vm.get_all_voices()
            
            # 按地区筛选
            if locale:
                voices = [v for v in voices if v.get('Locale') == locale]
            
            # 按性别筛选
            if gender:
                voices = [v for v in voices if v.get('Gender') == gender]
            
            # 简化返回数据
            simplified_voices = [
                {
                    'name': voice['ShortName'],
                    'display_name': voice['FriendlyName'],
                    'gender': voice['Gender'],
                    'locale': voice['Locale']
                }
                for voice in voices
            ]
            
            logger.info(
                f"获取语音列表",
                chinese_only=chinese_only,
                locale=locale,
                gender=gender,
                result_count=len(simplified_voices)
            )
            
            return jsonify({
                'success': True,
                'voices': simplified_voices,
                'count': len(simplified_voices),
                'filters': {
                    'chinese_only': chinese_only,
                    'locale': locale,
                    'gender': gender
                }
            })
            
        except Exception as e:
            logger.error("获取语音列表失败", error=e)
            return jsonify({
                'success': False,
                'error': '获取语音列表失败',
                'details': str(e)
            }), 500

    @app.route('/api/voices/stats', methods=['GET'])
    def get_voice_stats():
        """获取语音统计信息"""
        try:
            vm = get_voice_manager()
            stats = vm.get_voice_stats()
            
            logger.info("获取语音统计信息", stats=stats)
            
            return jsonify({
                'success': True,
                'stats': stats,
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error("获取语音统计失败", error=e)
            return jsonify({
                'success': False,
                'error': '获取语音统计失败',
                'details': str(e)
            }), 500

    @app.route('/api/voices/validate', methods=['POST'])
    def validate_voice():
        """验证语音名称是否有效"""
        try:
            data = request.get_json()
            voice_name = data.get('voice_name') if data else None
            
            if not voice_name:
                return jsonify({
                    'success': False,
                    'error': '缺少 voice_name 参数'
                }), 400
            
            vm = get_voice_manager()
            is_valid = vm.validate_voice(voice_name)
            voice_info = vm.get_voice_by_name(voice_name) if is_valid else None
            
            # 简化语音信息
            simplified_info = None
            if voice_info:
                simplified_info = {
                    'name': voice_info['ShortName'],
                    'display_name': voice_info['FriendlyName'],
                    'gender': voice_info['Gender'],
                    'locale': voice_info['Locale'],
                    'status': voice_info.get('Status', 'Unknown')
                }
            
            logger.info(
                f"验证语音",
                voice_name=voice_name,
                is_valid=is_valid
            )
            
            return jsonify({
                'success': True,
                'voice_name': voice_name,
                'valid': is_valid,
                'voice_info': simplified_info
            })
            
        except Exception as e:
            logger.error("验证语音失败", error=e)
            return jsonify({
                'success': False,
                'error': '验证语音失败',
                'details': str(e)
            }), 500

    @app.route('/api/voices/locales', methods=['GET'])
    def get_voice_locales():
        """获取可用的语音地区列表"""
        try:
            vm = get_voice_manager()
            chinese_only = request.args.get('chinese_only', 'true').lower() == 'true'
            
            locales = vm.get_available_locales(chinese_only=chinese_only)
            
            # 为每个地区添加语音数量信息
            locale_info = []
            for locale in locales:
                voices = vm.get_voices_by_locale(locale)
                locale_info.append({
                    'locale': locale,
                    'voice_count': len(voices),
                    'male_count': len([v for v in voices if v.get('Gender') == 'Male']),
                    'female_count': len([v for v in voices if v.get('Gender') == 'Female'])
                })
            
            logger.info(
                f"获取语音地区列表",
                chinese_only=chinese_only,
                locale_count=len(locales)
            )
            
            return jsonify({
                'success': True,
                'locales': locale_info,
                'count': len(locales),
                'chinese_only': chinese_only
            })
            
        except Exception as e:
            logger.error("获取语音地区列表失败", error=e)
            return jsonify({
                'success': False,
                'error': '获取语音地区列表失败',
                'details': str(e)
            }), 500

    @app.route('/api/voices/search', methods=['GET'])
    def search_voices():
        """搜索语音"""
        try:
            query = request.args.get('q', '').strip()
            chinese_only = request.args.get('chinese_only', 'true').lower() == 'true'
            
            if not query:
                return jsonify({
                    'success': False,
                    'error': '缺少搜索查询参数 q'
                }), 400
            
            vm = get_voice_manager()
            results = vm.search_voices(query, chinese_only=chinese_only)
            
            # 简化搜索结果
            simplified_results = [
                {
                    'name': voice['ShortName'],
                    'display_name': voice['FriendlyName'],
                    'gender': voice['Gender'],
                    'locale': voice['Locale']
                }
                for voice in results
            ]
            
            logger.info(
                f"搜索语音",
                query=query,
                chinese_only=chinese_only,
                result_count=len(results)
            )
            
            return jsonify({
                'success': True,
                'query': query,
                'results': simplified_results,
                'count': len(simplified_results),
                'chinese_only': chinese_only
            })
            
        except Exception as e:
            logger.error("搜索语音失败", error=e)
            return jsonify({
                'success': False,
                'error': '搜索语音失败',
                'details': str(e)
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
        
        # 注册用户设置蓝图
        app.register_blueprint(settings_controller.blueprint)
        logger.info("用户设置API已集成")
    except ImportError as e:
        logger.warning(f"管理控制台模块不可用: {e}")
    
    # 根路径
    @app.route('/')
    def index():
        """根路径 - 服务首页"""
        from flask import render_template, request
        
        # 检查是否是 API 请求（通过 Accept 头判断）
        if request.headers.get('Accept', '').startswith('application/json'):
            # 获取实时统计信息
            try:
                voice_manager = get_voice_manager()
                voice_stats = voice_manager.get_voice_statistics()
                cache_stats = enhanced_tts_service.audio_cache.get_stats()
            except Exception as e:
                logger.warning(f"获取统计信息失败: {e}")
                voice_stats = {"total_voices": "322+", "chinese_voices": "14"}
                cache_stats = {}
            
            # 返回 JSON API 信息
            return jsonify({
                "service": "Enhanced TTS API",
                "version": "2.1.0",
                "status": "running",
                "endpoints": {
                    "tts": "/api",
                    "cached_audio": "/audio", 
                    "status": "/api/status",
                    "health": "/health",
                    "dictionary": "/api/dictionary/*",
                    "config": "/api/config",
                    "voices": "/api/voices",
                    "voice_stats": "/api/voices/stats",
                    "voice_validate": "/api/voices/validate",
                    "voice_locales": "/api/voices/locales",
                    "voice_search": "/api/voices/search",
                    "admin": "/admin",
                    "tts_interface": "/tts"
                },
                "features": [
                    "Text-to-Speech conversion with 322+ voices",
                    "Narration and dialogue separation",
                    "Intelligent speed adjustment",
                    "Audio caching and optimization",
                    "Dictionary management",
                    "Voice management and search",
                    "Health monitoring and admin interface",
                    "Mobile-friendly responsive design",
                    "RESTful API with comprehensive documentation"
                ],
                "voice_stats": {
                    "total_voices": voice_stats.get("total_voices", "322+"),
                    "chinese_voices": voice_stats.get("chinese_voices", "14"),
                    "supported_locales": voice_stats.get("supported_locales", "75+"),
                    "voice_categories": ["narration", "dialogue", "general"]
                },
                "cache_stats": cache_stats,
                "documentation": {
                    "api_docs": "Available via web interface",
                    "examples": {
                        "basic_tts": "/api?text=Hello&speed=1.0&all=en-US-AvaNeural",
                        "narration_dialogue": "/api?text=He said \"Hello\"&narr=en-US-BrianNeural&dlg=en-US-AvaNeural",
                        "voice_list": "/api/voices",
                        "health_check": "/health"
                    }
                },
                "system_info": {
                    "uptime": time.time(),
                    "request_id": getattr(request, 'id', 'unknown')
                }
            })
        else:
            # 增强的移动端检测 - 主要基于屏幕宽度
            user_agent = request.headers.get('User-Agent', '').lower()
            
            # 移动设备关键词
            mobile_keywords = [
                'mobile', 'android', 'iphone', 'ipod', 'blackberry', 
                'windows phone', 'opera mini', 'iemobile', 'webos'
            ]
            
            # 平板设备关键词
            tablet_keywords = ['ipad', 'tablet', 'kindle', 'playbook', 'silk']
            
            # 初始基于 User-Agent 的检测
            ua_mobile = any(keyword in user_agent for keyword in mobile_keywords)
            ua_tablet = any(keyword in user_agent for keyword in tablet_keywords)
            
            # 优先使用屏幕宽度信息（如果可用）
            viewport_width = request.headers.get('Viewport-Width')
            screen_width = None
            
            if viewport_width:
                try:
                    screen_width = int(viewport_width)
                except ValueError:
                    pass
            
            # 基于屏幕宽度的设备类型判断
            if screen_width:
                # 主要判断逻辑：基于屏幕宽度
                if screen_width <= 768:
                    is_mobile = True
                    is_tablet = False
                elif screen_width <= 1024:
                    # 在平板范围内，结合 User-Agent 判断
                    if ua_tablet or (ua_mobile and 'ipad' in user_agent):
                        is_mobile = False
                        is_tablet = True
                    else:
                        # 可能是小屏笔记本，按桌面处理
                        is_mobile = False
                        is_tablet = False
                else:
                    # 大屏幕设备
                    is_mobile = False
                    is_tablet = False
            else:
                # 没有屏幕宽度信息，回退到 User-Agent 检测
                is_mobile = ua_mobile and not ua_tablet
                is_tablet = ua_tablet
            
            # 设备信息
            device_info = {
                'is_mobile': is_mobile,
                'is_tablet': is_tablet,
                'device_type': 'mobile' if is_mobile else ('tablet' if is_tablet else 'desktop'),
                'user_agent': user_agent,
                'screen_width': screen_width,
                'detection_method': 'screen-width' if screen_width else 'user-agent',
                'supports_touch': any(touch in user_agent for touch in ['touch', 'mobile', 'android', 'iphone', 'ipad'])
            }
            
            # 返回 HTML 首页
            try:
                return render_template('home.html', 
                                     is_mobile=is_mobile, 
                                     is_tablet=is_tablet,
                                     device_info=device_info)
            except Exception as e:
                logger.warning(f"首页模板加载失败: {e}")
                # 降级到简单 HTML（移动端优化版）
                device_styles = ""
                if is_mobile:
                    device_styles = """
                        @media (max-width: 768px) {
                            body { padding: 10px; font-size: 16px; }
                            .header h1 { font-size: 1.8rem; }
                            .links { flex-direction: column; gap: 10px; }
                            .links a { display: block; text-align: center; min-height: 44px; padding: 12px 20px; }
                            .feature { padding: 12px; margin: 15px 0; }
                            .mobile-indicator { display: inline-block; }
                        }
                    """
                elif is_tablet:
                    device_styles = """
                        @media (min-width: 769px) and (max-width: 1024px) {
                            .container { max-width: 900px; }
                            .links { flex-wrap: wrap; }
                            .links a { min-width: 200px; }
                        }
                    """
                
                return f"""
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>TTS 文本转语音服务</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                        .header {{ text-align: center; margin-bottom: 40px; }}
                        .feature {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }}
                        .links {{ display: flex; gap: 15px; justify-content: center; margin: 30px 0; flex-wrap: wrap; }}
                        .links a {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                        .links a:hover {{ background: #0056b3; }}
                        .mobile-indicator {{ background: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-size: 0.8rem; display: none; }}
                        .tablet-indicator {{ background: #17a2b8; color: white; padding: 5px 10px; border-radius: 3px; font-size: 0.8rem; display: none; }}
                        {device_styles}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🎙️ TTS 文本转语音服务</h1>
                        <p>高质量的文本转语音 API 服务</p>
                        {'<span class="mobile-indicator">📱 移动端优化</span>' if is_mobile else ''}
                        {'<span class="tablet-indicator">📱 平板优化</span>' if is_tablet else ''}
                    </div>
                    
                    <div class="feature">
                        <h3>🚀 快速开始</h3>
                        <p>使用我们的 Web 界面快速体验文本转语音功能，支持旁白对话分离。</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🎵 多语音支持</h3>
                        <p>支持 322+ 种不同的语音，包括中文、英文、日文等多种语言。</p>
                    </div>
                    
                    <div class="feature">
                        <h3>⚡ 智能处理</h3>
                        <p>自动识别文本中的旁白和对话部分，使用不同声音进行合成。</p>
                    </div>
                    
                    <div class="links">
                        <a href="/tts">🎙️ 开始使用</a>
                        <a href="/admin">⚙️ 管理面板</a>
                        <a href="/api/status">📊 服务状态</a>
                        <a href="/health">💚 健康检查</a>
                    </div>
                    
                    <div style="text-align: center; margin-top: 40px; color: #666;">
                        <p>Enhanced TTS API v2.1.0 | {device_info['device_type']}端访问 | {'支持触摸' if device_info['supports_touch'] else '鼠标操作'}</p>
                    </div>
                </body>
                </html>
                """
    
    # TTS Web 界面
    @app.route('/tts')
    def tts_interface():
        """TTS Web 界面"""
        from flask import render_template, request
        
        # 检测设备类型
        user_agent = request.headers.get('User-Agent', '').lower()
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone', 'opera mini', 'iemobile']
        tablet_keywords = ['ipad', 'tablet', 'kindle', 'playbook', 'silk']
        
        is_mobile = any(keyword in user_agent for keyword in mobile_keywords)
        is_tablet = any(keyword in user_agent for keyword in tablet_keywords)
        
        device_info = {
            'is_mobile': is_mobile,
            'is_tablet': is_tablet,
            'device_type': 'mobile' if is_mobile else ('tablet' if is_tablet else 'desktop'),
            'user_agent': user_agent,
            'supports_touch': any(touch in user_agent for touch in ['touch', 'mobile', 'android', 'iphone', 'ipad'])
        }
        
        try:
            return render_template('index.html', 
                                 is_mobile=is_mobile, 
                                 is_tablet=is_tablet,
                                 device_info=device_info)
        except Exception as e:
            logger.error(f"TTS 界面模板加载失败: {e}")
            return jsonify({
                "error": "TTS 界面暂时不可用",
                "message": "请直接使用 API 端点 /api",
                "device_info": device_info
            }), 500

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