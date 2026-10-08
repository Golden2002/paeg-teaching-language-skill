# -*- coding: utf-8 -*-
"""检查器：按教学语言规范诊断文本问题。

设计要点
  · 只依赖标准库；
  · 规则与词库外置在 data/*.json，便于学科自定；
  · 支持纯文本/Markdown（按行）与 JSON（按字段，自动跳过英文例句）。
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CJK = '\u4e00-\u9fff'

# 行首祈使式讲解的常见开头
IMPERATIVE_PATTERNS = [
    r'^记住', r'^牢记', r'^先看', r'^再看', r'^看看', r'^注意背', r'^背下',
    r'^请记住', r'^务必记住', r'^首先要记住',
]
SECOND_PERSON_PATTERNS = [r'你', r'您', r'咱们']

# 视为公式或英文例子的行，不参与部分检查
ASCII_ONLY = re.compile(r'^[\x00-\x7F\s]+$')


@dataclass
class Violation:
    category: str      # 分类：禁用词 / 标点 / 数字 / 语体
    rule: str          # 规则名称
    where: str         # 位置：文件:行 或 字段路径
    hit: str           # 命中内容
    sample: str        # 上下文片段
    advice: str = ''   # 修改建议

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """读取词库与规则配置；传入路径则与该默认配置合并。"""
    cfg: Dict[str, Any] = {'forbidden': [], 'replacements': [], 'rules': {}}
    for name, key in (('forbidden_words.json', 'forbidden'),
                      ('replacements.json', 'replacements'),
                      ('rules.json', 'rules')):
        p = os.path.join(DATA_DIR, name)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                loaded = json.load(f)
            # 支持 {"items": [...]} 与直接列表两种写法
            if isinstance(loaded, dict) and 'items' in loaded:
                cfg[key] = loaded['items']
            elif isinstance(loaded, dict) and 'rules' in loaded:
                cfg[key] = loaded['rules']
            else:
                cfg[key] = loaded
    if config_path and os.path.exists(config_path):
        with open(config_path, encoding='utf-8') as f:
            extra = json.load(f)
        for key in ('forbidden', 'replacements'):
            if key in extra:
                items = extra[key]
                if isinstance(items, dict) and 'items' in items:
                    items = items['items']
                cfg[key] = list(cfg.get(key, [])) + list(items)
        if 'rules' in extra:
            cfg['rules'].update(extra['rules'])
    return cfg


def _forbidden_map(cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    """统一违禁词结构：[{'word':..,'category':..,'advice':..}]"""
    out = []
    for item in cfg.get('forbidden', []):
        if isinstance(item, str):
            out.append({'word': item, 'category': '口语化', 'advice': '改为书面语表述'})
        else:
            out.append({
                'word': item.get('word', ''),
                'category': item.get('category', '口语化'),
                'advice': item.get('advice', '改为书面语表述'),
            })
    return [x for x in out if x['word']]


def check_text(text: str, where: str, cfg: Dict[str, Any], kind: str = 'body') -> List[Violation]:
    """检查一段文本。kind 取值：title / body / translation / en / formula。"""
    t = text or ''
    if kind == 'en' or ASCII_ONLY.match(t.strip() or ' '):
        return []
    out: List[Violation] = []
    rules = cfg.get('rules', {})

    def add(category, rule, hit, advice):
        out.append(Violation(category, rule, where, hit, t[:80], advice))

    # 1 违禁词
    for item in _forbidden_map(cfg):
        if item['word'] and item['word'] in t:
            add('禁用词', f"禁用词：{item['category']}", item['word'], item['advice'])

    # 2 并列连接符号：仅当加号两侧都是汉字时判为并列（英文公式豁免）
    if rules.get('plus_as_conjunction', True):
        for m in re.finditer(r'\+', t):
            left = t[:m.start()].rstrip()
            right = t[m.end():].lstrip()
            if left and right and re.search('[' + CJK + r']$', left) and re.match('[' + CJK + r']', right):
                add('标点', '并列词语之间使用加号', '+', '并列词语之间应当使用顿号或连词“与”')
                break

    # 3 并列斜杠：同样只判两侧都是汉字的情形
    if rules.get('slash_as_conjunction', True):
        for m in re.finditer(r'[/／]', t):
            left = t[:m.start()].rstrip()
            right = t[m.end():].lstrip()
            if left and right and re.search('[' + CJK + r']$', left) and re.match('[' + CJK + r']', right):
                add('标点', '并列词语之间使用斜杠', m.group(0), '并列词语之间应当使用顿号或连词“与”')
                break

    # 4 半角标点混入中文
    if rules.get('halfwidth_punct', True):
        m = re.search('[' + CJK + r'][,;:?!]', t) or re.search('[,;:?!][' + CJK + r']', t)
        if m:
            add('标点', '半角标点混入中文', m.group(0), '中文文本应当使用全角标点')
        if re.search('[' + CJK + r'][()]', t) or re.search(r'[()][' + CJK + r']', t):
            add('标点', '半角括号混入中文', '()', '中文文本应当使用全角括号')

    # 5 省略号与"等"连用
    if re.search(r'…{2,}\s*等', t):
        add('标点', '省略号与“等”连用', '……等', '省略号与“等”二者保留其一')

    # 6 破折号与"即"连用
    if re.search(r'——\s*(即|也就是)', t):
        add('标点', '破折号与“即”连用', '——即', '破折号与“即”二者保留其一')

    # 7 层级数字混用
    if rules.get('level_number', True) and re.search(r'第\s*[0-9]+\s*(讲|章|节|课)', t):
        add('数字', '层级编号使用阿拉伯数字', re.search(r'第\s*[0-9]+\s*(讲|章|节|课)', t).group(0),
            '层级编号应当与上下文保持一致，教学材料通常使用汉字数字')

    # 8 标题末尾句号
    if kind == 'title' and t.strip().endswith('。'):
        add('标点', '标题末尾使用句号', '。', '标题与副标题末尾不加句号')

    # 9 祈使式讲解
    for p in IMPERATIVE_PATTERNS:
        m = re.search(p, t.strip())
        if m:
            add('语体', '讲解使用祈使句', m.group(0), '讲解一律使用有主语的陈述句')
            break

    # 10 第二人称
    if kind not in ('translation', 'en', 'formula'):
        for p in SECOND_PERSON_PATTERNS:
            m = re.search(p, t)
            if m:
                add('语体', '讲解使用第二人称', m.group(0), '讲解中不使用第二人称，可用“学生”或“我们”')
                break

    # 11 超长句
    if rules.get('max_sentence_length'):
        limit = int(rules['max_sentence_length'])
        for sent in re.split(r'[。！？；]', t):
            s = sent.strip()
            if len(s) > limit:
                add('语体', '单句超过规定长度', s[:limit] + '…', f'单句一般不超过 {limit} 字，建议拆分')
                break
    return out


def _is_english(s: str) -> bool:
    return bool(re.search(r'[A-Za-z]{2,}', s)) and not re.search('[' + CJK + r']', s)


def check_json(path: str, cfg: Dict[str, Any]) -> List[Violation]:
    """检查课件类 JSON：按字段性质区分标题、正文、译文与英文。"""
    out: List[Violation] = []
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:  # 无法解析时作为普通文本处理
        return check_file_as_text(path, cfg)

    def walk(obj, path_str, kind='body'):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'en':
                    continue
                child_kind = kind
                if k == 'zh':
                    child_kind = 'translation'
                elif k in ('title', 'subtitle', 'headline', 'kicker'):
                    child_kind = 'title'
                walk(v, f'{path_str}.{k}', child_kind)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f'{path_str}[{i}]', kind)
        elif isinstance(obj, str):
            out.extend(check_text(obj, f'{os.path.basename(path)}:{path_str}', cfg, kind))

    walk(data, '$')
    return out


def check_file_as_text(path: str, cfg: Dict[str, Any]) -> List[Violation]:
    out: List[Violation] = []
    with open(path, encoding='utf-8', errors='replace') as f:
        for ln, line in enumerate(f, 1):
            s = line.rstrip('\n')
            if not re.search('[' + CJK + r']', s):
                continue
            kind = 'title' if s.lstrip().startswith('#') else 'body'
            s2 = re.sub(r'^#+\s*', '', s) if kind == 'title' else s
            out.extend(check_text(s2, f'{os.path.basename(path)}:{ln}', cfg, kind))
    return out


def check_file(path: str, cfg: Optional[Dict[str, Any]] = None) -> List[Violation]:
    cfg = cfg or load_config()
    if path.lower().endswith('.json'):
        return check_json(path, cfg)
    return check_file_as_text(path, cfg)


def check_path(path: str, cfg: Optional[Dict[str, Any]] = None) -> List[Violation]:
    cfg = cfg or load_config()
    if os.path.isfile(path):
        return check_file(path, cfg)
    out: List[Violation] = []
    for root, _dirs, files in os.walk(path):
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() in ('.md', '.txt', '.json'):
                out.extend(check_file(os.path.join(root, name), cfg))
    return out


def summarize(violations: Iterable[Violation]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for v in violations:
        counts[v.category] = counts.get(v.category, 0) + 1
    return counts
