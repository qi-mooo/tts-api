#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
声音数据预处理脚本
将原始声音数据转换为支持旁白/对话分类的格式
"""

import json
import os
import sys
from typing import Dict, List, Any

class VoiceDataProcessor:
    """声音数据预处理器"""
    
    def __init__(self):
        self.narration_keywords = [
            'Yunjian', 'Yunxi', 'Conrad', 'Henri', 'Brian', 'Guy', 'Davis', 'Tony',
            'Hamed', 'Shakir', 'Bassel', 'Taim', 'Fahed', 'Rami', 'Omar', 'Jamal',
            'Abdullah', 'Moaz', 'Laith', 'Hedi', 'Hamdan', 'Saleh', 'Babek',
            'Pradeep', 'Bashkar', 'Goran', 'Borislav', 'Thiha', 'Enric',
            'WanLung', 'Yunyang', 'Yunxia', 'YunJhe', 'Duarte', 'Dmitry',
            'Mattias', 'Niwat', 'Ahmet', 'Ostap', 'NamMinh'
        ]
        
        self.dialogue_keywords = [
            'Xiaoxiao', 'Xiaoyi', 'HiuGaai', 'HiuMaan', 'HsiaoChen', 'HsiaoYu',
            'Xiaobei', 'Xiaoni', 'Ava', 'Emma', 'Jenny', 'Aria', 'Jane', 'Sara',
            'Nancy', 'Ana', 'Ashley', 'Cora', 'Elizabeth', 'Michelle', 'Monica',
            'Fatima', 'Laila', 'Amina', 'Salma', 'Rana', 'Sana', 'Noura',
            'Layla', 'Iman', 'Mouna', 'Aysha', 'Amal', 'Zariyah', 'Amany',
            'Reem', 'Maryam', 'Banu', 'Nabanita', 'Tanishaa', 'Vesna',
            'Kalina', 'Nilar', 'Joana'
        ]

    def categorize_voice(self, voice_name: str) -> List[str]:
        """
        根据声音特征进行分类
        
        Args:
            voice_name: 声音名称
            
        Returns:
            分类列表，可能包含 'narration', 'dialogue'
        """
        categories = []
        
        # 检查是否包含旁白关键词
        if any(keyword in voice_name for keyword in self.narration_keywords):
            categories.append('narration')
            
        # 检查是否包含对话关键词
        if any(keyword in voice_name for keyword in self.dialogue_keywords):
            categories.append('dialogue')
            
        # 如果没有匹配到特定分类，则同时适用于旁白和对话
        if not categories:
            categories.extend(['narration', 'dialogue'])
            
        return categories

    def process_voice_data_from_json(self, voices_data: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
        """
        从 voices.json 数据处理声音分类
        
        Args:
            voices_data: 原始声音数据
            
        Returns:
            处理后的分类声音数据
        """
        processed_data = {}
        
        if 'all_voices' in voices_data:
            # 按语言分组
            language_groups = {}
            for voice in voices_data['all_voices']:
                locale = voice.get('Locale', '')
                short_name = voice.get('ShortName', '')
                
                if not locale or not short_name:
                    continue
                    
                # 提取语言代码（前两位）
                lang_code = locale.split('-')[0] if '-' in locale else locale
                
                if lang_code not in language_groups:
                    language_groups[lang_code] = []
                    
                language_groups[lang_code].append(short_name)
            
            # 为每种语言创建分类
            for lang_code, voice_list in language_groups.items():
                processed_data[lang_code] = {
                    'all': voice_list,
                    'narration': [],
                    'dialogue': []
                }
                
                # 对每个声音进行分类
                for voice in voice_list:
                    categories = self.categorize_voice(voice)
                    if 'narration' in categories:
                        processed_data[lang_code]['narration'].append(voice)
                    if 'dialogue' in categories:
                        processed_data[lang_code]['dialogue'].append(voice)
        
        return processed_data

    def process_voice_data_from_template(self, template_voices: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
        """
        从模板声音数据处理声音分类
        
        Args:
            template_voices: 模板中的声音数据
            
        Returns:
            处理后的分类声音数据
        """
        processed_data = {}
        
        for language, voice_list in template_voices.items():
            processed_data[language] = {
                'all': [voice for voice in voice_list if voice != "No"],
                'narration': [],
                'dialogue': []
            }
            
            # 对每个声音进行分类
            for voice in voice_list:
                if voice == "No":
                    continue
                    
                categories = self.categorize_voice(voice)
                if 'narration' in categories:
                    processed_data[language]['narration'].append(voice)
                if 'dialogue' in categories:
                    processed_data[language]['dialogue'].append(voice)
        
        return processed_data

def main():
    """主函数"""
    processor = VoiceDataProcessor()
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 处理 voices.json 文件
    voices_json_path = os.path.join(project_root, 'data', 'voices.json')
    if os.path.exists(voices_json_path):
        print("处理 voices.json 文件...")
        with open(voices_json_path, 'r', encoding='utf-8') as f:
            voices_data = json.load(f)
        
        processed_voices = processor.process_voice_data_from_json(voices_data)
        
        # 保存处理后的数据
        output_path = os.path.join(project_root, 'data', 'voices_categorized.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_voices, f, ensure_ascii=False, indent=2)
        
        print(f"已生成分类声音数据文件: {output_path}")
        
        # 输出统计信息
        total_languages = len(processed_voices)
        print(f"处理了 {total_languages} 种语言的声音数据")
        
        for lang, data in processed_voices.items():
            print(f"  {lang}: 总计 {len(data['all'])} 个声音, "
                  f"旁白 {len(data['narration'])} 个, "
                  f"对话 {len(data['dialogue'])} 个")
    else:
        print(f"未找到 voices.json 文件: {voices_json_path}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())