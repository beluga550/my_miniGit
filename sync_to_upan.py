#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹同步到U盘工具
支持增量同步、双向同步、删除多余文件等功能
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import time


class FolderSyncer:
    """文件夹同步器"""
    
    def __init__(self, source, target, delete_extra=False, dry_run=False, verbose=True):
        self.source = Path(source).resolve()
        self.target = Path(target).resolve()
        self.delete_extra = delete_extra
        self.dry_run = dry_run
        self.verbose = verbose
        
        self.stats = {
            'copied': 0,
            'updated': 0,
            'deleted': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def log(self, message):
        """输出日志"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def copy_file(self, src, dst):
        """复制文件"""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if self.dry_run:
                self.log(f"[模拟] 复制: {src} -> {dst}")
                return True
            
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            self.log(f"[错误] 复制失败 {src}: {e}")
            self.stats['errors'] += 1
            return False
    
    def compare_files(self, src, dst):
        """比较两个文件是否相同"""
        if not dst.exists():
            return False
        
        if src.stat().st_size != dst.stat().st_size:
            return False
        
        if src.stat().st_mtime > dst.stat().st_mtime:
            return False
        
        return True
    
    def sync_dir(self, src_dir, dst_dir):
        """同步目录"""
        if not src_dir.exists():
            self.log(f"[警告] 源目录不存在: {src_dir}")
            return
        
        if self.dry_run:
            self.log(f"[模拟] 创建目录: {dst_dir}")
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
        
        src_items = list(src_dir.iterdir())
        
        for item in src_items:
            rel_path = item.relative_to(src_dir)
            dst_item = dst_dir / rel_path
            
            if item.is_file():
                if not dst_item.exists() or not self.compare_files(item, dst_item):
                    action = "更新" if dst_item.exists() else "复制"
                    self.log(f"[{action}] {rel_path}")
                    if self.copy_file(item, dst_item):
                        if dst_item.exists():
                            self.stats['updated'] += 1
                        else:
                            self.stats['copied'] += 1
                else:
                    self.stats['skipped'] += 1
                    if self.verbose:
                        self.log(f"[跳过] {rel_path} (已存在且相同)")
            
            elif item.is_dir():
                self.sync_dir(item, dst_item)
        
        if self.delete_extra:
            self.delete_extra_files(src_dir, dst_dir)
    
    def delete_extra_files(self, src_dir, dst_dir):
        """删除目标目录中多余的文件"""
        if not dst_dir.exists():
            return
        
        for item in dst_dir.iterdir():
            rel_path = item.relative_to(dst_dir)
            src_item = src_dir / rel_path
            
            if not src_item.exists():
                if self.dry_run:
                    self.log(f"[模拟] 删除: {rel_path}")
                else:
                    try:
                        if item.is_file():
                            item.unlink()
                        else:
                            shutil.rmtree(item)
                        self.log(f"[删除] {rel_path}")
                        self.stats['deleted'] += 1
                    except Exception as e:
                        self.log(f"[错误] 删除失败 {rel_path}: {e}")
                        self.stats['errors'] += 1
            elif item.is_dir():
                self.delete_extra_files(src_item, item)
    
    def sync(self):
        """执行同步"""
        self.log("=" * 60)
        self.log("开始同步...")
        self.log(f"源目录: {self.source}")
        self.log(f"目标目录: {self.target}")
        self.log(f"删除多余文件: {'是' if self.delete_extra else '否'}")
        self.log(f"模拟运行: {'是' if self.dry_run else '否'}")
        self.log("=" * 60)
        
        start_time = time.time()
        
        self.sync_dir(self.source, self.target)
        
        elapsed_time = time.time() - start_time
        
        self.log("=" * 60)
        self.log("同步完成!")
        self.log(f"统计信息:")
        self.log(f"  新增文件: {self.stats['copied']}")
        self.log(f"  更新文件: {self.stats['updated']}")
        self.log(f"  删除文件: {self.stats['deleted']}")
        self.log(f"  跳过文件: {self.stats['skipped']}")
        self.log(f"  错误数量: {self.stats['errors']}")
        self.log(f"耗时: {elapsed_time:.2f} 秒")
        self.log("=" * 60)


def parse_config(config_file):
    """解析配置文件"""
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
    except Exception as e:
        print(f"[错误] 读取配置文件失败: {e}")
    return config


def main():
    parser = argparse.ArgumentParser(
        description='文件夹同步到U盘工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 同步文件夹到U盘（仅复制新文件和更新的文件）
  python sync_to_upan.py "C:\\MyFolder" "E:\\UpanBackup"
  
  # 同步并删除目标中多余的文件
  python sync_to_upan.py "C:\\MyFolder" "E:\\UpanBackup" --delete
  
  # 模拟运行，不实际复制文件
  python sync_to_upan.py "C:\\MyFolder" "E:\\UpanBackup" --dry-run
  
  # 创建配置文件后使用配置
  python sync_to_upan.py --config config.txt
        """
    )
    
    parser.add_argument('source', nargs='?', help='源文件夹路径')
    parser.add_argument('target', nargs='?', help='目标文件夹路径（U盘路径）')
    parser.add_argument('-d', '--delete', action='store_true', 
                        help='删除目标目录中源目录不存在的文件')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='模拟运行，不实际复制文件')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='静默模式，减少输出')
    parser.add_argument('--config', help='使用配置文件')
    
    args = parser.parse_args()
    
    if args.config:
        config = parse_config(args.config)
        source = config.get('source')
        target = config.get('target')
        delete_extra = config.get('delete_extra', False) == 'true'
        dry_run = args.dry_run
        verbose = not args.quiet
        
        if not source or not target:
            print("[错误] 配置文件必须包含 source 和 target")
            return
    else:
        source = args.source
        target = args.target
        delete_extra = args.delete
        dry_run = args.dry_run
        verbose = not args.quiet
        
        if not source or not target:
            parser.print_help()
            return
    
    syncer = FolderSyncer(
        source=source,
        target=target,
        delete_extra=delete_extra,
        dry_run=dry_run,
        verbose=verbose
    )
    syncer.sync()


if __name__ == '__main__':
    main()
