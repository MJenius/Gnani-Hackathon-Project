"""Two-process API persistence check. Restart API between capture and verify."""
import argparse
import json
from pathlib import Path
from uuid import uuid4
import httpx
from app.evaluation.runners.mission_demo import GOAL

def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['capture','verify']);args=parser.parse_args()
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

if __name__=='__main__': main()
