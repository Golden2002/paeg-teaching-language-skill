# -*- coding: utf-8 -*-
"""检查器自测。

运行方式（无需第三方依赖）：
    python -m unittest discover -s tests -v
也兼容 pytest：
    python -m pytest tests -q
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from paeg_teaching_language import check_json, check_text, fix_text, load_config  # noqa: E402

CFG = load_config()


def rules(text, kind='body'):
    return [v.rule for v in check_text(text, 'test', CFG, kind)]


class TestChecker(unittest.TestCase):
    def test_口语化违禁词被检出(self):
        vs = check_text('词单独存在时，谈不上主语或宾语。', 'test', CFG)
        self.assertTrue(any(v.category == '禁用词' and v.hit == '谈不上' for v in vs))

    def test_比喻式表述被检出(self):
        vs = check_text('谓语动词要背三个包袱。', 'test', CFG)
        self.assertTrue(any(v.hit == '包袱' for v in vs))

    def test_并列使用加号被检出(self):
        self.assertIn('并列词语之间使用加号', rules('判断依据是位置 + 关系 + 功能。'))

    def test_英文公式中的加号不误判(self):
        self.assertNotIn('并列词语之间使用加号', rules('to + 动词原形'))
        self.assertNotIn('并列词语之间使用加号', rules('To do sth. + 谓语'))

    def test_并列使用斜杠被检出(self):
        self.assertIn('并列词语之间使用斜杠', rules('记得去做 / 记得做过。'))

    def test_半角标点混入中文被检出(self):
        self.assertIn('半角标点混入中文', rules('词进入句子,才开始承担成分。'))

    def test_标题末尾句号被检出(self):
        self.assertIn('标题末尾使用句号', rules('词进入句子，才有成分。', kind='title'))
        self.assertNotIn('标题末尾使用句号', rules('词进入句子，才有成分。', kind='body'))

    def test_层级数字混用被检出(self):
        self.assertIn('层级编号使用阿拉伯数字', rules('这正是第 2 讲要讨论的内容。'))

    def test_祈使式讲解被检出(self):
        self.assertIn('讲解使用祈使句', rules('记住连词就记住了从句。'))

    def test_第二人称被检出_译文豁免(self):
        self.assertIn('讲解使用第二人称', rules('你应当先找出逻辑主语。'))
        self.assertNotIn('讲解使用第二人称', rules('我要是你，我就去。', kind='translation'))

    def test_省略号与等连用被检出(self):
        self.assertIn('省略号与“等”连用', rules('短语、从句、分词……等成分。'))

    def test_超长句被检出(self):
        long_sentence = '这是一个用于测试超长句判定的句子，' * 4 + '它明显超过了规定长度。'
        self.assertIn('单句超过规定长度', rules(long_sentence))

    def test_英文例子不参与中文检查(self):
        self.assertEqual(check_text('He works hard, and he is happy.', 'test', CFG, kind='en'), [])

    def test_修复器替换比喻词与标点(self):
        fixed = fix_text('三个包袱：位置 + 关系 + 功能。')
        self.assertNotIn('包袱', fixed)
        self.assertNotIn('+', fixed)

    def test_JSON按字段检查并区分标题与译文(self):
        data = {
            'slides': [
                {'title': '八种成分：看功能就能认出来。',
                 'data': {'items': [
                     {'t': '谓语动词要背三个包袱。'},
                     {'en': 'To + 动词原形 is a formula.'},
                     {'zh': '我要是你，我就去。'},
                 ]}},
            ]
        }
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'deck.json')
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            vs = check_json(p, CFG)
        hits = {v.hit for v in vs}
        self.assertIn('包袱', hits)                       # 正文命中
        self.assertIn('标题末尾使用句号', {v.rule for v in vs})  # 标题字段命中
        self.assertNotIn('你', hits)                       # 译文豁免第二人称
        self.assertFalse(any(v.rule == '并列词语之间使用加号' for v in vs))  # 英文公式豁免

    # ---- 1.0.1 新增：字段类型区分 ----

    def test_教师备注不检查句长与第二人称(self):
        long_note = '本页逐行提问“这个成分承担什么句法功能”，让学生依据功能而不是词形作出判断，约三分钟，必要时请学生举例说明。'
        self.assertEqual(check_text(long_note, 'note', CFG, kind='note'), [])
        self.assertIn('讲解使用第二人称', rules('你应当先找出逻辑主语。'))
        self.assertNotIn('讲解使用第二人称', rules('你先找出逻辑主语。', kind='table'))

    def test_表格单元格不检查第二人称与句长(self):
        cell = '我要是你，我就去。' + '这是一个用于测试的较长说明文字，' * 3
        self.assertEqual(check_text(cell, 'table', CFG, kind='table'), [])

    def test_公式不检查并列连接符号(self):
        self.assertEqual(check_text('to + 动词原形', 'formula', CFG, kind='formula'), [])
        self.assertEqual(check_text('It is + 形容词 + for + 名词 + to do', 'formula', CFG, kind='formula'), [])

    def test_句长只计汉字(self):
        mixed = 'This sentence contains many English words. ' + '汉字句子的长度需要单独计算。'
        self.assertNotIn('单句超过规定长度', rules(mixed))
        long_cn = '这是一个用于测试长度上限的汉语句子，' * 4
        self.assertIn('单句超过规定长度', rules(long_cn))


if __name__ == '__main__':
    unittest.main(verbosity=2)
