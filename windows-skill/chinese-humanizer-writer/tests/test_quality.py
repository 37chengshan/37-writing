import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import platform_quality_gate as gate
import audit_chinese_ai_flavor as flavor
import prepare_campaign as campaign


class QualityTests(unittest.TestCase):
    def test_x_weighted_cjk_and_link(self):
        self.assertEqual(gate.x_weight_estimate('你好'),4)
        self.assertEqual(gate.x_weight_estimate('https://example.com/a'),23)
        self.assertEqual(gate.x_weight_estimate('abc'),3)

    def test_x_thread_per_post(self):
        x='你好，第一条事实。\n\n<!-- POST -->\n\n再来看第二条事实。'
        r=gate.validate('x',x)
        self.assertEqual(r['metrics']['post_count'],2)
        self.assertTrue(r['passed_static_gate'])

    def test_x_over_limit_blocks(self):
        r=gate.validate('x','中'*141)
        self.assertFalse(r['passed_static_gate'])
        self.assertTrue(any('超过' in e for e in r['errors']))

    def test_xhs_title_warns_and_three_lines(self):
        raw='---\ntitle: "这是一个非常非常非常非常非常非常非常长的小红书测试标题"\n---\n\n第一次看懂工具。\n给你三个步骤。\n第三步最容易出错。\n\n#工具教程'
        r=gate.validate('xiaohongshu',raw)
        self.assertEqual(len(r['metrics']['first_3_nonempty_lines']),3)
        self.assertTrue(any('标题超过' in x for x in r['warnings']))

    def test_evidence_verified_without_url_blocks(self):
        x=gate.validate('wechat','---\ntitle: "证据"\n---\n\n正文。',{'claims':[{'statement':'收入超过一千','status':'verified','source_url':''}]})
        self.assertFalse(x['passed_static_gate'])
        self.assertTrue(any('来源链接' in e for e in x['errors']))

    def test_unverified_claim_blocks(self):
        x=gate.validate('x','这是我的看法',{'claims':[{'statement':'没核实的数字','status':'unverified'}]})
        self.assertFalse(x['passed_static_gate'])

    def test_original_numeric_change_blocks_even_good_style(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); orig=p/'old.md'; targ=p/'new.md'
            orig.write_text('# 标题\n\n项目花了100元。',encoding='utf-8')
            targ.write_text('# 标题\n\n项目花了200元。',encoding='utf-8')
            result=flavor.audit_file(targ,orig)
            self.assertIn('200',result['preservation_check']['invented_numbers'])
            self.assertTrue(result['hard_errors'])
            self.assertFalse(result['scores']['Pass (门禁通过 >=40)'])

    def test_protected_inline_code_and_tables(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'orig.md';b=Path(d)/'new.md'
            a.write_text('这是命令 `python -V`。\n\n| 列 | 值 |\n|---|---|\n| 金额 | 3万 |',encoding='utf-8')
            b.write_text('这是命令 `python -vv`。\n\n| 列 | 值 |\n|---|---|\n| 金额 | 3亿 |',encoding='utf-8')
            result=flavor.audit_file(b,a)
            self.assertFalse(result['preservation_check']['inline_code_preserved'])
            self.assertFalse(result['preservation_check']['markdown_tables_preserved'])
            self.assertFalse(result['scores']['Pass (门禁通过 >=40)'])

    def test_campaign_no_overwrite_and_unicode(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'中文项目'; files=campaign.prepare(out,'历史人物','自有号',['wechat','x'])
            self.assertEqual(len(files),5)
            with self.assertRaises(FileExistsError):campaign.prepare(out,'历史人物','自有号',['wechat'])
            brief=json.loads((out/'brief.json').read_text(encoding='utf-8'))
            self.assertTrue(brief['human_approval_required'])
            self.assertIn('中文',str(out))

if __name__=='__main__':unittest.main()
