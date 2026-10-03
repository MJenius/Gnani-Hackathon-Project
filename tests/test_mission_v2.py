import json
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.main import app
from app.agent.planner.contract import MissionPlan,planning_input
from app.agent.planner.evon import MockEvon
from app.mission.execution import persistent

GOAL="I'm running late for my meeting. Tell Ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes."

class MissionV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=self.temp.name+'/state.sqlite3'
        self.env=patch.dict(os.environ,DRIVEOS_DB=self.db);self.env.start()
        self.client=TestClient(app);self.counter=0
    def tearDown(self):
        self.client.close();self.env.stop();self.temp.cleanup()
    def start(self,**extra):
        request={'transcript':GOAL,'request_key':'start','authorized':True,**extra}
        response=self.client.post('/missions/start',json=request)
        self.assertEqual(response.status_code,200,response.text);return response.json()
    def act(self,mission,op='advance',**extra):
        self.counter+=1
        body={'request_key':'cmd'+str(self.counter),'expected_revision':mission['revision'],**extra}
        method=self.client.patch if op in {'world','requirements'} else self.client.post
        response=method('/missions/'+mission['id']+'/'+op,json=body)
        self.assertEqual(response.status_code,200,response.text);return response.json()
    def finish(self,mission):
        for _ in range(30):
            if mission['status']!='EXECUTING': return mission
            mission=self.act(mission)
        self.fail('Execution did not terminate within the bound')
    def effects(self,mission,action):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute('SELECT payload FROM mission_effects WHERE mission_id=? AND action=?',(mission['id'],action)).fetchall()
    def test_normal_mission(self):
        with patch('httpx.post') as network:
            mission=self.finish(self.start());network.assert_not_called()
        self.assertEqual(mission['status'],'COMPLETED')
        self.assertEqual(mission['world']['calendar']['time'],'16:30')
        self.assertEqual(mission['eta']['added_minutes'],4)
        self.assertEqual(len(self.effects(mission,'contact.notify_delay')),1)
    def test_parking_changes_during_execution_demo(self):
        start=self.start(demo='parking-change');mission=self.finish(start)
        self.assertEqual(start['world']['parking'][0]['available'],True)
        self.assertEqual(mission['id'],start['id'])
        self.assertTrue(mission['demo_event_fired'])
        self.assertEqual(mission['route']['parking']['id'],'p2')
        self.assertEqual(mission['eta']['added_minutes'],5)
        self.assertTrue(any(event['status']=='REPLANNING' for event in mission['events']))
        task=next(task for task in mission['tasks'] if task['tool']=='parking.select')
        self.assertTrue(any(item['to']=='REPLANNING' for item in task['history']))
    def test_rejected_time_replans_and_confirmation_gates_calendar(self):
        mission=self.act(self.start(),'world',changes={'contact_response':'rejected'})
        mission=self.finish(mission)
        self.assertEqual(mission['status'],'AWAITING_CONFIRMATION')
        self.assertEqual(mission['world']['calendar']['time'],'16:00')
        self.assertEqual(self.effects(mission,'calendar.reschedule'),[])
        pending=mission['confirmation'];self.assertEqual(pending['arguments']['time'],'16:45')
        mission=self.act(mission,'confirm',confirmation_id=pending['id'],approved=True)
        mission=self.finish(mission)
        self.assertEqual(mission['world']['calendar']['time'],'16:45')
        self.assertEqual(len(self.effects(mission,'calendar.reschedule')),1)
    def test_fuel_detour_changes_before_verification(self):
        mission=self.start()
        for _ in range(15):
            fuel=next(task for task in mission['tasks'] if task['tool']=='fuel.select')
            if fuel['candidate']: break
            mission=self.act(mission)
        self.assertEqual(fuel['status'],'EXECUTING')
        mission=self.act(mission,'world',changes={'fuel_detour_minutes':8})
        mission=self.finish(mission)
        self.assertIsNone(mission['route']['fuel'])
        self.assertLessEqual(mission['eta']['added_minutes'],5)
        self.assertEqual(self.effects(mission,'fuel.select'),[])
    def test_combined_failures_and_no_answer_are_bounded(self):
        mission=self.act(self.start(demo='parking-change'),'world',changes={'contact_response':'no_answer','fuel_detour_minutes':8})
        mission=self.finish(mission)
        self.assertEqual(mission['status'],'ESCALATED')
        self.assertEqual(mission['route']['parking']['id'],'p2')
        self.assertIsNone(mission['route']['fuel'])
        self.assertEqual(len(self.effects(mission,'contact.call')),2)
        self.assertEqual(len(self.effects(mission,'contact.notify_delay')),0)
        self.assertEqual(len(self.effects(mission,'contact.delay_queued')),1)
        self.assertEqual(self.effects(mission,'calendar.reschedule'),[])
    def test_user_change_keeps_completed_calendar_and_mission_id(self):
        mission=self.start()
        while not self.effects(mission,'calendar.reschedule'): mission=self.act(mission)
        old_id=mission['id'];old_contact=next(task for task in mission['tasks'] if task['tool']=='contact.negotiate')
        mission=self.act(mission,'requirements',changes={'include_fuel':False,'max_detour_minutes':3})
        mission=self.finish(mission)
        self.assertEqual(mission['id'],old_id)
        self.assertIsNone(mission['route']['fuel'])
        self.assertLessEqual(mission['eta']['added_minutes'],3)
        self.assertEqual(next(task for task in mission['tasks'] if task['tool']=='contact.negotiate')['history'],old_contact['history'])
        self.assertEqual(len(self.effects(mission,'contact.notify_delay')),1)
        self.assertEqual(len(self.effects(mission,'calendar.reschedule')),1)
    def test_state_survives_reads_and_completed_route_can_replan(self):
        mission=self.finish(self.start())
        self.assertEqual(self.client.get('/missions/'+mission['id']).json(),mission)
        mission=self.act(mission,'world',changes={'parking_full':True})
        resumed=self.client.get('/missions/'+mission['id']).json()
        mission=self.finish(resumed)
        self.assertEqual(mission['route']['parking']['id'],'p2')
        self.assertEqual(len(self.effects(mission,'calendar.reschedule')),1)
    def test_duplicate_and_concurrent_commands_do_not_duplicate_actions(self):
        mission=self.start()
        body={'request_key':'same','expected_revision':mission['revision']}
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:persistent.command(mission['id'],'advance',body),range(4)))
        self.assertEqual({result['revision'] for result in results},{1})
        self.assertEqual(len(self.effects(mission,'contact.notify_delay')),0)
        self.assertEqual(len(self.effects(mission,'contact.delay_queued')),1)
        self.assertEqual(len(self.effects(mission,'contact.call')),1)
        self.assertEqual(self.client.post('/missions/'+mission['id']+'/advance',json=dict(body,request_key='stale')).status_code,409)
        self.assertEqual(self.client.post('/missions/start',json={'transcript':GOAL,'request_key':'start','authorized':True}).json()['id'],mission['id'])
    def test_stale_confirmation_and_denial(self):
        mission=self.finish(self.act(self.start(),'world',changes={'contact_response':'rejected'}))
        old=mission['confirmation']['id']
        mission=self.act(mission,'requirements',changes={'max_detour_minutes':3})
        body={'request_key':'stale-confirm','expected_revision':mission['revision'],'confirmation_id':old,'approved':True}
        self.assertEqual(self.client.post('/missions/'+mission['id']+'/confirm',json=body).status_code,409)
        mission=self.act(mission,'confirm',confirmation_id=mission['confirmation']['id'],approved=False)
        mission=self.finish(mission)
        self.assertEqual(self.effects(mission,'calendar.reschedule'),[])
        self.assertEqual(mission['status'],'ESCALATED')
    def test_plan_confirmation_and_unknown_sensitive_action(self):
        plan=MockEvon().plan_mission(planning_input(GOAL)).model_dump();plan['needs_confirmation']=True
        mission=self.start(plan=plan)
        self.assertEqual(mission['status'],'AWAITING_CONFIRMATION')
        mission=self.act(mission)
        self.assertEqual(self.effects(mission,'contact.notify_delay'),[])
        mission=self.act(mission,'confirm',confirmation_id=mission['confirmation']['id'],approved=True)
        self.assertEqual(self.finish(mission)['status'],'COMPLETED')
        plan['tasks'][0]['action']='payment.purchase'
        self.assertEqual(self.client.post('/missions/start',json={'transcript':GOAL,'request_key':'danger','authorized':True,'plan':plan}).status_code,422)
    def test_invalid_mutations_and_unauthorized_start(self):
        self.assertEqual(self.client.post('/missions/start',json={'transcript':GOAL,'request_key':'unauth'}).status_code,403)
        mission=self.start()
        for changes in [{'max_detour_minutes':6},{'include_fuel':None},{}]:
            response=self.client.patch('/missions/'+mission['id']+'/requirements',json={'request_key':'bad','expected_revision':mission['revision'],'changes':changes})
            self.assertEqual(response.status_code,422)
    def test_failed_transition_preserves_committed_call_and_can_resume(self):
        mission=self.act(self.start())
        with patch('app.mission.execution.persistent.services.contact',side_effect=RuntimeError('synthetic service failure')):
            with self.assertRaises(RuntimeError):
                persistent.command(mission['id'],'advance',{'request_key':'failing','expected_revision':mission['revision']})
        restored=persistent.get(mission['id'])
        self.assertEqual(restored,mission)
        self.assertEqual(self.finish(restored)['status'],'COMPLETED')
        self.assertEqual(len(self.effects(mission,'contact.call')),1)
    def test_maps_recalculate_and_withdrawn_agreement_invalidates_confirmation(self):
        mission=self.finish(self.act(self.start(),'world',changes={'contact_response':'rejected'}))
        old=mission['confirmation']['id']
        mission=self.act(mission,'world',changes={'contact_response':'accepted','base_travel_minutes':28})
        self.assertIsNone(mission['confirmation'])
        mission=self.finish(mission)
        self.assertEqual(mission['world']['calendar']['time'],'16:30')
        self.assertEqual(mission['eta']['arrival'],'16:32')
        self.assertEqual(mission['status'],'ESCALATED')
        self.assertNotIn(old,mission['approved_confirmations'])
    def test_command_key_collision_rejected(self):
        mission=self.start()
        body={'request_key':'fixed','expected_revision':mission['revision']}
        mission=persistent.command(mission['id'],'advance',body)
        with self.assertRaises(ValueError):
            persistent.command(mission['id'],'world',{**body,'changes':{'parking_full':True}})

    def test_repeated_conditions_and_requirements_are_noops(self):
        mission=self.finish(self.start(demo='parking-change'))
        generations=[task['generation'] for task in mission['tasks']]
        world_version=mission['world']['version'];requirements_version=mission['requirements_version']
        mission=self.act(mission,'world',changes={'parking_full':True})
        mission=self.act(mission,'requirements',changes={'max_detour_minutes':5,'include_fuel':True})
        self.assertEqual(mission['status'],'COMPLETED')
        self.assertEqual([task['generation'] for task in mission['tasks']],generations)
        self.assertEqual(mission['world']['version'],world_version)
        self.assertEqual(mission['requirements_version'],requirements_version)
        self.assertEqual(len(self.effects(mission,'parking.select')),1)

    def test_frozen_contract_unchanged(self):
        from pathlib import Path
        self.assertEqual(MissionPlan.model_json_schema(),json.loads(Path('docs/evon-plan-v1.schema.json').read_text()))

if __name__=='__main__': unittest.main()
