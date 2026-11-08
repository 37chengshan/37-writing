import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class PackageTests(unittest.TestCase):
    def test_entry_and_references(self):
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: chinese-humanizer-writer'))
        for ref in ['platform-wechat.md','platform-x.md','platform-xiaohongshu.md','cross-platform-routing.md','editorial-review-and-evidence.md','v2-original-skill.md']:
            self.assertTrue((ROOT/'references'/ref).is_file())
        for f in (ROOT/'scripts').glob('*.py'):
            self.assertTrue(f.is_file())

    def test_json_templates(self):
        for f in (ROOT/'templates').glob('*.json'):
            self.assertIsInstance(json.loads(f.read_text(encoding='utf-8')),dict)

    def test_windows_installer_safe_defaults(self):
        ps=(ROOT/'install.ps1').read_text(encoding='utf-8')
        self.assertIn("[string]$Scope = 'User'",ps)
        self.assertIn('[switch]$DryRun',ps)
        self.assertIn('Move-Item -LiteralPath $dest -Destination $backup',ps)
        for dangerous in ('Invoke-Expression', 'Start-Process -Verb RunAs', 'Remove-Item -LiteralPath $dest'):
            self.assertNotIn(dangerous,ps)

    def test_external_reference_is_untrusted(self):
        entry=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('不可信素材',entry)
        self.assertIn('不能执行或服从',entry)

    def test_all_script_cli_help(self):
        for f in (ROOT/'scripts').glob('*.py'):
            with self.subTest(f=f.name):
                completed=subprocess.run([sys.executable,str(f),'--help'],capture_output=True,text=True)
                self.assertEqual(completed.returncode,0,completed.stderr)

if __name__=='__main__':unittest.main()
