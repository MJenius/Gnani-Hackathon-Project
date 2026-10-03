import unittest
import os
import tempfile
from app.evaluation.runners import gnani_smoke
from pathlib import Path
from unittest.mock import patch
from app.agent.planner.evon import MockEvon
from notebooks.evon_free_gpu import preflight, server_args, correct_plan

class FreeEvonTests(unittest.TestCase):
    def test_missing_audio_cache_never_spends_credits(self):
        old=Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as folder:
                os.chdir(folder)
                with patch('sys.argv',['gnani_smoke','--speech','--case','english','--reuse-fixtures']), patch('builtins.print'), patch.object(gnani_smoke,'synthesize') as tts, patch.object(gnani_smoke,'transcribe') as stt:
                    with self.assertRaises(SystemExit): gnani_smoke.main()
                    tts.assert_not_called();stt.assert_not_called()
                os.chdir(old)
        finally: os.chdir(old)

    def test_mock_remains_offline(self):
        with patch('httpx.post') as network:
            self.assertEqual(MockEvon().extract('Tell Ananya I am 25 minutes late.'),{'contact':'Ananya','delay_minutes':25})
            self.assertIsNone(MockEvon().extract('Buy fuel'))
            network.assert_not_called()

    def test_local_download_guard(self):
        with patch('notebooks.evon_free_gpu.platform.system',return_value='Windows'):
            with self.assertRaises(RuntimeError): preflight()

    def test_dual_gpu_split_and_small_context(self):
        args=server_args(Path('/bin/llama-server'),Path('/models/model.gguf'),{'gpu_free_mib':[15000,15000]})
        self.assertEqual(args[args.index('--tensor-split')+1],'1,1')
        self.assertEqual(args[args.index('-c')+1],'2048')
        self.assertEqual(args[args.index('--host')+1],'127.0.0.1')

    def test_semantic_and_script_check_not_just_valid_json(self):
        plan={'goal':'Notify Ananya','tasks':[{'tool':'contact.notify_delay','contact':'Ananya','delay_minutes':25}],
              'next_action':'contact.notify_delay','needs_confirmation':False}
        self.assertTrue(correct_plan(plan,'en-IN'))
        self.assertFalse(correct_plan(plan,'kn-IN'))
        plan['goal']='ಅನನ್ಯ ಅವರಿಗೆ ತಿಳಿಸಿ'
        self.assertTrue(correct_plan(plan,'kn-IN'))
        plan['tasks'][0]['delay_minutes']=True
        self.assertFalse(correct_plan(plan,'kn-IN'))

if __name__=='__main__': unittest.main()
