
# 添加到你的 Flask 应用中的语音相关 API 端点

from voice_manager import get_voice_manager

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
        
        return jsonify({
            'success': True,
            'voices': simplified_voices,
            'count': len(simplified_voices)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/voices/stats', methods=['GET'])
def get_voice_stats():
    """获取语音统计信息"""
    try:
        vm = get_voice_manager()
        stats = vm.get_voice_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/voices/validate', methods=['POST'])
def validate_voice():
    """验证语音名称是否有效"""
    try:
        data = request.get_json()
        voice_name = data.get('voice_name')
        
        if not voice_name:
            return jsonify({
                'success': False,
                'error': '缺少 voice_name 参数'
            }), 400
        
        vm = get_voice_manager()
        is_valid = vm.validate_voice(voice_name)
        voice_info = vm.get_voice_by_name(voice_name) if is_valid else None
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'voice_info': voice_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
