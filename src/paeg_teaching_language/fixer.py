# -*- coding: utf-8 -*-
"""修复器：对可机械替换的问题做批量改正（比喻词、口语词、标点格式）。"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Tuple

from .checker import CJK, load_config

# 机械可替换的默认对照表（可由 data/replacements.json 覆盖或增补）
DEFAULT_PAIRS: List[Tuple[str, str]] = [
    ('各管一摊', '各有分工'),
    ('抱团', '组合'),
    ('认全', '辨认'),
    ('搞定', '完成'),
    ('干货', '要点'),
    ('抓手', '切入点'),
    ('秒懂', '迅速理解'),
    ('包袱', '限定'),
    ('建筑材料', '基本单位'),
    ('承重构件', '组合单位'),
]

# 中文之间的半角斜杠、加号 → 顿号
RE_SLASH = re.compile('([' + CJK + r'])\s*[/／]\s*([' + CJK + r'])')
RE_PLUS = re.compile('([' + CJK + r'])\s*\+\s*([' + CJK + r'])')


def pairs_from_config(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    pairs = list(DEFAULT_PAIRS)
    for item in cfg.get('replacements', []):
        if isinstance(item, dict) and item.get('from'):
            pairs.append((item['from'], item.get('to', '')))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            pairs.append((item[0], item[1]))
    # 长词优先，避免短词先替换破坏长词
    pairs.sort(key=lambda x: -len(x[0]))
    return pairs


def fix_text(text: str, cfg: Dict[str, Any] | None = None) -> str:
    cfg = cfg or load_config()
    out = text
    for a, b in pairs_from_config(cfg):
        out = out.replace(a, b)
    out = RE_SLASH.sub(r'\1、\2', out)
    out = RE_PLUS.sub(r'\1、\2', out)
    return out


def fix_markdown_file(path: str, cfg: Dict[str, Any] | None = None, write: bool = False) -> str:
    cfg = cfg or load_config()
    text = open(path, encoding='utf-8').read()
    fixed = fix_text(text, cfg)
    if write and fixed != text:
        open(path, 'w', encoding='utf-8').write(fixed)
    return fixed


def fix_json_file(path: str, cfg: Dict[str, Any] | None = None, write: bool = False) -> Any:
    """修复课件类 JSON；英文例句字段（en）保持原样。"""
    cfg = cfg or load_config()
    data = json.load(open(path, encoding='utf-8'))

    def walk(obj):
        if isinstance(obj, dict):
            return {k: (v if k == 'en' else walk(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        if isinstance(obj, str):
            return fix_text(obj, cfg)
        return obj

    fixed = walk(data)
    if write:
        json.dump(fixed, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return fixed
