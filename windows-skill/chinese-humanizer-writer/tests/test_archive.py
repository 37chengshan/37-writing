import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import fetch_and_archive_articles as arc
import distill_style_dna as dna


class ArchiveTests(unittest.TestCase):
    HTML='''<!DOCTYPE html><html><head><meta property="og:title" content="钱和人：一篇测试文章"><meta property="og:url" content="https://mp.weixin.qq.com/s?__biz=ABC&amp;mid=123456&amp;idx=2"></head><body><div id="js_content"><p>第一段是真正的观察。</p><p><img data-src="https://example.org/photo.jpg" /></p><p><a href="https://example.org/source">原始资料</a></p><p><a href="javascript:alert(1)">危险链接</a></p><script>alert('x')</script></div></body></html>'''

    def test_html_preserves_images_and_safe_links(self):
        a=arc.parse_wechat_or_generic_html(self.HTML, '测试号')
        self.assertEqual(a['image_count'],1)
        self.assertIn('![配图](https://example.org/photo.jpg)',a['body'])
        self.assertIn('[原始资料](https://example.org/source)',a['body'])
        self.assertNotIn('javascript:',a['body'])
        self.assertNotIn('<script>',a['body'])
        self.assertEqual(a['date'],'unknown')
        self.assertIn('mid=123456',a['source_url'])

    def test_windows_reserved_names(self):
        self.assertEqual(arc.sanitize_filename('CON'),'_CON')
        self.assertEqual(arc.sanitize_filename('LPT1.txt'),'_LPT1.txt')
        self.assertEqual(arc.sanitize_filename('a:b/c'),'a_b_c')

    def test_dedup_idempotence_and_json_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); f=p/'in.html';f.write_text(self.HTML,encoding='utf-8')
            out=p/'profiles'
            one=arc.archive_inputs(f,out,'测试号','external','wechat','深度分析')
            two=arc.archive_inputs(f,out,'测试号','external','wechat','深度分析')
            self.assertEqual(one['imported_count'],1)
            self.assertEqual(two['imported_count'],0)
            self.assertEqual(two['skipped_duplicates_count'],1)
            prof=out/'external_benchmarks'/'测试号'
            self.assertEqual(len(list((prof/'raw').glob('*.md'))),1)
            data=json.loads(next((prof/'_meta').glob('*.json')).read_text(encoding='utf-8'))
            self.assertEqual(data['dedup_key'],'wx_mid_123456_idx_2')
            self.assertIn('00-索引', (prof/'00-索引.md').read_text(encoding='utf-8'))

    def test_platform_filter_and_track_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'our_own_voice'/'作者'; (root/'raw').mkdir(parents=True)
            (root/'raw'/'a.md').write_text('---\ntrack: "self"\nplatform: "wechat"\n---\n\n# A\n\n长文有起有伏。过了几天，故事发生变化。',encoding='utf-8')
            (root/'raw'/'b.md').write_text('---\ntrack: "self"\nplatform: "x"\n---\n\n# B\n\n短帖只讲一件事。',encoding='utf-8')
            stats=dna.analyze_corpus_l1_l6(root,'wechat')
            self.assertEqual(stats['article_count'],1)
            self.assertEqual(stats['platform'],'wechat')
            with self.assertRaises(ValueError):dna.analyze_corpus_l1_l6(root/'raw')
            (root/'raw'/'a.md').write_text('---\ntrack: "external"\nplatform: "wechat"\n---\n\n错误轨道',encoding='utf-8')
            with self.assertRaises(ValueError):dna.analyze_corpus_l1_l6(root,'wechat')

if __name__=='__main__':unittest.main()
