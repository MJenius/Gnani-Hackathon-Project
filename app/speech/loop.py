import hashlib
import os
import sqlite3
from pathlib import Path
from contextlib import closing
from app.speech.gnani import transcribe, synthesize
from app.speech.usage import BudgetExceeded
from app.speech.gnani import ProviderError
from app.mission.execution.engine import execute

def run(audio, language, request_key, authorized, mode):
    path=Path(os.getenv('DRIVEOS_VOICE_DB','data/voice-requests.sqlite3'))
    path.parent.mkdir(parents=True,exist_ok=True)
    fingerprint=hashlib.sha256(audio+language.encode()+mode.encode()+str(authorized).encode()).hexdigest()
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
            transcript=transcribe(audio,language)
            db.execute('INSERT INTO voice_requests VALUES (?,?,?)',(request_key,fingerprint,transcript))
    mission=execute({'transcript':transcript,'request_key':'voice:'+request_key,'authorized':authorized,'mode':mode})
    try:
        output=synthesize(mission['spoken_response'],'en-IN')
        return mission,output,None
    except (ProviderError,BudgetExceeded) as error:
        return mission,None,str(error)
