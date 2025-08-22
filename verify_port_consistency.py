#!/usr/bin/env python3
"""
端口配置一致性验证脚本

检查项目中所有配置文件、文档和代码中的端口设置是否一致
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class PortCheck:
    """端口检查结果"""
    file_path: str
    line_number: int
    content: str
    port: str
    context: str
    is_correct: bool


class PortConsistencyChecker:
    """端口一致性检查器"""
    
    def __init__(self, target_port: str = "8080"):
        self.target_port = target_port
        self.results: List[PortCheck] = []
        
        # 需要检查的文件模式
        self.file_patterns = [
            "*.py",
            "*.md",
            "*.yml", 
            "*.yaml",
            "*.json",
            "*.conf",
            "Dockerfile*",
            "Makefile",
            "*.sh"
        ]
        
        # 排除的目录
        self.exclude_dirs = {
            ".git", "__pycache__", "venv", "node_modules", 
            ".pytest_cache", ".coverage", "logs", "audio_cache"
        }
        
        # 端口匹配模式
        self.port_patterns = [
            # 直接端口引用
            r':(\d{4,5})\b',
            # localhost 引用
            r'localhost:(\d{4,5})\b',
            # 127.0.0.1 引用
            r'127\.0\.0\.1:(\d{4,5})\b',
            # 0.0.0.0 引用
            r'0\.0\.0\.0:(\d{4,5})\b',
            # port = 配置
            r'port\s*[=:]\s*(\d{4,5})\b',
            # EXPOSE 指令
            r'EXPOSE\s+(\d{4,5})\b',
            # 端口映射
            r'(\d{4,5}):(\d{4,5})',
            # 环境变量端口
            r'PORT[^=]*=\s*(\d{4,5})\b',
        ]
    
    def check_all_files(self) -> Dict[str, Any]:
        """检查所有文件的端口配置"""
        print(f"🔍 开始检查端口配置一致性（目标端口: {self.target_port}）")
        print("=" * 60)
        
        # 遍历项目文件
        for root, dirs, files in os.walk("."):
            # 排除指定目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self._should_check_file(file_path):
                    self._check_file(file_path)
        
        # 生成报告
        return self._generate_report()
    
    def _should_check_file(self, file_path: str) -> bool:
        """判断是否需要检查该文件"""
        file_name = os.path.basename(file_path)
        
        # 检查文件扩展名
        for pattern in self.file_patterns:
            if Path(file_path).match(pattern):
                return True
        
        # 特殊文件名
        special_files = ["Dockerfile", "Makefile", "docker-compose.yml"]
        if file_name in special_files:
            return True
        
        return False
    
    def _check_file(self, file_path: str):
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                self._check_line(file_path, line_num, line)
                
        except Exception as e:
            print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    def _check_line(self, file_path: str, line_num: int, line: str):
        """检查单行内容"""
        for pattern in self.port_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            
            for match in matches:
                # 处理端口映射的情况
                if ':' in match.group() and len(match.groups()) == 2:
                    # 端口映射格式 host_port:container_port
                    host_port, container_port = match.groups()
                    self._add_port_check(file_path, line_num, line, host_port, "host_port")
                    self._add_port_check(file_path, line_num, line, container_port, "container_port")
                else:
                    # 单个端口
                    port = match.group(1) if match.groups() else match.group()
                    port = re.sub(r'[^\d]', '', port)  # 只保留数字
                    if port and port.isdigit():
                        self._add_port_check(file_path, line_num, line, port, "port")
    
    def _add_port_check(self, file_path: str, line_num: int, line: str, port: str, context: str):
        """添加端口检查结果"""
        # 跳过明显不是服务端口的情况
        if self._should_skip_port(port, line):
            return
        
        is_correct = port == self.target_port
        
        check = PortCheck(
            file_path=file_path,
            line_number=line_num,
            content=line.strip(),
            port=port,
            context=context,
            is_correct=is_correct
        )
        
        self.results.append(check)
    
    def _should_skip_port(self, port: str, line: str) -> bool:
        """判断是否应该跳过该端口检查"""
        port_num = int(port)
        
        # 跳过系统端口和常见服务端口
        skip_ports = {
            22, 25, 53, 80, 110, 143, 443, 993, 995,  # 系统服务端口
            3306, 5432, 6379, 27017,  # 数据库端口
            9200, 9300,  # Elasticsearch
            8000, 8001, 8002, 8003,  # 常见开发端口（但不包括 8080）
            8081,  # demo_restart.py 中故意使用的不同端口
        }
        
        if port_num in skip_ports:
            return True
        
        # 跳过端口范围验证中的边界值
        if port_num in {65535, 70000} and ('<=', '>=' in line or 'range' in line.lower() or 'test' in line.lower()):
            return True
        
        # 跳过注释行
        if line.strip().startswith('#') or line.strip().startswith('//'):
            return True
        
        # 跳过明显的示例或注释
        if any(keyword in line.lower() for keyword in ['example', '示例', 'sample']):
            # 但如果是我们的 demo 文件，不跳过
            if 'demo_' not in line.lower():
                return True
        
        # 跳过测试文件中的无效端口测试
        if 'test' in line.lower() and port_num > 65535:
            return True
        
        # 跳过避免冲突的端口配置
        if '避免冲突' in line or 'avoid conflict' in line.lower():
            return True
        
        return False
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成检查报告"""
        correct_count = sum(1 for r in self.results if r.is_correct)
        incorrect_count = len(self.results) - correct_count
        
        # 按文件分组
        by_file = {}
        for result in self.results:
            if result.file_path not in by_file:
                by_file[result.file_path] = []
            by_file[result.file_path].append(result)
        
        # 统计不正确的端口
        incorrect_ports = {}
        for result in self.results:
            if not result.is_correct:
                port = result.port
                if port not in incorrect_ports:
                    incorrect_ports[port] = []
                incorrect_ports[port].append(result)
        
        report = {
            'summary': {
                'target_port': self.target_port,
                'total_checks': len(self.results),
                'correct_count': correct_count,
                'incorrect_count': incorrect_count,
                'consistency_rate': f"{(correct_count / len(self.results) * 100):.1f}%" if self.results else "0%"
            },
            'by_file': by_file,
            'incorrect_ports': incorrect_ports,
            'files_with_issues': [f for f, checks in by_file.items() if any(not c.is_correct for c in checks)]
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """打印检查报告"""
        summary = report['summary']
        
        print(f"\n📊 端口配置一致性检查报告")
        print("=" * 60)
        print(f"目标端口: {summary['target_port']}")
        print(f"检查项目: {summary['total_checks']}")
        print(f"正确配置: {summary['correct_count']}")
        print(f"错误配置: {summary['incorrect_count']}")
        print(f"一致性率: {summary['consistency_rate']}")
        
        if summary['incorrect_count'] > 0:
            print(f"\n❌ 发现 {summary['incorrect_count']} 个端口配置问题:")
            print("-" * 40)
            
            for file_path in report['files_with_issues']:
                print(f"\n📄 {file_path}:")
                
                for check in report['by_file'][file_path]:
                    if not check.is_correct:
                        print(f"  第 {check.line_number} 行: 端口 {check.port} (应为 {self.target_port})")
                        print(f"    内容: {check.content[:80]}{'...' if len(check.content) > 80 else ''}")
            
            print(f"\n🔧 需要修正的端口统计:")
            for port, checks in report['incorrect_ports'].items():
                files = set(c.file_path for c in checks)
                print(f"  端口 {port}: {len(checks)} 处 (涉及 {len(files)} 个文件)")
        
        else:
            print(f"\n✅ 所有端口配置都正确！")
        
        print("\n" + "=" * 60)
    
    def fix_issues(self, report: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """修复端口配置问题"""
        if report['summary']['incorrect_count'] == 0:
            print("✅ 没有需要修复的端口配置问题")
            return {'fixed': 0, 'files': []}
        
        print(f"🔧 {'模拟' if dry_run else '开始'}修复端口配置问题...")
        
        fixed_files = []
        fixed_count = 0
        
        for file_path in report['files_with_issues']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                modified = False
                file_fixes = []
                
                for check in report['by_file'][file_path]:
                    if not check.is_correct:
                        line_idx = check.line_number - 1
                        old_line = lines[line_idx]
                        
                        # 替换端口
                        new_line = self._replace_port_in_line(old_line, check.port, self.target_port)
                        
                        if new_line != old_line:
                            lines[line_idx] = new_line
                            modified = True
                            fixed_count += 1
                            
                            file_fixes.append({
                                'line': check.line_number,
                                'old': old_line.strip(),
                                'new': new_line.strip(),
                                'port_changed': f"{check.port} → {self.target_port}"
                            })
                
                if modified:
                    if not dry_run:
                        # 备份原文件
                        backup_path = f"{file_path}.backup"
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            with open(file_path, 'r', encoding='utf-8') as orig:
                                f.write(orig.read())
                        
                        # 写入修改后的内容
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                    
                    fixed_files.append({
                        'file': file_path,
                        'fixes': file_fixes
                    })
                    
                    print(f"  {'[模拟] ' if dry_run else ''}修复 {file_path}: {len(file_fixes)} 处")
                    
            except Exception as e:
                print(f"⚠️  无法修复文件 {file_path}: {e}")
        
        result = {
            'fixed': fixed_count,
            'files': fixed_files
        }
        
        if dry_run:
            print(f"\n📋 模拟修复完成，共 {fixed_count} 处需要修复")
            print("使用 --fix 参数执行实际修复")
        else:
            print(f"\n✅ 修复完成，共修复 {fixed_count} 处端口配置")
            print("原文件已备份为 .backup 后缀")
        
        return result
    
    def _replace_port_in_line(self, line: str, old_port: str, new_port: str) -> str:
        """在行中替换端口"""
        # 精确替换，避免误替换
        patterns = [
            (rf'\b{old_port}\b', new_port),  # 独立的端口号
            (rf':{old_port}\b', f':{new_port}'),  # 冒号后的端口
            (rf'{old_port}:', f'{new_port}:'),  # 冒号前的端口（端口映射）
        ]
        
        result = line
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        
        return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='端口配置一致性检查工具')
    parser.add_argument('--port', default='8080', help='目标端口 (默认: 8080)')
    parser.add_argument('--fix', action='store_true', help='自动修复端口配置问题')
    parser.add_argument('--dry-run', action='store_true', help='模拟修复（不实际修改文件）')
    
    args = parser.parse_args()
    
    checker = PortConsistencyChecker(args.port)
    report = checker.check_all_files()
    checker.print_report(report)
    
    if args.fix or args.dry_run:
        fix_result = checker.fix_issues(report, dry_run=not args.fix)
        
        if args.fix and fix_result['fixed'] > 0:
            print("\n🔄 重新检查修复结果...")
            new_report = checker.check_all_files()
            checker.print_report(new_report)
    
    # 返回退出码
    return 0 if report['summary']['incorrect_count'] == 0 else 1


if __name__ == '__main__':
    exit(main())