"""Offline deterministic v2 demo: normal start, garage fills, autonomous replan."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from app.mission.execution.persistent import start,command

GOAL="I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes."

def main():
    with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,DRIVEOS_DB=folder+'/demo.sqlite3'):
        mission=start({'transcript':GOAL,'request_key':'deterministic-demo','authorized':True,'demo':'parking-change'})
        initial_id=mission['id'];initial_available=mission['world']['parking'][0]['available']
        for index in range(30):
            if mission['status']!='EXECUTING': break
            mission=command(initial_id,'advance',{'request_key':'step-'+str(index),'expected_revision':mission['revision']})
        assert initial_available and mission['demo_event_fired'] and mission['id']==initial_id
        assert mission['status']=='COMPLETED' and mission['route']['parking']['id']=='p2'
        assert mission['eta']['added_minutes']<=5
    output=Path('data/mission-v2-demo.json');output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(mission,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':mission['status'],'same_mission':mission['id']==initial_id,
                      'external_change_after_start':mission['demo_event_fired'],
                      'parking':mission['route']['parking']['name'],'eta':mission['eta'],
                      'replans':[event['message'] for event in mission['events'] if event['status']=='REPLANNING']},indent=2))

if __name__=='__main__': main()
