"""
优化音频缓存系统使用示例
展示如何使用音频缓存的各种功能
"""

import time
import json
from typing import Any

# 模拟 AudioSegment 用于演示
class MockAudioSegment:
    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data
    
    def __len__(self):
        return len(self.raw_data)
    
    def __add__(self, other):
        return MockAudioSegment(self.raw_data + other.raw_data)


def demonstrate_basic_usage():
    """演示基本的缓存使用"""
    print("=== 基本缓存使用演示 ===")
    
    # 添加当前目录到路径以便导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from audio_cache import OptimizedAudioCache
    
    # 创建缓存实例
    cache = OptimizedAudioCache(size_limit=1024*1024, time_limit=300)  # 1MB, 5分钟
    
    # 模拟音频数据
    audio1 = MockAudioSegment(b'x' * 1000)  # 1KB音频
    audio2 = MockAudioSegment(b'y' * 2000)  # 2KB音频
    
    # 存储音频到缓存
    cache.put("你好世界", "zh-CN-YunjianNeural", 1.0, audio1)
    cache.put("Hello World", "en-US-JennyNeural", 1.2, audio2)
    
    print(f"缓存条目数: {len(cache)}")
    
    # 从缓存获取音频
    retrieved1 = cache.get("你好世界", "zh-CN-YunjianNeural", 1.0)
    retrieved2 = cache.get("不存在的文本", "zh-CN-YunjianNeural", 1.0)
    
    print(f"获取音频1: {'成功' if retrieved1 else '失败'}")
    print(f"获取音频2: {'成功' if retrieved2 else '失败'}")
    
    # 显示统计信息
    stats = cache.get_stats()
    print(f"命中率: {stats['hit_rate']:.2%}")
    print(f"内存使用: {stats['memory_usage_percent']:.1f}%")


def demonstrate_statistics_monitoring():
    """演示统计和监控功能"""
    print("\n=== 统计和监控功能演示 ===")
    
    from audio_cache import OptimizedAudioCache
    
    cache = OptimizedAudioCache()
    
    # 执行一系列操作
    for i in range(10):
        audio = MockAudioSegment(b'x' * (100 * (i + 1)))
        cache.put(f"文本{i}", "zh-CN-YunjianNeural", 1.0, audio)
    
    # 模拟一些缓存命中和未命中
    for i in range(15):
        text = f"文本{i % 12}"  # 有些会命中，有些不会
        result = cache.get(text, "zh-CN-YunjianNeural", 1.0)
    
    # 获取详细统计信息
    stats = cache.get_stats()
    print("缓存统计信息:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 获取缓存条目信息
    entries_info = cache.get_cache_entries_info()
    print(f"\n缓存条目详情 (共{len(entries_info)}个):")
    for i, entry in enumerate(entries_info[:3]):  # 只显示前3个
        print(f"  条目{i+1}: {entry['size_kb']}KB, "
              f"访问{entry['access_count']}次, "
              f"年龄{entry['age_seconds']:.1f}秒")


def demonstrate_memory_management():
    """演示内存管理功能"""
    print("\n=== 内存管理功能演示 ===")
    
    from audio_cache import OptimizedAudioCache
    
    # 创建小容量缓存用于演示
    cache = OptimizedAudioCache(size_limit=5000, time_limit=60)
    
    print(f"缓存大小限制: {cache.size_limit} 字节")
    
    # 添加音频直到超过限制
    for i in range(10):
        audio = MockAudioSegment(b'x' * 1000)  # 1KB每个
        cache.put(f"大文本{i}", "zh-CN-YunjianNeural", 1.0, audio)
        
        stats = cache.get_stats()
        print(f"添加条目{i+1}: {stats['entry_count']}个条目, "
              f"{stats['total_size_bytes']}字节, "
              f"内存使用率{stats['memory_usage_percent']:.1f}%")
    
    # 执行缓存优化
    print("\n执行缓存优化...")
    optimization_result = cache.optimize()
    print(f"优化结果: 移除{optimization_result['entries_removed']}个条目, "
          f"释放{optimization_result['bytes_freed']}字节")


def demonstrate_lru_behavior():
    """演示LRU行为"""
    print("\n=== LRU行为演示 ===")
    
    from audio_cache import OptimizedAudioCache
    
    cache = OptimizedAudioCache(size_limit=3000, time_limit=60)
    
    # 添加3个条目
    for i in range(3):
        audio = MockAudioSegment(b'x' * 900)
        cache.put(f"文本{i}", "zh-CN-YunjianNeural", 1.0, audio)
    
    print("初始状态:")
    for i in range(3):
        result = cache.get(f"文本{i}", "zh-CN-YunjianNeural", 1.0)
        print(f"  文本{i}: {'存在' if result else '不存在'}")
    
    # 访问文本0，使其成为最近使用
    cache.get("文本0", "zh-CN-YunjianNeural", 1.0)
    
    # 添加新条目，应该淘汰文本1（最少使用）
    audio_new = MockAudioSegment(b'x' * 900)
    cache.put("新文本", "zh-CN-YunjianNeural", 1.0, audio_new)
    
    print("\n添加新条目后:")
    for text in ["文本0", "文本1", "文本2", "新文本"]:
        result = cache.get(text, "zh-CN-YunjianNeural", 1.0)
        print(f"  {text}: {'存在' if result else '不存在'}")


def demonstrate_expiration():
    """演示过期机制"""
    print("\n=== 过期机制演示 ===")
    
    from audio_cache import OptimizedAudioCache
    
    # 创建短过期时间的缓存
    cache = OptimizedAudioCache(size_limit=10000, time_limit=2)  # 2秒过期
    
    audio = MockAudioSegment(b'x' * 1000)
    cache.put("临时文本", "zh-CN-YunjianNeural", 1.0, audio)
    
    # 立即获取
    result1 = cache.get("临时文本", "zh-CN-YunjianNeural", 1.0)
    print(f"立即获取: {'成功' if result1 else '失败'}")
    
    # 等待过期
    print("等待3秒...")
    time.sleep(3)
    
    # 再次获取
    result2 = cache.get("临时文本", "zh-CN-YunjianNeural", 1.0)
    print(f"过期后获取: {'成功' if result2 else '失败'}")
    
    stats = cache.get_stats()
    print(f"淘汰次数: {stats['evictions']}")


def demonstrate_config_integration():
    """演示配置集成"""
    print("\n=== 配置集成演示 ===")
    
    from audio_cache import OptimizedAudioCache
    
    cache = OptimizedAudioCache()
    
    print(f"当前配置:")
    print(f"  大小限制: {cache.size_limit} 字节")
    print(f"  时间限制: {cache.time_limit} 秒")
    
    # 模拟配置变更
    print("\n模拟配置变更...")
    cache._on_config_change("tts.cache_size_limit", 2048000)
    cache._on_config_change("tts.cache_time_limit", 600)
    
    print(f"更新后配置:")
    print(f"  大小限制: {cache.size_limit} 字节")
    print(f"  时间限制: {cache.time_limit} 秒")


def main():
    """主函数 - 运行所有演示"""
    print("优化音频缓存系统功能演示")
    print("=" * 50)
    
    try:
        demonstrate_basic_usage()
        demonstrate_statistics_monitoring()
        demonstrate_memory_management()
        demonstrate_lru_behavior()
        demonstrate_expiration()
        demonstrate_config_integration()
        
        print("\n" + "=" * 50)
        print("所有演示完成！")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()