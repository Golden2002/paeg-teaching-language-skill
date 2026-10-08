# -*- coding: utf-8 -*-
"""命令行入口：check / fix / report"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import List

from .checker import Violation, check_path, load_config, summarize
from .fixer import fix_json_file, fix_markdown_file


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    violations: List[Violation] = check_path(args.path, cfg)
    if args.json:
        json.dump([v.to_dict() for v in violations], open(args.json, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    print('=' * 68)
    print(f'检查对象：{args.path}')
    print(f'违规总数：{len(violations)}')
    if violations:
        print('按类别统计：', dict(Counter(v.category for v in violations)))
        print('按规则统计：', dict(Counter(v.rule for v in violations)))
        print('-' * 68)
        shown = 0
        for v in violations:
            print(f'[{v.category}] {v.rule}｜{v.where}｜命中"{v.hit}"｜建议：{v.advice}')
            print(f'    上下文：{v.sample}')
            shown += 1
            if args.limit and shown >= args.limit:
                print(f'…… 其余 {len(violations) - shown} 条见报告文件')
                break
    else:
        print('未发现规范问题。')
    print('=' * 68)
    return 1 if violations else 0


def cmd_fix(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    targets: List[str] = []
    if os.path.isfile(args.path):
        targets = [args.path]
    else:
        for root, _dirs, files in os.walk(args.path):
            for name in sorted(files):
                if os.path.splitext(name)[1].lower() in ('.md', '.txt', '.json'):
                    targets.append(os.path.join(root, name))
    changed = 0
    for p in targets:
        if p.lower().endswith('.json'):
            before = open(p, encoding='utf-8').read()
            fix_json_file(p, cfg, write=args.write)
            after = open(p, encoding='utf-8').read()
        else:
            before = open(p, encoding='utf-8').read()
            after = fix_markdown_file(p, cfg, write=args.write)
        if before != after:
            changed += 1
            print(('已写回：' if args.write else '待修复（预览）：') + p)
    print(f'共处理 {len(targets)} 个文件，其中 {changed} 个存在可机械修复的问题。')
    if not args.write:
        print('提示：加 --write 才会写回文件。')
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='paeg_teaching_language',
                                description='中文教学语言规范检查与修复工具')
    sub = p.add_subparsers(dest='cmd', required=True)

    c = sub.add_parser('check', help='检查文件或目录')
    c.add_argument('path')
    c.add_argument('--config', help='额外词库配置（JSON）')
    c.add_argument('--json', help='将完整报告写入 JSON 文件')
    c.add_argument('--limit', type=int, default=50, help='终端打印条数上限')
    c.set_defaults(func=cmd_check)

    f = sub.add_parser('fix', help='修复可机械替换的问题')
    f.add_argument('path')
    f.add_argument('--config', help='额外词库配置（JSON）')
    f.add_argument('--write', action='store_true', help='写回文件（默认仅预览）')
    f.set_defaults(func=cmd_fix)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
