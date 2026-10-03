"""Explicit paid verification; never invoked by the offline tests or application startup."""
import argparse
import json
import hashlib
import os
import re
import tempfile
from unittest.mock import patch
from pathlib import Path
from time import perf_counter, sleep
from app.speech.gnani import synthesize, transcribe, wav_info
from app.agent.planner.evon import EvonClient
from app.speech.loop import run as run_voice

CASES = [
    ('english', 'en-IN', 'en-IN', 'Your mission is ready.'),
    ('kannada', 'kn-IN', 'kn-IN', 'ನಿಮ್ಮ ಪ್ರಯಾಣದ ಯೋಜನೆ ಸಿದ್ಧವಾಗಿದೆ.'),
    ('mixed', 'auto', 'kn-IN', 'ಅನನ್ಯ ಅವರಿಗೆ ಹೇಳಿ, I am twenty five minutes late.'),
    ('numbers-time', 'en-IN', 'en-IN', 'Tell Ananya I am twenty five minutes late. The meeting is at four thirty in the afternoon.'),
    ('dates', 'en-IN', 'en-IN', 'The meeting is on the third of October twenty twenty six.'),
    ('hinglish', 'auto', 'hi-IN', 'Ananya ko batao, I am twenty five minutes late.'),
]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--speech', action='store_true', help='Spend up to ten speech requests on synthetic fixtures')
    parser.add_argument('--evon', action='store_true', help='Spend two configured Evon requests (English and Kannada)')
    parser.add_argument('--case', choices=[item[0] for item in CASES], help='Run just one speech case')
    parser.add_argument('--loop', action='store_true', help='Three paid calls for a synthetic real-speech/tool loop, without Evon')
    parser.add_argument('--save-fixtures',action='store_true',help='Save synthetic speech audio and transcript locally after an explicitly requested paid test')
    parser.add_argument('--reuse-fixtures',action='store_true',help='Offline replay of cached fixtures; missing fixtures fail without paid calls')
    args=parser.parse_args()
    if args.reuse_fixtures and (args.loop or args.evon or args.save_fixtures): parser.error('Offline fixture replay cannot be combined with other provider tests')
    if not (args.speech or args.evon or args.loop): parser.error('Choose --speech, --evon and/or --loop explicitly')
    results=[]
    if args.loop:
        try:
            audio=synthesize('Tell Ananya I am twenty five minutes late.','en-IN')
            # Avoid back-to-back fixture and response synthesis; observed provider throttles bursts.
            sleep(10)
            with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,
                    DRIVEOS_DB=directory+'/mission.sqlite3',DRIVEOS_VOICE_DB=directory+'/voice.sqlite3'):
                start=perf_counter()
                mission,output,error=run_voice(audio,'en-IN','synthetic-loop',True,'speech_test')
                success=mission['status']=='COMPLETED' and bool(output)
                result={'operation':'speech-tool-loop','success':success,'planner':'deterministic-demo',
                        'evon_used':False,'latency_ms':round((perf_counter()-start)*1000),
                        'mission_status':mission['status'],'audio_returned':bool(output)}
                if error: result['speech_error']=error
                results.append(result)
        except (RuntimeError,ValueError) as error:
            results.append({'operation':'speech-tool-loop','success':False,'error':str(error)})
    if args.speech:
        for name,tts_language,stt_language,text in CASES:
            if args.case and name != args.case: continue
            operation='timbre'
            try:
                group=name if name in {'english','kannada','hinglish'} else 'english' if name in {'dates','numbers-time'} else 'kannada'
                folder=Path('test_audio')/group
                audio_path=folder/(name+'.wav'); cache_path=folder/(name+'.cached.json')
                prompt_hash=hashlib.sha256(text.encode()).hexdigest()
                if args.reuse_fixtures:
                    audio=audio_path.read_bytes(); cache=json.loads(cache_path.read_text(encoding='utf-8'))
                    if cache['prompt_sha256']!=prompt_hash or cache['audio_sha256']!=hashlib.sha256(audio).hexdigest():
                        raise ValueError('Fixture provenance mismatch; no paid retry')
                    results.append({'case':name,'operation':'cached-fixture','success':True,'provider_called':False,
                                    'historical_transcript_characters':len(cache['transcript']),**wav_info(audio)})
                    continue
                start=perf_counter(); audio=synthesize(text,tts_language)
                results.append({'case':name,'operation':operation,'success':True,
                                'latency_ms':round((perf_counter()-start)*1000),**wav_info(audio)})
                operation='prisma';start=perf_counter();heard=transcribe(audio,stt_language)
                if args.save_fixtures:
                    folder.mkdir(parents=True,exist_ok=True);audio_path.write_bytes(audio)
                    cache_path.write_text(json.dumps({'transcript':heard,'language':stt_language,'source':'synthetic Timbre → Prisma',
                        'prompt_sha256':prompt_hash,'audio_sha256':hashlib.sha256(audio).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
                results.append({'case':name,'operation':operation,'success':True,
                                'latency_ms':round((perf_counter()-start)*1000),
                                'transcript_characters':len(heard),
                                'kannada_script_present': bool(re.search('[\u0c80-\u0cff]',heard)),
                                'digits_present': bool(re.search(r'\d',heard)),
                                'contains_ananya': 'ananya' in heard.lower() or 'ಅನನ್ಯ' in heard,
                                'quality_verdict':'manual review required; API success is not transcription accuracy'})
            except (RuntimeError,ValueError,OSError) as error:
                results.append({'case':name,'operation':operation,'success':False,'error':str(error)})
                # Authentication, quota and transport errors should not burn the rest of the matrix.
                break
    if args.evon:
        if not os.getenv('EVON_BASE_URL') or not os.getenv('EVON_MODEL'):
            for language in ['en-IN','kn-IN']:
                results.append({'operation':'evon','language':language,'status':'blocked','reason':'No Evon deployment configured'})
        else:
            for language,text in [('en-IN','Tell Ananya I am 25 minutes late.'),
                                  ('kn-IN','ನಾನು ಇಪ್ಪತ್ತೈದು ನಿಮಿಷ ತಡವಾಗುತ್ತೇನೆ ಎಂದು ಅನನ್ಯ ಅವರಿಗೆ ತಿಳಿಸಿ.')]:
                try:
                    start=perf_counter(); result=EvonClient().plan(text)
                    results.append({'operation':'evon','language':language,'success':True,
                                    'latency_ms':round((perf_counter()-start)*1000), 'schema_valid':True,
                                    'correct_task':len(result.tasks)==1 and result.tasks[0].delay_minutes==25})
                except (RuntimeError,ValueError) as error:
                    results.append({'operation':'evon','language':language,'success':False,'error':str(error)})
                    break
    output=Path('data/gnani-smoke-results.json'); output.parent.mkdir(parents=True,exist_ok=True)
    previous=json.loads(output.read_text(encoding='utf-8')) if output.exists() else []
    output.write_text(json.dumps(previous+results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))
    if any(item.get('success') is False for item in results): raise SystemExit(1)

if __name__ == '__main__': main()
