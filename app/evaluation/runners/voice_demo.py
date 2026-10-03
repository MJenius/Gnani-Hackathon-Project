"""Explicit real Prisma/Timbre v2 verification using synthetic speech, existing credits."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from time import perf_counter, sleep
from unittest.mock import patch
from app.speech.gnani import synthesize
from app.speech.loop import run, mission_speech
from app.mission.execution import persistent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--real',action='store_true',help='Use configured Gnani credentials and existing speech credits; no retries')
    parser.add_argument('--case',choices=['english','kannada','hinglish'],required=True)
    parser.add_argument('--reuse-audio',action='store_true',help='Reuse saved synthetic input; Prisma and Timbre remain real')
    args=parser.parse_args()
    if not args.real: parser.error('Real provider calls require --real')
    fixtures=json.loads(Path('app/evaluation/fixtures/voice_missions.json').read_text(encoding='utf-8'))
    fixture=next(item for item in fixtures if item['id']==args.case)
    language={'english':'en-IN','kannada':'kn-IN','hinglish':'hi-IN'}[args.case]
    result={'case':args.case,'planner':'MockEvon','evon_used':False,'input_source':'synthetic Timbre speech, not microphone','success':False}
    started=perf_counter()
    try:
        audio_path=Path('data/voice-v2-'+args.case+'.wav')
        if args.reuse_audio: audio=audio_path.read_bytes()
        else:
            audio=synthesize(fixture['text'],language)
            audio_path.parent.mkdir(exist_ok=True);audio_path.write_bytes(audio)
            sleep(10)
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,DRIVEOS_DB=folder+'/mission.sqlite3',DRIVEOS_VOICE_DB=folder+'/voice.sqlite3'):
            loop_start=perf_counter()
            mission,output,error=run(audio,language,'real-v2-'+args.case,True,'speech_test',True,'parking-change')
            result['transcript']=mission['transcript']
            result['initial_audio_returned']=bool(output)
            if error: result['speech_error']=error
            for index in range(40):
                if mission['status']!='EXECUTING': break
                mission=persistent.command(mission['id'],'advance',{'request_key':str(index),'expected_revision':mission['revision']})
            sleep(10)
            final_audio=mission_speech(mission['id'],mission['revision'])
            result.update(success=mission['status']=='COMPLETED' and bool(final_audio),status=mission['status'],
                parking=mission['route']['parking'],added_minutes=mission['eta']['added_minutes'],
                loop_latency_ms=round((perf_counter()-loop_start)*1000),latency_includes_tts_cooldown=True)
    except (RuntimeError,ValueError) as error:
        result['error']=str(error)
    result['total_latency_ms']=round((perf_counter()-started)*1000)
    path=Path('data/voice-v2-'+args.case+'.json');path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='transcript'},indent=2))
    if not result['success']: raise SystemExit(1)

if __name__=='__main__': main()
