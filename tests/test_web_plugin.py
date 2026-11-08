import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'chatgpt-plugin' / '37-writing'


class WebPluginContract(unittest.TestCase):
    def test_manifest(self):
        data = json.loads((PACKAGE / 'plugin.json').read_text(encoding='utf-8'))
        self.assertEqual(data['name'], '37-writing')
        self.assertEqual(data['$schema'], 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json')
        self.assertRegex(data['version'], r'^\d+\.\d+\.\d+$')
        ui = data['extensions']['com.openai']['interface']
        self.assertLessEqual(len(ui['shortDescription']), 30)
        self.assertEqual(ui['category'], 'Productivity')

    def test_six_valid_skills(self):
        files = list((PACKAGE / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(files), 6)
        names = set()
        for f in files:
            content = f.read_text(encoding='utf-8')
            self.assertTrue(content.startswith('---\n'), f)
            front = content.split('---', 2)[1]
            name = re.search(r'(?m)^name:\s*(.+)$', front)
            desc = re.search(r'(?m)^description:\s*(.+)$', front)
            self.assertIsNotNone(name, f)
            self.assertIsNotNone(desc, f)
            self.assertEqual(name.group(1).strip(), f.parent.name)
            self.assertTrue(desc.group(1).strip())
            self.assertNotIn(f.parent.name, names)
            names.add(f.parent.name)

    def test_cross_skill_references(self):
        for f in (PACKAGE / 'skills').glob('*/SKILL.md'):
            source = f.read_text(encoding='utf-8')
            for relative in re.findall(r'`(\.\./[^`]+\.md)`', source):
                self.assertTrue((f.parent / relative).is_file(), (f, relative))

    def test_web_only_no_local_command_in_docs(self):
        content = '\n'.join(f.read_text(encoding='utf-8') for f in PACKAGE.rglob('*.md'))
        self.assertNotRegex(content, r'(?m)^\s*(?:py -3|python3? )\s+.*scripts/')
        self.assertFalse((PACKAGE / 'mcp.json').exists())
        self.assertFalse((PACKAGE / 'skills' / 'writing-workbench' / 'references' / 'self-evolving-diff-learning.md').exists())
        self.assertTrue((PACKAGE / 'skills' / 'writing-workbench' / 'references' / 'user-edit-feedback.md').exists())


if __name__ == '__main__':
    unittest.main()
