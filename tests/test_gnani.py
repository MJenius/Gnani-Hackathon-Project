import base64
import io
import json
import os
import sqlite3
import struct
import tempfile
import unittest
import wave
from contextlib import closing
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from app.api.main import app
from app.agent.planner.evon import EvonClient
from app.speech.gnani import ProviderError, synthesize, transcribe, wav_info
from app.speech.usage import BudgetExceeded

def audio():
    output=io.BytesIO()
    with wave.open(output,'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000)
        wav.writeframes(b'\0\0'*1600)
    return output.getvalue()

class GnaniTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ, {'GNANI_API_KEY':'test-only-placeholder',
            'DRIVEOS_USAGE_DB':self.temp.name+'/usage.sqlite3', 'DRIVEOS_DB':self.temp.name+'/missions.sqlite3',
            'DRIVEOS_VOICE_DB':self.temp.name+'/voice.sqlite3', 'DRIVEOS_API_STAGE':'eval',
            'DRIVEOS_API_MAX_REQUESTS':'10','EVON_BASE_URL':'','EVON_MODEL':''})
        self.env.start(); self.client=TestClient(app)

    def tearDown(self):
        self.client.close(); self.env.stop(); self.temp.cleanup()

    def test_real_contract_and_metadata_only_logging(self):
        def provider(url,**kwargs):
            self.assertEqual(kwargs['headers']['X-API-Key-ID'],'test-only-placeholder')
            self.assertTrue(url.startswith('https://api.vachana.ai/'))
            if url.endswith('/stt/v3'):
                self.assertEqual(kwargs['data']['format'],'transcribe')
                self.assertEqual(kwargs['data']['language_code'],'kn-IN')
                return httpx.Response(200,json={'success':True,'transcript':'Synthetic transcript'})
            self.assertEqual(kwargs['json']['model'],'timbre-v2.5')
            self.assertEqual(kwargs['json']['voice'],'Saanvi')
            return httpx.Response(200,content=audio())
        with patch('app.speech.gnani.httpx.post',side_effect=provider):
            self.assertEqual(transcribe(audio(),'kn-IN'),'Synthetic transcript')
            self.assertEqual(synthesize('Synthetic speech','kn-IN'),audio())
        with closing(sqlite3.connect(os.environ['DRIVEOS_USAGE_DB'])) as db:
            rows=db.execute('SELECT * FROM usage').fetchall()
            self.assertEqual(len(rows),2)
            self.assertNotIn('test-only-placeholder',str(rows))
            self.assertNotIn('Synthetic speech',str(rows))
            self.assertNotIn('Synthetic transcript',str(rows))

    def test_streaming_wav_header_repaired(self):
        streamed=bytearray(audio())
        struct.pack_into('<I',streamed,4,0xffffffff)
        struct.pack_into('<I',streamed,40,0xfffffffe)
        with patch('app.speech.gnani.httpx.post',return_value=httpx.Response(200,content=bytes(streamed))):
            output=synthesize('Synthetic speech')
        self.assertEqual(wav_info(output)['audio_seconds'],0.1)

    def test_invalid_audio_never_calls_provider(self):
        with patch('app.speech.gnani.httpx.post') as call:
            with self.assertRaises(ValueError): transcribe(b'invalid')
            call.assert_not_called()

    def test_rate_limit_sanitized_and_no_retry(self):
        response=httpx.Response(429,text='credential=test-only-placeholder')
        with patch('app.speech.gnani.httpx.post',return_value=response) as call:
            with self.assertRaisesRegex(ProviderError,'HTTP 429'): synthesize('Synthetic speech')
            self.assertEqual(call.call_count,1)

    def test_budget_blocks_before_network(self):
        with patch.dict(os.environ,DRIVEOS_API_MAX_REQUESTS='0'),patch('app.speech.gnani.httpx.post') as call:
            with self.assertRaises(BudgetExceeded): synthesize('Synthetic speech')
            call.assert_not_called()

    def test_full_live_unavailable_without_evon(self):
        with patch('app.speech.loop.transcribe') as call:
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},
                data={'request_key':'one','mode':'live','authorized':'true'})
            self.assertEqual(response.status_code,503)
            call.assert_not_called()

    def test_voice_loop_replay_and_collision(self):
        with patch('app.speech.loop.transcribe',return_value='Tell Ananya I am 25 minutes late.') as stt, \
             patch('app.speech.loop.synthesize',return_value=audio()):
            data={'request_key':'voice-one','mode':'speech_test','authorized':'true'}
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['status'],'COMPLETED')
            self.assertEqual(base64.b64decode(response.json()['audio_base64']),audio())
            replay=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data)
            self.assertEqual(replay.json()['id'],response.json()['id'])
            self.assertEqual(stt.call_count,1)
            data['language']='kn-IN'
            self.assertEqual(self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data).status_code,422)
        with closing(sqlite3.connect(os.environ['DRIVEOS_DB'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0],1)

    def test_tts_failure_preserves_committed_mission(self):
        with patch('app.speech.loop.transcribe',return_value='Tell Ananya I am 25 minutes late.'), \
             patch('app.speech.loop.synthesize',side_effect=ProviderError('HTTP 429')):
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},
                data={'request_key':'one','mode':'speech_test','authorized':'true'})
        self.assertEqual(response.json()['status'],'COMPLETED')
        self.assertIsNone(response.json()['audio_base64'])
        self.assertIn('429',response.json()['speech_error'])

    def test_evon_english_kannada_contract_offline(self):
        output=json.dumps({'goal':'Notify Ananya','tasks':[{'tool':'contact.notify_delay','contact':'Ananya','delay_minutes':25}],
                           'next_action':'contact.notify_delay','needs_confirmation':False})
        for text in ['Tell Ananya I am 25 minutes late.','ನಾನು ಇಪ್ಪತ್ತೈದು ನಿಮಿಷ ತಡವಾಗುತ್ತೇನೆ ಎಂದು ಅನನ್ಯ ಅವರಿಗೆ ತಿಳಿಸಿ.']:
            # Contract test only. This is explicitly not a real Evon inference result.
            client=EvonClient(completion=lambda messages:output)
            self.assertEqual(client.extract(text)['delay_minutes'],25)

    def test_evon_unsafe_output_rejected(self):
        for output in ['not JSON',json.dumps({'goal':'Pay','tasks':[{'tool':'payment.purchase','contact':'Ananya','delay_minutes':25}],
                    'next_action':'contact.notify_delay','needs_confirmation':False})]:
            with self.assertRaises(ProviderError): EvonClient(completion=lambda messages:output).plan('Buy fuel')

if __name__=='__main__': unittest.main()
