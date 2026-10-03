import hashlib
import os
import sqlite3
from pathlib import Path
from contextlib import closing
from app.speech.gnani import transcribe, synthesize
from app.speech.usage import BudgetExceeded
from app.speech.gnani import ProviderError
from app.mission.execution.engine import execute
from app.mission.execution import persistent
from app.speech.normalize import normalize

def run(audio, language, request_key, authorized, mode, persistent_mission=False, demo='none'):
    path=Path(os.getenv('DRIVEOS_VOICE_DB','data/voice-requests.sqlite3'))
    path.parent.mkdir(parents=True,exist_ok=True)
    engine_identity=(str(persistent_mission)+demo).encode() if persistent_mission or demo!='none' else b''
    fingerprint=hashlib.sha256(audio+language.encode()+mode.encode()+str(authorized).encode()+engine_identity).hexdigest()
    # ponytail: one local transaction spans STT; use per-request jobs if concurrency grows.
    with closing(sqlite3.connect(path,timeout=60)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS voice_requests (key TEXT PRIMARY KEY, fingerprint TEXT, transcript TEXT)')
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT fingerprint,transcript FROM voice_requests WHERE key=?',(request_key,)).fetchone()
        if old:
            if old[0]!=fingerprint:
                raise ValueError('Voice request key already belongs to another recording or mode')
            transcript=old[1]
        else:
            transcript=normalize(transcribe(audio,language))
            db.execute('INSERT INTO voice_requests VALUES (?,?,?)',(request_key,fingerprint,transcript))
    request={'transcript':transcript,'request_key':'voice:'+request_key,'authorized':authorized,'mode':mode}
    mission=persistent.start({**request,'demo':demo}) if persistent_mission else execute(request)
    try:
        if persistent_mission:
            initial='Mission started. I will handle the simulated meeting and route.' if mission['tasks'] else mission['spoken_response']
            if mission['status']=='AWAITING_CONFIRMATION': initial='Please review the proposed mission plan. No action has run.'
            output=cached_speech(mission['id'],-1,initial)
        else: output=synthesize(mission['spoken_response'],'en-IN')
        return mission,output,None
    except (ProviderError,BudgetExceeded) as error:
        return mission,None,str(error)

def mission_speech(mission_id, revision):
    mission=persistent.get(mission_id)
    if mission['revision']!=revision: raise ValueError('Mission changed; refresh before requesting speech')
    if mission['mode'] not in {'speech_test','live'}: raise ValueError('Real speech requires a Gnani voice mission')
    if mission['status'] not in {'COMPLETED','ESCALATED','AWAITING_CONFIRMATION'}:
        raise ValueError('No mission summary or confirmation is ready')
    text=mission['confirmation']['label'] if mission['status']=='AWAITING_CONFIRMATION' else mission['spoken_response']
    return cached_speech(mission_id,revision,text)

def cached_speech(mission_id,revision,text):
    path=Path(os.getenv('DRIVEOS_VOICE_DB','data/voice-requests.sqlite3'))
    path.parent.mkdir(parents=True,exist_ok=True)
    # Cache by exact mission revision; playback retries never spend more credits.
    with closing(sqlite3.connect(path,timeout=60)) as db,db:
        db.execute('CREATE TABLE IF NOT EXISTS mission_speech (id TEXT, revision INTEGER, audio BLOB, PRIMARY KEY(id,revision))')
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT audio FROM mission_speech WHERE id=? AND revision=?',(mission_id,revision)).fetchone()
        if old: return old[0]
        output=synthesize(text,'en-IN')
        db.execute('INSERT INTO mission_speech VALUES (?,?,?)',(mission_id,revision,output))
        return output
