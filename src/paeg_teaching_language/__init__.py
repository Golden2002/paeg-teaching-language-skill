# -*- coding: utf-8 -*-
"""PAEG 教学语言规范技能：检查与修复中文教学物料语言问题。"""
from .checker import (  # noqa: F401
    Violation,
    check_file,
    check_json,
    check_path,
    check_text,
    load_config,
    summarize,
)
from .fixer import fix_json_file, fix_markdown_file, fix_text  # noqa: F401

__version__ = '1.0.0'
__all__ = [
    'Violation', 'check_file', 'check_json', 'check_path', 'check_text',
    'load_config', 'summarize', 'fix_json_file', 'fix_markdown_file', 'fix_text',
]
