"""End-to-end offline workflow + command exit code smoke tests."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def call(script, *args):
    return subprocess.run([sys.executable, str(ROOT/'scripts'/script), *map(str,args)],
                          capture_output=True, text=True, encoding='utf-8')

class WorkflowTests(unittest.TestCase):
    def test_workflow_project_to_three_release_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp)/'中文项目'
            res=call('prepare_campaign.py','--topic','实际核验案例','--account','自有账号','--out',work)
            self.assertEqual(res.returncode,0,res.stderr)
            # These are fictional test strings, not factual publications.
            (work/'draft-wechat.md').write_text('---\ntitle: "测试：一个好问题"\n---\n\n主人公先做了一个决定。随后他发现，成本不只是账面上的数字。接下来的选择决定了最终结果。\n',encoding='utf-8')
            (work/'draft-x.md').write_text('一个好问题：账面有利润，现金就一定够用吗？\n\n<!-- POST -->\n\n第二条：应检查收款时点与固定支出，而不能只看利润。',encoding='utf-8')
            (work/'draft-xiaohongshu.md').write_text('---\ntitle: "账面利润和现金流"\n---\n\n开店的人先看过来。\n利润高不代表能付房租。\n教你列一张现金流核对表。\n\n步骤一：列出已收款金额。\n步骤二：列出应付账款。\n#开店经验',encoding='utf-8')
            for platform in ('wechat','x','xiaohongshu'):
                res=call('platform_quality_gate.py','--platform',platform,'--input',work/f'draft-{platform}.md','--json','--strict')
                self.assertEqual(res.returncode,0,res.stdout+'\n'+res.stderr)
                self.assertTrue(json.loads(res.stdout)['passed_static_gate'])

    def test_unfinished_template_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp)/'project'
            self.assertEqual(call('prepare_campaign.py','--topic','练习','--account','自有','--out',work).returncode,0)
            for platform in ('wechat','x','xiaohongshu'):
                res=call('platform_quality_gate.py','--platform',platform,'--input',work/f'draft-{platform}.md','--json','--strict')
                self.assertEqual(res.returncode,2,(platform,res.stdout,res.stderr))

    def test_archive_distill_then_learning_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            f=root/'raw.md'
            f.write_text('---\ntitle: "测试故事"\ndate: "2026-11-01"\nauthor: "A"\n---\n\n# 测试故事\n\n我读了第一份报告。结果并没有那么简单。\n\n再核对另一条证据，事情出现了反转。',encoding='utf-8')
            out=root/'profiles'
            res=call('fetch_and_archive_articles.py','--input',f,'--account','测试号','--track','self','--platform','wechat','--base-dir',out)
            self.assertEqual(res.returncode,0,res.stderr)
            prof=out/'our_own_voice'/'测试号'
            res=call('distill_style_dna.py','--profile-dir',prof,'--platform','wechat')
            self.assertEqual(res.returncode,0,res.stderr)
            result=json.loads(res.stdout)
            self.assertEqual(result['platform_filter'],'wechat')
            self.assertTrue((prof/'platforms'/'wechat'/'Writing-DNA.md').exists())
            self.assertFalse((prof/'Writing-DNA.md').exists())
            draft=root/'draft.md';final=root/'final.md'
            draft.write_text('---\ntitle: "新稿"\n---\n\n值得注意的是，账上有钱也有风险。',encoding='utf-8')
            final.write_text('---\ntitle: "新稿"\n---\n\n账上有钱，也可能马上没钱。',encoding='utf-8')
            res=call('learn_from_user_edits.py','--draft',draft,'--final',final,'--profile-dir',prof,'--platform','wechat')
            self.assertEqual(res.returncode,0,res.stderr)
            report=json.loads(res.stdout)
            self.assertEqual(report['platform'],'wechat')
            ledger=json.loads((prof/'evolution_ledger.json').read_text(encoding='utf-8'))
            self.assertEqual(ledger['total_edit_sessions'],1)
            self.assertEqual(ledger['candidate_banned_phrases'].get('值得注意的是'),1)
            res=call('learn_from_user_edits.py','--draft',draft,'--final',final,'--profile-dir',prof,'--platform','wechat')
            self.assertEqual(res.returncode,0,res.stderr)
            self.assertEqual(json.loads((prof/'evolution_ledger.json').read_text(encoding='utf-8'))['total_edit_sessions'],1)

    def test_external_track_rejects_learning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a=root/'a.md';b=root/'b.md'
            a.write_text('原文。',encoding='utf-8');b.write_text('修改的原文。',encoding='utf-8')
            external=root/'external_benchmarks'/'外部号'
            res=call('learn_from_user_edits.py','--draft',a,'--final',b,'--profile-dir',external)
            self.assertEqual(res.returncode,2)
            self.assertFalse(external.exists())

    def test_audit_cli_strict_numeric_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            orig=root/'orig.md';fin=root/'fin.md'
            orig.write_text('原来的价格是50元。',encoding='utf-8')
            fin.write_text('原来的价格是80元。',encoding='utf-8')
            res=call('audit_chinese_ai_flavor.py',fin,'--original',orig,'--json','--strict')
            self.assertEqual(res.returncode,2,res.stdout+'\n'+res.stderr)
            self.assertTrue(json.loads(res.stdout)['hard_errors'])

if __name__ == '__main__': unittest.main()
