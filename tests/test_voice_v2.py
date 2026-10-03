import json
import os
import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
import unittest
import test_gnani
import httpx
audio=test_gnani.audio
from app.mission.execution import persistent
from app.agent.planner.contract import planning_input
from app.agent.planner.evon import MockEvon
from app.speech.normalize import normalize

class VoiceV2Tests(unittest.TestCase):
    setUp=test_gnani.GnaniTests.setUp
    tearDown=test_gnani.GnaniTests.tearDown
    def test_persistent_voice_execution_and_cached_completion(self):
        text=json.loads(Path('app/evaluation/fixtures/voice_missions.json').read_text(encoding='utf-8'))[0]['text']
        with patch('app.speech.loop.transcribe',return_value=text) as stt, patch('app.speech.loop.synthesize',return_value=audio()) as tts:
            data={'request_key':'v2','mode':'speech_test','authorized':'true','persistent_mission':'true','demo':'parking-change'}
            def start(): return self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data)
            response=start();self.assertEqual(response.status_code,200,response.text)
            mission=response.json();self.assertEqual(mission['engine_version'],2)
            self.assertEqual(start().json()['id'],mission['id']);self.assertEqual(stt.call_count,1)
            self.assertEqual(tts.call_count,1)
            for index in range(30):
                if mission['status']!='EXECUTING': break
                mission=persistent.command(mission['id'],'advance',{'request_key':str(index),'expected_revision':mission['revision']})
            self.assertEqual(mission['status'],'COMPLETED');self.assertEqual(mission['route']['parking']['id'],'p2')
            self.assertEqual(persistent.get(mission['id']),mission)
            body={'expected_revision':mission['revision']}
            endpoint='/missions/'+mission['id']+'/speech'
            count=tts.call_count
            for _ in range(2): self.assertEqual(self.client.post(endpoint,json=body).status_code,200)
            self.assertEqual(tts.call_count,count+1)
            self.assertEqual(self.client.post(endpoint,json={'expected_revision':0}).status_code,409)
            self.assertIn('CALL_RESULT',[event['status'] for event in mission['events']])

    def test_v2_voice_failure_replay_and_engine_collision(self):
        from app.speech.gnani import ProviderError
        text=json.loads(Path('app/evaluation/fixtures/voice_missions.json').read_text(encoding='utf-8'))[0]['text']
        data={'request_key':'failure','mode':'speech_test','authorized':'true','persistent_mission':'true'}
        with patch('app.speech.loop.transcribe',return_value=text) as stt,patch('app.speech.loop.synthesize',side_effect=ProviderError('HTTP 429')):
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data)
            self.assertEqual(response.status_code,200)
            mission=response.json();self.assertEqual(mission['status'],'EXECUTING');self.assertIsNone(mission['audio_base64'])
            self.assertEqual(persistent.get(mission['id'])['revision'],0)
            with patch('app.speech.loop.synthesize',return_value=audio()):
                replay=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data)
                self.assertEqual(replay.json()['id'],mission['id']);self.assertEqual(stt.call_count,1)
            data['persistent_mission']='false'
            self.assertEqual(self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data).status_code,422)

    def test_v2_voice_requires_authorization_and_speech_config(self):
        with patch('app.speech.loop.transcribe') as stt:
            data={'request_key':'blocked','mode':'speech_test','persistent_mission':'true'}
            self.assertEqual(self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data).status_code,403)
            data['authorized']='true'
            with patch.dict(os.environ,GNANI_API_KEY=''):
                self.assertEqual(self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data=data).status_code,503)
            stt.assert_not_called()

    def test_legacy_voice_fingerprint_remains_compatible(self):
        fingerprint=hashlib.sha256(audio()+b'en-INspeech_testTrue').hexdigest()
        with closing(sqlite3.connect(os.environ['DRIVEOS_VOICE_DB'])) as db,db:
            db.execute('CREATE TABLE voice_requests (key TEXT PRIMARY KEY, fingerprint TEXT, transcript TEXT)')
            db.execute('INSERT INTO voice_requests VALUES (?,?,?)',('old',fingerprint,'Tell Ananya I am 25 minutes late.'))
        with patch('app.speech.loop.transcribe') as stt,patch('app.speech.loop.synthesize',return_value=audio()):
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data={'request_key':'old','mode':'speech_test','authorized':'true'})
            self.assertEqual(response.status_code,200);self.assertEqual(response.json()['status'],'COMPLETED');stt.assert_not_called()

    def test_budget_visible_and_exhaustion_blocks_voice_before_network(self):
        from app.speech.gnani import synthesize
        with patch.dict(os.environ,DRIVEOS_API_MAX_REQUESTS='1'),patch('app.speech.gnani.httpx.post',return_value=httpx.Response(200,content=audio())) as network:
            synthesize('Synthetic response')
            budget=self.client.get('/health').json()['request_budget']
            self.assertEqual(budget,{'stage':'eval','maximum':1,'used':1,'remaining':0})
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data={'request_key':'capped','mode':'speech_test','authorized':'true','persistent_mission':'true'})
            self.assertEqual(response.status_code,429);self.assertEqual(network.call_count,1)

    def test_multilingual_constraints_and_unsupported_contexts(self):
        fixtures=json.loads(Path('app/evaluation/fixtures/voice_missions.json').read_text(encoding='utf-8'))
        for fixture in fixtures:
            with self.subTest(fixture=fixture['id']):
                plan=MockEvon().plan_mission(planning_input(fixture['text']))
                self.assertEqual(len(plan.tasks),4 if fixture['signature'] else 0)
                if fixture['signature']:
                    self.assertEqual(plan.tasks[-1].arguments.max_detour_minutes,5)
                    self.assertEqual(plan.tasks[0].arguments.proposed_time,'16:30')
        self.assertEqual(normalize('  ಅನನ್ಯ  4:30\n ಐದು  '),'ಅನನ್ಯ 4:30 ಐದು')

    def test_v2_live_planner_failure_never_substitutes_mock(self):
        from app.speech.gnani import ProviderError
        with patch.dict(os.environ,EVON_MODE='remote',EVON_BASE_URL='http://localhost:9999/v1',EVON_MODEL='evon'),patch('app.speech.loop.transcribe',return_value='mission'),patch('app.agent.planner.evon.EvonClient.plan_mission',side_effect=ProviderError('Evon unavailable')):
            response=self.client.post('/voice/missions',files={'audio':('test.wav',audio(),'audio/wav')},data={'request_key':'live','authorized':'true','mode':'live','persistent_mission':'true'})
            self.assertEqual(response.status_code,502)
            self.assertIn('Evon unavailable',response.text)
