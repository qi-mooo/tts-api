#!/usr/bin/env python3
"""
安装脚本 - 获取并配置 edge-tts 语音列表
在部署时自动运行，确保语音列表是最新的
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import edge_tts
except ImportError:
    print("错误: edge-tts 未安装")
    print("请运行: pip install edge-tts")
    sys.exit(1)


async def install_voices():
    """安装和配置语音列表"""
    print("=== Edge-TTS 语音列表安装程序 ===")
    
    # 创建必要的目录
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    try:
        # 获取语音列表
        print("正在从 Microsoft 服务器获取语音列表...")
        voices = await edge_tts.list_voices()
        print(f"成功获取 {len(voices)} 个语音")
        
        # 筛选中文语音
        chinese_voices = [v for v in voices if v.get('Locale', '').startswith('zh-')]
        print(f"找到 {len(chinese_voices)} 个中文语音")
        
        # 保存语音列表
        voices_file = data_dir / 'voices.json'
        with open(voices_file, 'w', encoding='utf-8') as f:
            json.dump({
                'all_voices': voices,
                'chinese_voices': chinese_voices,
                'voice_count': len(voices),
                'chinese_count': len(chinese_voices),
                'install_time': asyncio.get_event_loop().time()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"语音列表已保存到: {voices_file}")
        
        # 创建快速访问的中文语音映射
        chinese_map = {}
        for voice in chinese_voices:
            short_name = voice['ShortName']
            chinese_map[short_name] = {
                'name': voice['FriendlyName'],
                'gender': voice['Gender'],
                'locale': voice['Locale']
            }
        
        map_file = data_dir / 'chinese_voices_map.json'
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(chinese_map, f, ensure_ascii=False, indent=2)
        
        print(f"中文语音映射已保存到: {map_file}")
        
        # 显示可用的中文语音
        print("\n=== 可用的中文语音 ===")
        locales = {}
        for voice in chinese_voices:
            locale = voice['Locale']
            if locale not in locales:
                locales[locale] = []
            locales[locale].append(voice)
        
        for locale in sorted(locales.keys()):
            print(f"\n{locale}:")
            for voice in locales[locale]:
                print(f"  - {voice['ShortName']} ({voice['Gender']})")
        
        print(f"\n✅ 语音列表安装完成!")
        print(f"   总语音数: {len(voices)}")
        print(f"   中文语音数: {len(chinese_voices)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        return False


def check_voices_file():
    """检查语音文件是否存在且有效"""
    voices_file = project_root / 'data' / 'voices.json'
    
    if not voices_file.exists():
        return False
    
    try:
        with open(voices_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据完整性
        if 'all_voices' not in data or 'chinese_voices' not in data:
            return False
        
        if len(data['all_voices']) == 0:
            return False
        
        print(f"✅ 找到现有语音文件: {len(data['all_voices'])} 个语音")
        return True
        
    except (json.JSONDecodeError, KeyError):
        return False


async def main():
    """主函数"""
    print("检查现有语音文件...")
    
    if check_voices_file():
        response = input("语音文件已存在，是否重新下载? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("使用现有语音文件")
            return
    
    success = await install_voices()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())