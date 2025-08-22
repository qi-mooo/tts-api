#!/usr/bin/env python3
"""
集成语音管理器到现有的 TTS 系统
更新配置文件和相关模块
"""

import json
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from voice_manager import VoiceManager


def update_config_with_voices():
    """更新配置文件，添加语音选项"""
    config_file = project_root / 'config.json'
    
    if not config_file.exists():
        print("配置文件不存在，跳过更新")
        return
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"读取配置文件失败: {e}")
        return
    
    # 获取语音管理器
    vm = VoiceManager()
    defaults = vm.get_default_voices()
    chinese_voices = vm.get_chinese_voices()
    
    # 更新配置中的语音设置
    if 'tts' not in config:
        config['tts'] = {}
    
    # 设置默认语音
    config['tts']['default_narrator_voice'] = defaults.get('narrator', 'zh-CN-YunjianNeural')
    config['tts']['default_dialogue_voice'] = defaults.get('dialogue', 'zh-CN-XiaoyiNeural')
    
    # 添加可用语音列表
    config['tts']['available_voices'] = [
        {
            'name': voice['ShortName'],
            'display_name': voice['FriendlyName'],
            'gender': voice['Gender'],
            'locale': voice['Locale']
        }
        for voice in chinese_voices
    ]
    
    # 添加语音统计信息
    stats = vm.get_voice_stats()
    config['tts']['voice_stats'] = stats
    
    # 保存更新后的配置
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置文件已更新: {config_file}")
        print(f"   - 默认旁白语音: {config['tts']['default_narrator_voice']}")
        print(f"   - 默认对话语音: {config['tts']['default_dialogue_voice']}")
        print(f"   - 可用中文语音: {len(config['tts']['available_voices'])} 个")
    except IOError as e:
        print(f"❌ 保存配置文件失败: {e}")


def create_voice_api_endpoint():
    """创建语音 API 端点的示例代码"""
    api_code = '''
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
'''
    
    api_file = project_root / 'voice_api_endpoints.py'
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(api_code)
    
    print(f"✅ 语音 API 端点示例已创建: {api_file}")


def create_makefile_targets():
    """创建 Makefile 目标用于语音管理"""
    makefile_content = '''
# 语音管理相关的 Makefile 目标

.PHONY: install-voices update-voices test-voices

install-voices:
	@echo "安装语音列表..."
	./venv/bin/python3 scripts/install_voices.py

update-voices:
	@echo "更新语音列表..."
	./venv/bin/python3 scripts/update_voices.py

test-voices:
	@echo "测试语音管理器..."
	./venv/bin/python3 voice_manager.py

integrate-voices:
	@echo "集成语音管理器..."
	./venv/bin/python3 scripts/integrate_voice_manager.py

voices-stats:
	@echo "显示语音统计..."
	./venv/bin/python3 -c "from voice_manager import voice_manager; import json; print(json.dumps(voice_manager.get_voice_stats(), indent=2, ensure_ascii=False))"
'''
    
    makefile_targets_file = project_root / 'Makefile.voices'
    with open(makefile_targets_file, 'w', encoding='utf-8') as f:
        f.write(makefile_content)
    
    print(f"✅ 语音管理 Makefile 目标已创建: {makefile_targets_file}")
    print("   可以使用以下命令:")
    print("   - make -f Makefile.voices install-voices")
    print("   - make -f Makefile.voices update-voices")
    print("   - make -f Makefile.voices test-voices")


def main():
    """主函数"""
    print("=== 语音管理器集成脚本 ===")
    
    # 检查语音数据是否存在
    vm = VoiceManager()
    stats = vm.get_voice_stats()
    
    if stats['chinese_voices'] == 0:
        print("❌ 未找到语音数据，请先运行: python3 scripts/install_voices.py")
        return
    
    print(f"✅ 找到 {stats['chinese_voices']} 个中文语音")
    
    # 更新配置文件
    update_config_with_voices()
    
    # 创建 API 端点示例
    create_voice_api_endpoint()
    
    # 创建 Makefile 目标
    create_makefile_targets()
    
    print("\n=== 集成完成 ===")
    print("语音管理器已成功集成到项目中！")
    print("\n下一步:")
    print("1. 检查更新后的 config.json 文件")
    print("2. 将 voice_api_endpoints.py 中的代码添加到你的 Flask 应用")
    print("3. 在你的 TTS 服务中使用 voice_manager 模块")
    print("4. 运行测试确保一切正常工作")


if __name__ == "__main__":
    main()