#!/usr/bin/env python3
"""
获取 edge-tts 语音列表并存储到 JSON 文件
用于程序和安装脚本使用
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any

import edge_tts


async def get_voices_list() -> List[Dict[str, Any]]:
    """获取所有可用的语音列表"""
    try:
        voices = await edge_tts.list_voices()
        return voices
    except Exception as e:
        print(f"获取语音列表失败: {e}")
        return []


def filter_chinese_voices(voices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """筛选中文语音"""
    chinese_voices = []
    for voice in voices:
        locale = voice.get('Locale', '')
        if locale.startswith('zh-'):
            chinese_voices.append(voice)
    return chinese_voices


def organize_voices_by_locale(voices: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按地区组织语音列表"""
    organized = {}
    for voice in voices:
        locale = voice.get('Locale', 'unknown')
        if locale not in organized:
            organized[locale] = []
        organized[locale].append(voice)
    return organized


def create_voice_summary(voices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """创建语音列表摘要"""
    summary = {
        'total_voices': len(voices),
        'locales': {},
        'genders': {'Male': 0, 'Female': 0, 'Unknown': 0},
        'last_updated': datetime.now().isoformat()
    }
    
    for voice in voices:
        locale = voice.get('Locale', 'unknown')
        gender = voice.get('Gender', 'Unknown')
        
        if locale not in summary['locales']:
            summary['locales'][locale] = 0
        summary['locales'][locale] += 1
        
        if gender in summary['genders']:
            summary['genders'][gender] += 1
        else:
            summary['genders']['Unknown'] += 1
    
    return summary


async def main():
    """主函数"""
    print("正在获取 edge-tts 语音列表...")
    
    # 获取所有语音
    all_voices = await get_voices_list()
    if not all_voices:
        print("无法获取语音列表")
        return
    
    print(f"获取到 {len(all_voices)} 个语音")
    
    # 创建输出目录
    os.makedirs('data', exist_ok=True)
    
    # 保存完整语音列表
    with open('data/voices_all.json', 'w', encoding='utf-8') as f:
        json.dump(all_voices, f, ensure_ascii=False, indent=2)
    print("完整语音列表已保存到 data/voices_all.json")
    
    # 筛选中文语音
    chinese_voices = filter_chinese_voices(all_voices)
    print(f"找到 {len(chinese_voices)} 个中文语音")
    
    # 保存中文语音列表
    with open('data/voices_chinese.json', 'w', encoding='utf-8') as f:
        json.dump(chinese_voices, f, ensure_ascii=False, indent=2)
    print("中文语音列表已保存到 data/voices_chinese.json")
    
    # 按地区组织语音
    organized_voices = organize_voices_by_locale(all_voices)
    with open('data/voices_by_locale.json', 'w', encoding='utf-8') as f:
        json.dump(organized_voices, f, ensure_ascii=False, indent=2)
    print("按地区组织的语音列表已保存到 data/voices_by_locale.json")
    
    # 创建摘要
    summary = create_voice_summary(all_voices)
    with open('data/voices_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("语音列表摘要已保存到 data/voices_summary.json")
    
    # 创建简化的语音选择列表（用于前端）
    simplified_voices = []
    for voice in chinese_voices:
        simplified_voices.append({
            'name': voice['ShortName'],
            'display_name': voice['FriendlyName'],
            'gender': voice['Gender'],
            'locale': voice['Locale'],
            'language': voice['Locale'].split('-')[0]
        })
    
    with open('data/voices_simplified.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_voices, f, ensure_ascii=False, indent=2)
    print("简化语音列表已保存到 data/voices_simplified.json")
    
    # 打印统计信息
    print("\n=== 语音统计 ===")
    print(f"总语音数: {summary['total_voices']}")
    print(f"中文语音数: {len(chinese_voices)}")
    print(f"男性语音: {summary['genders']['Male']}")
    print(f"女性语音: {summary['genders']['Female']}")
    print(f"支持的地区数: {len(summary['locales'])}")
    
    print("\n=== 中文地区分布 ===")
    chinese_locales = {k: v for k, v in summary['locales'].items() if k.startswith('zh-')}
    for locale, count in sorted(chinese_locales.items()):
        print(f"{locale}: {count} 个语音")


if __name__ == "__main__":
    asyncio.run(main())