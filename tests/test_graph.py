import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from app.agent.planner.contract import MissionPlan
from app.agent.planner.evon import MockEvon, EvonClient, mission_planner
from app.mission.execution.engine import execute
from app.speech.gnani import ProviderError

CASES=json.loads(Path('app/evaluation/fixtures/mission_plans.json').read_text(encoding='utf-8'))

class GraphTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=self.temp.name+'/missions.sqlite3'
        self.env=patch.dict(os.environ,DRIVEOS_DB=self.db,EVON_MODE='mock');self.env.start()
        self.request={'transcript':CASES[-1]['input']['mission'],'request_key':'graph','authorized':True,'mode':'simulation',
                      'scenario':{'contact_response':'accepted','parking_full':False,'max_detour_minutes':5}}
    def tearDown(self):
        self.env.stop();self.temp.cleanup()
    def effects(self,action=None):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute('SELECT action FROM tool_effects'+(' WHERE action=?' if action else ''),(action,) if action else ()).fetchall()
    def test_signature_and_replay(self):
        with patch('httpx.post') as network:
            result=execute(self.request)
            self.assertEqual(result['status'],'COMPLETED')
            self.assertEqual(execute(self.request),result)
            network.assert_not_called()
        self.assertEqual(len(self.effects()),4)
        tasks={task['tool']:task for task in result['tasks']}
        self.assertEqual(tasks['calendar.reschedule']['dependencies'],['t1'])
        self.assertEqual(tasks['fuel.select']['output']['total_detour_minutes'],4)
    def test_rejected_and_no_answer_never_change_calendar(self):
        for reply in ['rejected','no_answer']:
            request=dict(self.request,request_key=reply,scenario=dict(self.request['scenario'],contact_response=reply))
            result=execute(request)
            self.assertEqual(result['status'],'ESCALATED')
            calendar=next(task for task in result['tasks'] if task['tool']=='calendar.reschedule')
            self.assertEqual(calendar['status'],'BLOCKED')
            self.assertEqual(self.effects('calendar.reschedule'),[])
    def test_full_lot_replans_and_shared_detour_skips_fuel(self):
        request=dict(self.request,scenario=dict(self.request['scenario'],parking_full=True,max_detour_minutes=3))
        result=execute(request)
        self.assertIn('REPLANNING',[event['status'] for event in result['events']])
        tasks={task['tool']:task for task in result['tasks']}
        self.assertEqual(tasks['parking.select']['output']['id'],'p2')
        self.assertEqual(tasks['fuel.select']['status'],'SKIPPED')
        self.assertEqual(self.effects('fuel.select'),[])
    def test_unauthorized_and_failure_roll_back(self):
        with self.assertRaises(PermissionError): execute(dict(self.request,authorized=False))
        from app.tools.simulated import perform
        def partially_fail(db,mission_id,task,scenario,completed):
            if task.action=='parking.select': raise RuntimeError('tool failure after contact mutation')
            return perform(db,mission_id,task,scenario,completed)
        with patch('app.mission.execution.graph.perform',side_effect=partially_fail):
            with self.assertRaises(RuntimeError): execute(self.request)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM missions').fetchone()[0],0)
        self.assertEqual(execute(self.request)['status'],'COMPLETED')
    def test_known_expected_plans_and_provider_contract(self):
        for case in CASES:
            plan=MockEvon().plan_mission(case['input'])
            nodes={task.id:task for task in plan.tasks}
            actual={task.action:{'arguments':task.arguments.model_dump(),'depends_on':sorted(nodes[key].action for key in task.depends_on)} for task in plan.tasks}
            self.assertEqual(actual,case['expected'])
            self.assertEqual(EvonClient(completion=lambda messages:plan.model_dump_json()).plan_mission(case['input']),plan)
    def test_invalid_graphs_fail_closed(self):
        plan=MockEvon().plan_mission(CASES[-1]['input']).model_dump()
        for mutation in ['cycle','missing_contact','fuel_dependency','unknown_tool','extra_argument']:
            value=json.loads(json.dumps(plan))
            if mutation=='cycle': value['tasks'][0]['depends_on']=['t2']
            elif mutation=='missing_contact': value['tasks'][1]['depends_on']=[]
            elif mutation=='fuel_dependency': value['tasks'][3]['depends_on']=[]
            elif mutation=='unknown_tool': value['tasks'][0]['action']='payment.purchase'
            else: value['tasks'][0]['arguments']['phone']='real number'
            with self.assertRaises(ValueError): MissionPlan.model_validate(value)
    def test_live_never_silently_uses_mock(self):
        with self.assertRaises(ProviderError): mission_planner('live')

if __name__=='__main__': unittest.main()
