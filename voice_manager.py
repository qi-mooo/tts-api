"""
语音管理器 - 管理 edge-tts 语音列表和选择
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class VoiceManager:
    """语音管理器类"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.voices_file = self.data_dir / "voices.json"
        self.chinese_map_file = self.data_dir / "chinese_voices_map.json"
        
        self._voices_data = None
        self._chinese_map = None
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_voices_data(self) -> Dict[str, Any]:
        """加载语音数据"""
        if self._voices_data is None:
            if self.voices_file.exists():
                try:
                    with open(self.voices_file, 'r', encoding='utf-8') as f:
                        self._voices_data = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"加载语音数据失败: {e}")
                    self._voices_data = {'all_voices': [], 'chinese_voices': []}
            else:
                print("语音数据文件不存在，请运行 scripts/install_voices.py")
                self._voices_data = {'all_voices': [], 'chinese_voices': []}
        
        return self._voices_data
    
    def _load_chinese_map(self) -> Dict[str, Dict[str, str]]:
        """加载中文语音映射"""
        if self._chinese_map is None:
            if self.chinese_map_file.exists():
                try:
                    with open(self.chinese_map_file, 'r', encoding='utf-8') as f:
                        self._chinese_map = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"加载中文语音映射失败: {e}")
                    self._chinese_map = {}
            else:
                self._chinese_map = {}
        
        return self._chinese_map
    
    def get_all_voices(self) -> List[Dict[str, Any]]:
        """获取所有语音列表"""
        data = self._load_voices_data()
        return data.get('all_voices', [])
    
    def get_chinese_voices(self) -> List[Dict[str, Any]]:
        """获取中文语音列表"""
        data = self._load_voices_data()
        return data.get('chinese_voices', [])
    
    def get_voice_by_name(self, voice_name: str) -> Optional[Dict[str, Any]]:
        """根据语音名称获取语音信息"""
        all_voices = self.get_all_voices()
        for voice in all_voices:
            if voice.get('ShortName') == voice_name:
                return voice
        return None
    
    def get_chinese_voice_info(self, voice_name: str) -> Optional[Dict[str, str]]:
        """获取中文语音的简化信息"""
        chinese_map = self._load_chinese_map()
        return chinese_map.get(voice_name)
    
    def get_voices_by_locale(self, locale: str) -> List[Dict[str, Any]]:
        """根据地区获取语音列表"""
        all_voices = self.get_all_voices()
        return [voice for voice in all_voices if voice.get('Locale') == locale]
    
    def get_voices_by_gender(self, gender: str, chinese_only: bool = True) -> List[Dict[str, Any]]:
        """根据性别获取语音列表"""
        voices = self.get_chinese_voices() if chinese_only else self.get_all_voices()
        return [voice for voice in voices if voice.get('Gender') == gender]
    
    def get_available_locales(self, chinese_only: bool = True) -> List[str]:
        """获取可用的地区列表"""
        voices = self.get_chinese_voices() if chinese_only else self.get_all_voices()
        locales = set()
        for voice in voices:
            locale = voice.get('Locale')
            if locale:
                locales.add(locale)
        return sorted(list(locales))
    
    def get_default_voices(self) -> Dict[str, str]:
        """获取默认语音配置"""
        chinese_voices = self.get_chinese_voices()
        
        defaults = {
            'narrator': 'zh-CN-YunjianNeural',  # 旁白 - 男性
            'dialogue': 'zh-CN-XiaoyiNeural',   # 对话 - 女性
        }
        
        # 验证默认语音是否存在，如果不存在则选择第一个可用的
        available_names = [voice['ShortName'] for voice in chinese_voices]
        
        for key, voice_name in defaults.items():
            if voice_name not in available_names and available_names:
                # 选择第一个可用的语音作为备选
                defaults[key] = available_names[0]
                print(f"默认语音 {voice_name} 不可用，使用 {available_names[0]} 替代")
        
        return defaults
    
    def validate_voice(self, voice_name: str) -> bool:
        """验证语音名称是否有效"""
        return self.get_voice_by_name(voice_name) is not None
    
    def get_voice_stats(self) -> Dict[str, Any]:
        """获取语音统计信息"""
        all_voices = self.get_all_voices()
        chinese_voices = self.get_chinese_voices()
        
        stats = {
            'total_voices': len(all_voices),
            'chinese_voices': len(chinese_voices),
            'locales': len(self.get_available_locales(chinese_only=False)),
            'chinese_locales': len(self.get_available_locales(chinese_only=True)),
        }
        
        # 统计性别分布
        gender_stats = {'Male': 0, 'Female': 0, 'Unknown': 0}
        for voice in chinese_voices:
            gender = voice.get('Gender', 'Unknown')
            if gender in gender_stats:
                gender_stats[gender] += 1
            else:
                gender_stats['Unknown'] += 1
        
        stats['gender_distribution'] = gender_stats
        
        return stats
    
    def search_voices(self, query: str, chinese_only: bool = True) -> List[Dict[str, Any]]:
        """搜索语音"""
        voices = self.get_chinese_voices() if chinese_only else self.get_all_voices()
        query = query.lower()
        
        results = []
        for voice in voices:
            # 搜索语音名称、友好名称和地区
            searchable_text = ' '.join([
                voice.get('ShortName', ''),
                voice.get('FriendlyName', ''),
                voice.get('Locale', ''),
                voice.get('Gender', '')
            ]).lower()
            
            if query in searchable_text:
                results.append(voice)
        
        return results


# 全局语音管理器实例
voice_manager = VoiceManager()


def get_voice_manager() -> VoiceManager:
    """获取语音管理器实例"""
    return voice_manager


# 便捷函数
def get_default_narrator_voice() -> str:
    """获取默认旁白语音"""
    defaults = voice_manager.get_default_voices()
    return defaults.get('narrator', 'zh-CN-YunjianNeural')


def get_default_dialogue_voice() -> str:
    """获取默认对话语音"""
    defaults = voice_manager.get_default_voices()
    return defaults.get('dialogue', 'zh-CN-XiaoyiNeural')


def validate_voice_name(voice_name: str) -> bool:
    """验证语音名称"""
    return voice_manager.validate_voice(voice_name)


if __name__ == "__main__":
    # 测试代码
    vm = VoiceManager()
    
    print("=== 语音管理器测试 ===")
    stats = vm.get_voice_stats()
    print(f"总语音数: {stats['total_voices']}")
    print(f"中文语音数: {stats['chinese_voices']}")
    print(f"中文地区数: {stats['chinese_locales']}")
    
    print("\n=== 默认语音 ===")
    defaults = vm.get_default_voices()
    for key, voice in defaults.items():
        print(f"{key}: {voice}")
    
    print("\n=== 中文地区 ===")
    locales = vm.get_available_locales(chinese_only=True)
    for locale in locales:
        voices = vm.get_voices_by_locale(locale)
        print(f"{locale}: {len(voices)} 个语音")