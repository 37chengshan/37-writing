import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import learn_from_user_edits as learning


class LearningTests(unittest.TestCase):
    def test_candidate_needs_three_independent_sessions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'our_own_voice'/'我';
            for n in range(1,4):
                x={'killed_phrases':['值得注意的是'], 'sentence_replacements':[],
                   'learned_rules':[], 'final_metrics':{'mean_sent_len':14,'mean_para_chars':35,
                   'em_dash_per_1k':0,'paren_per_1k':0,'quest_per_1k':0}}
                learning.update_evolution_ledger(root,x,str(n))
                ledger=json.loads((root/'evolution_ledger.json').read_text(encoding='utf-8'))
                self.assertEqual(ledger['total_edit_sessions'],n)
                self.assertEqual('值得注意的是' in ledger['hard_banned_phrases'],n>=3)
            learning.update_evolution_ledger(root,x,'3')
            ledger=json.loads((root/'evolution_ledger.json').read_text(encoding='utf-8'))
            self.assertEqual(ledger['total_edit_sessions'],3)

    def test_diff_detects_phrase_removal(self):
        insights=learning.extract_diff_insights('值得注意的是，这一问题很严重。','问题很严重。')
        self.assertIn('值得注意的是',insights['killed_phrases'])

if __name__=='__main__':unittest.main()
