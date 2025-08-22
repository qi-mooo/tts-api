#!/usr/bin/env python3
"""
测试语音管理器功能
"""

import sys
from voice_manager import VoiceManager, get_default_narrator_voice, get_default_dialogue_voice


def test_voice_manager():
    """测试语音管理器的各种功能"""
    print("=== 语音管理器功能测试 ===\n")
    
    # 创建语音管理器实例
    vm = VoiceManager()
    
    # 1. 测试基本统计信息
    print("1. 基本统计信息:")
    stats = vm.get_voice_stats()
    print(f"   总语音数: {stats['total_voices']}")
    print(f"   中文语音数: {stats['chinese_voices']}")
    print(f"   中文地区数: {stats['chinese_locales']}")
    print(f"   性别分布: 男性 {stats['gender_distribution']['Male']}, 女性 {stats['gender_distribution']['Female']}")
    
    # 2. 测试默认语音
    print("\n2. 默认语音设置:")
    defaults = vm.get_default_voices()
    print(f"   默认旁白语音: {defaults['narrator']}")
    print(f"   默认对话语音: {defaults['dialogue']}")
    
    # 3. 测试便捷函数
    print("\n3. 便捷函数测试:")
    narrator = get_default_narrator_voice()
    dialogue = get_default_dialogue_voice()
    print(f"   便捷函数 - 旁白语音: {narrator}")
    print(f"   便捷函数 - 对话语音: {dialogue}")
    
    # 4. 测试语音验证
    print("\n4. 语音验证测试:")
    test_voices = [
        "zh-CN-YunjianNeural",  # 应该存在
        "zh-CN-XiaoyiNeural",  # 应该存在
        "zh-CN-NonExistentNeural",  # 不存在
        "en-US-JennyNeural"  # 英文语音，应该存在但不是中文
    ]
    
    for voice in test_voices:
        is_valid = vm.validate_voice(voice)
        voice_info = vm.get_voice_by_name(voice)
        print(f"   {voice}: {'✅ 有效' if is_valid else '❌ 无效'}")
        if voice_info:
            print(f"      -> {voice_info['FriendlyName']} ({voice_info['Gender']}, {voice_info['Locale']})")
    
    # 5. 测试按地区获取语音
    print("\n5. 按地区获取语音:")
    locales = vm.get_available_locales(chinese_only=True)
    for locale in locales[:3]:  # 只显示前3个
        voices = vm.get_voices_by_locale(locale)
        print(f"   {locale}: {len(voices)} 个语音")
        for voice in voices[:2]:  # 每个地区只显示前2个
            print(f"      - {voice['ShortName']} ({voice['Gender']})")
    
    # 6. 测试按性别获取语音
    print("\n6. 按性别获取语音:")
    male_voices = vm.get_voices_by_gender('Male', chinese_only=True)
    female_voices = vm.get_voices_by_gender('Female', chinese_only=True)
    print(f"   中文男性语音: {len(male_voices)} 个")
    print(f"   中文女性语音: {len(female_voices)} 个")
    
    # 7. 测试搜索功能
    print("\n7. 语音搜索测试:")
    search_queries = ["Yunjian", "Female", "zh-CN", "Taiwan"]
    for query in search_queries:
        results = vm.search_voices(query, chinese_only=True)
        print(f"   搜索 '{query}': 找到 {len(results)} 个结果")
        for result in results[:2]:  # 只显示前2个结果
            print(f"      - {result['ShortName']}")
    
    # 8. 测试获取语音详细信息
    print("\n8. 语音详细信息:")
    test_voice = "zh-CN-YunjianNeural"
    voice_info = vm.get_voice_by_name(test_voice)
    if voice_info:
        print(f"   语音名称: {voice_info['ShortName']}")
        print(f"   友好名称: {voice_info['FriendlyName']}")
        print(f"   性别: {voice_info['Gender']}")
        print(f"   地区: {voice_info['Locale']}")
        print(f"   状态: {voice_info.get('Status', 'Unknown')}")
    
    print("\n=== 测试完成 ===")
    return True


def test_integration_with_config():
    """测试与配置文件的集成"""
    print("\n=== 配置集成测试 ===")
    
    try:
        import json
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        tts_config = config.get('tts', {})
        
        print("配置文件中的语音设置:")
        print(f"   默认旁白语音: {tts_config.get('default_narrator_voice', '未设置')}")
        print(f"   默认对话语音: {tts_config.get('default_dialogue_voice', '未设置')}")
        print(f"   可用语音数量: {len(tts_config.get('available_voices', []))}")
        
        # 验证配置中的语音是否有效
        vm = VoiceManager()
        narrator_voice = tts_config.get('default_narrator_voice')
        dialogue_voice = tts_config.get('default_dialogue_voice')
        
        if narrator_voice:
            is_valid = vm.validate_voice(narrator_voice)
            print(f"   旁白语音验证: {'✅ 有效' if is_valid else '❌ 无效'}")
        
        if dialogue_voice:
            is_valid = vm.validate_voice(dialogue_voice)
            print(f"   对话语音验证: {'✅ 有效' if is_valid else '❌ 无效'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置集成测试失败: {e}")
        return False


def main():
    """主函数"""
    success = True
    
    try:
        # 运行基本功能测试
        success &= test_voice_manager()
        
        # 运行配置集成测试
        success &= test_integration_with_config()
        
        if success:
            print("\n🎉 所有测试通过！语音管理器工作正常。")
            return 0
        else:
            print("\n❌ 部分测试失败，请检查错误信息。")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())