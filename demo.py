# -*- coding: utf-8 -*-
"""一分钟演示：诊断一段典型的教学文本问题，并给出修复结果。

运行：
    python demo.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from paeg_teaching_language import check_text, fix_text, load_config  # noqa: E402

BAD_TEXT = (
    '词单独存在时只是一个词，谈不上主语或宾语；词进入句子才开始各司其职，'
    '所以词类是身份，句子成分是岗位。判断依据是位置 + 关系 + 功能。'
    '谓语动词要背三个包袱——即时态、语态和语气。记住连词就记住了从句。'
)

GOOD_TEXT = (
    '词在独立状态下不充当句子成分，句子成分只在词进入句子以后产生。'
    '词类指词的语法类别，句子成分指词在句中的句法功能。'
    '判断句子成分的依据有三项：词在句中的位置、词与相邻词的结构关系。'
    '此外还要看词所承担的句法功能。'
    '谓语动词受时态、语态和语气限定。从属连词是识别状语从句类型的主要标志。'
)


def main() -> int:
    cfg = load_config()
    print('=' * 72)
    print('【待检查文本】')
    print(BAD_TEXT)
    print('-' * 72)
    violations = check_text(BAD_TEXT, 'demo', cfg)
    print(f'共发现 {len(violations)} 处问题：')
    for v in violations:
        print(f'  · [{v.category}] {v.rule}｜命中“{v.hit}”｜{v.advice}')
    print('-' * 72)
    print('【机械修复后（仅处理可替换项，语体问题仍需人工改写）】')
    print(fix_text(BAD_TEXT, cfg))
    print('-' * 72)
    print('【改写示例（人工终审后的合格文本）】')
    print(GOOD_TEXT)
    remain = check_text(GOOD_TEXT, 'demo', cfg)
    print(f'改写后剩余问题：{len(remain)} 处')
    print('=' * 72)
    return 0


if __name__ == '__main__':
    sys.exit(main())
