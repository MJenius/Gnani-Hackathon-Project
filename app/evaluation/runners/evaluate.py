import os
import tempfile
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from time import perf_counter
from statistics import median
from unittest.mock import patch
from app.mission.execution.engine import execute
from app.mission.execution import persistent
from app.agent.planner.contract import MissionPlan

def main():
    cases = [('Tell Ananya I am 25 minutes late.', 'COMPLETED'),
             ('Tell Ananya I am 0 minutes late.', 'ESCALATED'),
             ('Buy petrol for me', 'ESCALATED')]
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, DRIVEOS_DB=directory+'/eval.sqlite3'):
        passed = sum(execute({'transcript': text, 'request_key': str(index), 'authorized': True})['status'] == expected
                     for index, (text, expected) in enumerate(cases))
    print(f'Deterministic text slice: {passed}/{len(cases)} expected outcomes')
    if passed != len(cases): raise SystemExit(1)
    evaluate_missions()

def evaluate_missions():
    fixtures=json.loads(Path('app/evaluation/fixtures/voice_missions.json').read_text(encoding='utf-8'))
    results=[]
    with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,DRIVEOS_DB=folder+'/evaluation.sqlite3'),patch('httpx.post') as network:
        cases=[(item,{},'none') for item in fixtures]
        cases += [(fixtures[0],{},'parking-change'),(fixtures[0],{'contact_response':'no_answer'},'none'),(fixtures[0],{'contact_response':'rejected'},'none')]
        for index,(fixture,scenario,demo) in enumerate(cases):
            started=perf_counter()
            mission=persistent.start({'transcript':fixture['text'],'request_key':str(index),'authorized':True,'scenario':scenario,'demo':demo})
            MissionPlan.model_validate(mission['plan'])
            for step in range(40):
                if mission['status']!='EXECUTING': break
                request={'request_key':str(step),'expected_revision':mission['revision']}
                mission=persistent.command(mission['id'],'advance',request)
                assert persistent.command(mission['id'],'advance',request)==mission
            nodes={node['id']:node for node in mission['tasks']}
            dependencies=all(all(nodes[key]['status']=='COMPLETED' for key in node['dependencies']) for node in mission['tasks'] if node['status']=='COMPLETED')
            with closing(sqlite3.connect(os.environ['DRIVEOS_DB'])) as db:
                effects=db.execute('SELECT action,payload FROM mission_effects WHERE mission_id=?',(mission['id'],)).fetchall()
            notifications=sum(action=='contact.notify_delay' for action,_ in effects)
            expected='ESCALATED' if not fixture['signature'] or scenario.get('contact_response')=='no_answer' else 'AWAITING_CONFIRMATION' if scenario.get('contact_response')=='rejected' else 'COMPLETED'
            results.append({'case':fixture['id'],'scenario':scenario,'demo':demo,'status':mission['status'],
                'expected_outcome':mission['status']==expected,'mission_completed':mission['status']=='COMPLETED','schema_valid':True,
                'dependencies_correct':dependencies,'intent_preserved':len(mission['tasks'])==(4 if fixture['signature'] else 0),
                'replanning_success':mission['route']['parking']['id']=='p2' if demo=='parking-change' else None,
                'duplicate_effects':max(0,notifications-1),'confirmation_compliant':not scenario or mission['world']['calendar']['time']=='16:00',
                'unsafe_actions':sum(action not in {'contact.delay_queued','contact.call','contact.notify_delay','calendar.reschedule','parking.select','fuel.select'} for action,_ in effects),
                'no_answer_bounded':mission['tasks'][0]['attempts']==2 if scenario.get('contact_response')=='no_answer' else None,
                'ground_truth_verified':all(node['output'].get('available',False) for node in mission['tasks'] if node['tool'] in {'parking.select','fuel.select'} and node['status']=='COMPLETED') if any(node['tool'] in {'parking.select','fuel.select'} and node['status']=='COMPLETED' for node in mission['tasks']) else None,
                'latency_ms':round((perf_counter()-started)*1000,2),'user_interventions':int(mission['status'] in {'AWAITING_CONFIRMATION','ESCALATED'})})
        network.assert_not_called()
    metrics={key:sum(bool(item[key]) for item in results)/len(results) for key in ['expected_outcome','schema_valid','dependencies_correct','intent_preserved','confirmation_compliant']}
    verified=[item for item in results if item['ground_truth_verified'] is not None]
    metrics['ground_truth_verification_success']=sum(item['ground_truth_verified'] for item in verified)/len(verified)
    supported=[item for item in results if item['case'] in {f['id'] for f in fixtures if f['signature']} and not item['scenario']]
    metrics.update(mission_completion_rate=sum(item['mission_completed'] for item in supported)/len(supported),
        replanning_success=all(item['replanning_success'] for item in results if item['replanning_success'] is not None),
        no_answer_handling=all(item['no_answer_bounded'] for item in results if item['no_answer_bounded'] is not None),
        duplicate_execution_rate=sum(item['duplicate_effects'] for item in results)/len(results),
        unsafe_action_rate=sum(item['unsafe_actions'] for item in results)/len(results),
        median_latency_ms=median(item['latency_ms'] for item in results),user_interventions=sum(item['user_interventions'] for item in results))
    multilingual={language: {'passed':sum(item['expected_outcome'] for item in results if item['case']==language),
                             'tested':sum(item['case']==language for item in results)} for language in ['english','kannada','hinglish']}
    output={'planner':'DriveOS Mission Interpreter (MockEvon; deterministic, no inference)',
            'providers_called':False,'human_microphone_validation':{'status':'not_verified','scope':'No measured human end-to-end completion/playback gate in this offline runner'},
            'multilingual_fixture_validity':multilingual,
            'latency_scope':'local text → persisted mission; excludes STT/TTS and browser pacing','metrics':metrics,'cases':results}
    path=Path('data/evaluation-results.json');path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(metrics,indent=2))
    assert all(item['expected_outcome'] and item['dependencies_correct'] and item['confirmation_compliant'] and item['intent_preserved'] and not item['duplicate_effects'] and not item['unsafe_actions'] for item in results)

if __name__ == '__main__': main()
