"""Two-process API persistence check. Restart API between capture and verify."""
import argparse
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path
from uuid import uuid4
import httpx
from app.evaluation.runners.mission_demo import GOAL

def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['capture','verify','auto']);args=parser.parse_args()
    if args.phase=='auto': return automatic()
    path=Path('data/restart-check.json');path.parent.mkdir(exist_ok=True)
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=10) as client:
        def advance(mission):
            response=client.post('/missions/'+mission['id']+'/advance',json={'request_key':str(uuid4()),'expected_revision':mission['revision']});response.raise_for_status();return response.json()
        if args.phase=='capture':
            response=client.post('/missions/start',json={'transcript':GOAL,'request_key':str(uuid4()),'authorized':True,'demo':'parking-change'});response.raise_for_status();mission=response.json()
            for _ in range(5): mission=advance(mission)
            path.write_text(json.dumps(mission),encoding='utf-8');print('Captured executing mission for API restart.')
        else:
            saved=json.loads(path.read_text(encoding='utf-8'));response=client.get('/missions/'+saved['id']);response.raise_for_status();mission=response.json();assert mission==saved
            for _ in range(40):
                if mission['status']!='EXECUTING': break
                mission=advance(mission)
            assert mission['status']=='COMPLETED' and mission['id']==saved['id'] and mission['route']['parking']['id']=='p2'
            print('API restart preserved exact state; resumed same mission to completion.')

def automatic():
    """Start, stop and restart a real API process against an isolated database."""
    with tempfile.TemporaryDirectory() as folder:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env={**os.environ,'DRIVEOS_DB':folder+'/restart.sqlite3'}
        saved=None
        for phase in ['capture','verify']:
            process=subprocess.Popen([sys.executable,'-m','uvicorn','app.api.main:app','--host','127.0.0.1','--port',str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=5) as client:
                    for _ in range(100):
                        if process.poll() is not None: raise RuntimeError('Restart-check API exited before startup')
                        try:
                            if client.get('/health').status_code==200: break
                        except httpx.HTTPError: pass
                        time.sleep(.1)
                    else: raise RuntimeError('Restart-check API did not start')
                    def advance(mission):
                        response=client.post('/missions/'+mission['id']+'/advance',json={'request_key':str(uuid4()),'expected_revision':mission['revision']})
                        response.raise_for_status();return response.json()
                    if phase=='capture':
                        response=client.post('/missions/start',json={'transcript':GOAL,'request_key':'restart','authorized':True,'demo':'parking-change'})
                        response.raise_for_status();saved=response.json()
                        for _ in range(5): saved=advance(saved)
                    else:
                        response=client.get('/missions/'+saved['id']);response.raise_for_status();mission=response.json()
                        assert mission==saved,'Restart changed committed state'
                        for _ in range(40):
                            if mission['status']!='EXECUTING': break
                            mission=advance(mission)
                        assert mission['id']==saved['id'] and mission['status']=='COMPLETED' and mission['route']['parking']['id']=='p2'
                        with closing(sqlite3.connect(env['DRIVEOS_DB'])) as db:
                            effects=dict(db.execute('SELECT action,COUNT(*) FROM mission_effects GROUP BY action'))
                        assert effects['contact.call']==effects['contact.notify_delay']==effects['calendar.reschedule']==1
            finally:
                process.terminate();process.wait(timeout=10)
        result={'status':'passed','api_processes':2,'exact_state_restored':True,'same_mission_id':True,
                'resumed_status':mission['status'],'effect_counts':effects,'providers_called':False}
        output=Path('data/restart-results.json');output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__': main()
