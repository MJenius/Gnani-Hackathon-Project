"""Mission Engine v2: one durable transition per command, same mission through replans.

SQLite serializes local commands. The browser drives the demonstration clock; no
background worker is needed. Closing the console pauses progression, not persistence.
"""
import hashlib
import json
import os
import sqlite3
from contextlib import closing, contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from app.agent.planner.contract import MissionPlan, planning_input
from app.agent.planner.evon import mission_planner
from app.agent.policies.actions import validate, validate_calendar_change
from app.mission.execution.graph import LABELS
from app.tools import world as services

TERMINAL={'COMPLETED','SKIPPED','BLOCKED','CANCELLED','FAILED'}
STATES=TERMINAL|{'PLANNED','READY','EXECUTING','WAITING_ON_EXTERNAL','REPLANNING','AWAITING_CONFIRMATION'}

def now(): return datetime.now(timezone.utc).isoformat()
def display_time(value):
    hour,minute=map(int,value.split(':'));return f'{hour%12 or 12}:{minute:02} '+('PM' if hour>=12 else 'AM')
def encoded(value): return json.dumps(value,sort_keys=True,ensure_ascii=False)
def digest(value): return hashlib.sha256(encoded(value).encode()).hexdigest()

@contextmanager
def connection():
    path=Path(os.getenv('DRIVEOS_DB','data/driveos.sqlite3'));path.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path,timeout=10)) as db,db:
        db.execute('CREATE TABLE IF NOT EXISTS active_missions (id TEXT PRIMARY KEY, start_key TEXT UNIQUE, fingerprint TEXT, state TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS mission_commands (mission_id TEXT, key TEXT, fingerprint TEXT, PRIMARY KEY(mission_id,key))')
        db.execute('CREATE TABLE IF NOT EXISTS mission_effects (id TEXT PRIMARY KEY, mission_id TEXT, task_id TEXT, action TEXT, payload TEXT)')
        db.execute('BEGIN IMMEDIATE')
        yield db

def load(db,mission_id):
    row=db.execute('SELECT state FROM active_missions WHERE id=?',(mission_id,)).fetchone()
    if not row: raise LookupError('Mission not found')
    return json.loads(row[0])

def get(mission_id):
    with connection() as db: return load(db,mission_id)

def event(mission,status,message,task_id=None):
    mission['events'].append({'id':len(mission['events'])+1,'status':status,'message':message,
        'task_id':task_id,'timestamp':now(),'step':mission['step']})

def transition(mission,task,status,message,output=None):
    if status not in STATES: raise ValueError('Invalid task state')
    task['history'].append({'from':task['status'],'to':status,'message':message,'timestamp':now(),
                            'generation':task['generation'],'output':deepcopy(task.get('output'))})
    task['status']=status;task['updated_at']=now()
    if output is not None: task['output']=output
    event(mission,status,message,task['id'])

def effect(db,mission,task,token,action,payload):
    key=mission['id']+':'+token
    old=db.execute('SELECT payload FROM mission_effects WHERE id=?',(key,)).fetchone()
    if old:
        if old[0]!=encoded(payload): raise ValueError('Action identity conflict')
        return False
    db.execute('INSERT INTO mission_effects VALUES (?,?,?,?,?)',(key,mission['id'],task['id'],action,encoded(payload)))
    return True

def task_for(mission,action):
    return next((task for task in mission['tasks'] if task['tool']==action),None)

def reopen(mission,task,reason):
    if not task: return
    transition(mission,task,'REPLANNING',reason)
    task['generation']+=1;task['candidate']=None;task['output']=None
    transition(mission,task,'PLANNED','Revised task queued; completed action history retained')
    mission['terminal_announced']=False

def refresh_route(mission,reason=None):
    previous=mission.get('eta')
    mission['eta']=services.eta(mission['world'],mission['route'])
    if reason and previous!=mission['eta']:
        event(mission,'ETA_UPDATED',reason+': simulated arrival '+mission['eta']['arrival'])

def pending_confirmation(mission,task,action,arguments,label):
    proposal={'mission_id':mission['id'],'task_id':task['id'] if task else None,'action':action,
              'arguments':arguments,'requirements_version':mission['requirements_version'],
              'task_generation':task['generation'] if task else 0}
    bound={**proposal,'id':digest(proposal),'label':label}
    mission['confirmation']=bound
    return bound

def summary(mission):
    if not mission['tasks']: return 'This request is outside the supported demo fixtures. No external action was taken.'
    world=mission['world'];calendar=task_for(mission,'calendar.reschedule')
    text=['Synthetic mission complete.' if mission['status']=='COMPLETED' else 'Some mission tasks need your attention.']
    if calendar:
        text.append('Meeting moved to '+display_time(world['calendar']['time'])+'.' if calendar['status']=='COMPLETED' else 'Calendar was left unchanged.')
    for kind in ['parking','fuel']:
        task=task_for(mission,kind+'.select')
        if task:
            item=mission['route'][kind]
            text.append(item['name']+' selected.' if item else kind.title()+' omitted.')
    text.append('Simulated arrival '+display_time(mission['eta']['arrival'])+'; added route time '+str(mission['eta']['added_minutes'])+' minutes.')
    if calendar and calendar['status']=='COMPLETED' and mission['eta']['arrival']>world['calendar']['time']:
        text.append('Arrival is later than the agreed meeting time; another agreement is needed.')
    return ' '.join(text)

def update_view(mission):
    tasks=mission['tasks'];nodes={task['id']:task for task in tasks}
    if mission.get('plan_review'):
        mission['status']='AWAITING_CONFIRMATION';mission['current_action']='Review the proposed plan';return
    for task in tasks:
        if task['status']=='PLANNED' and all(nodes[key]['status'] in TERMINAL for key in task['dependencies']):
            if any(nodes[key]['status'] in {'BLOCKED','FAILED','CANCELLED'} for key in task['dependencies']):
                transition(mission,task,'BLOCKED','Required task did not succeed')
            else: transition(mission,task,'READY','Dependencies satisfied')
    active=[task for task in tasks if task['status'] in {'READY','EXECUTING','WAITING_ON_EXTERNAL'}]
    if active:
        mission['status']='EXECUTING';mission['current_action']=active[0]['description']
    elif any(task['status']=='AWAITING_CONFIRMATION' for task in tasks):
        mission['status']='AWAITING_CONFIRMATION';mission['current_action']='Waiting for your approval'
    elif all(task['status'] in TERMINAL for task in tasks):
        calendar=task_for(mission,'calendar.reschedule')
        late=calendar and calendar['status']=='COMPLETED' and mission['eta']['arrival']>mission['world']['calendar']['time']
        if tasks and all(task['status']=='CANCELLED' for task in tasks): mission['status']='CANCELLED'
        elif late or not tasks or any(task['status'] in {'BLOCKED','FAILED'} for task in tasks): mission['status']='ESCALATED'
        else: mission['status']='COMPLETED'
        mission['current_action']='Finished' if mission['status']=='COMPLETED' else 'Review unresolved tasks'
        mission['spoken_response']=summary(mission)
        if not mission['terminal_announced']:
            if late: event(mission,'REPLANNING','Updated ETA misses the agreed time; further negotiation requires review')
            event(mission,mission['status'],mission['spoken_response']);mission['terminal_announced']=True
    else:
        mission['status']='ESCALATED';mission['current_action']='No executable task; review dependencies'


def start(request):
    fingerprint=digest(request)
    with connection() as db:
        old=db.execute('SELECT fingerprint,state FROM active_missions WHERE start_key=?',(request['request_key'],)).fetchone()
        if old:
            if old[0]!=fingerprint: raise ValueError('Start key belongs to another mission')
            return json.loads(old[1])
        # ponytail: local DB lock spans planning; use per-request planning jobs before concurrent serving.
        if request.get('plan') is not None: plan=MissionPlan.model_validate(request['plan'])
        else: plan=mission_planner(request.get('mode','simulation')).plan_mission(planning_input(request['transcript']))
        for task in plan.tasks: validate(task.action,request['authorized'])
        stamp=now();scenario=request.get('scenario') or {}
        mission={'id':str(uuid4()),'engine_version':2,'contract_version':'1','goal':request['transcript'],
                 'transcript':request['transcript'],'plan':plan.model_dump(),'planner':('Evon' if request.get('mode')=='live' else 'MockEvon') if request.get('plan') is None else 'provided-plan',
                 'mode':request.get('mode','simulation'),'external_tools':'simulated','authorized':request['authorized'],
                 'revision':0,'step':0,'status':'PLANNING','created_at':stamp,'updated_at':stamp,
                 'requirements':{'max_detour_minutes':min([scenario.get('max_detour_minutes',5)]+[node.arguments.max_detour_minutes for node in plan.tasks if node.action in {'parking.select','fuel.select'}]),'include_fuel':True},
                 'requirements_version':0,'world':services.initial(scenario),'route':{'parking':None,'fuel':None},
                 'confirmation':None,'approved_confirmations':[],'plan_review':plan.needs_confirmation,
                 'demo':request.get('demo','none'),'demo_event_fired':False,'terminal_announced':False,'events':[],'tasks':[],
                 'spoken_response':'Mission started. I will handle the simulated meeting and route.'}
        for node in plan.tasks:
            mission['tasks'].append({'id':node.id,'tool':node.action,'description':LABELS[node.action],
                'inputs':node.arguments.model_dump(),'dependencies':node.depends_on,'status':'PLANNED',
                'history':[],'generation':0,'attempts':0,'candidate':None,'output':None,
                'created_at':stamp,'updated_at':stamp})
        event(mission,'PLANNING','Mission graph persisted; no call or calendar action has run')
        refresh_route(mission)
        if plan.needs_confirmation: pending_confirmation(mission,None,'plan.review',plan.model_dump(),'Approve the proposed mission plan')
        update_view(mission)
        db.execute('INSERT INTO active_missions VALUES (?,?,?,?)',(mission['id'],request['request_key'],fingerprint,encoded(mission)))
        return mission

def external_change(mission,patch):
    updated=services.change(mission['world'],patch)
    if all(value==mission['world'][key] for key,value in updated.items() if key!='version'):
        return
    mission['world']=updated
    details=[]
    if 'parking_full' in patch: details.append('Office garage is '+('full' if patch['parking_full'] else 'available'))
    if 'alternative_parking_full' in patch: details.append('East lot is '+('full' if patch['alternative_parking_full'] else 'available'))
    if 'contact_response' in patch: details.append('Ananya response: '+patch['contact_response'].replace('_',' '))
    if 'counter_offer' in patch: details.append('Ananya changed her counter-offer')
    if 'fuel_detour_minutes' in patch: details.append('Fuel detour is '+str(patch['fuel_detour_minutes'])+' minutes')
    if 'base_travel_minutes' in patch: details.append('Base route time is '+str(patch['base_travel_minutes'])+' minutes')
    event(mission,'WORLD_CHANGED','; '.join(details))
    parking_changed=any(key in patch for key in ['parking_full','alternative_parking_full'])
    fuel_changed='fuel_detour_minutes' in patch
    # In-progress candidates are checked in the next transition, making failure visible.
    parking=task_for(mission,'parking.select');fuel=task_for(mission,'fuel.select')
    if parking_changed and parking and parking['status'] in TERMINAL:
        mission['route']['parking']=None;mission['route']['fuel']=None
        reopen(mission,parking,'Parking changed after selection; inspect alternatives')
        if fuel: reopen(mission,fuel,'Parking changed; recalculate remaining fuel budget')
    elif fuel_changed and fuel and fuel['status'] in TERMINAL:
        mission['route']['fuel']=None;reopen(mission,fuel,'Fuel detour changed; inspect alternatives')
    if any(key in patch for key in ['contact_response','counter_offer']):
        contact=task_for(mission,'contact.negotiate');calendar=task_for(mission,'calendar.reschedule')
        if contact and contact['status'] in TERMINAL and contact['attempts']<2 and calendar and calendar['status']!='COMPLETED':
            mission['confirmation']=None
            reopen(mission,contact,'External party available; resume negotiation')
            if calendar: reopen(mission,calendar,'Wait for renewed negotiation')
    if 'base_travel_minutes' in patch:
        event(mission,'REPLANNING','Maps changed; recalculate the route ETA')
    refresh_route(mission,'Route conditions changed')
    mission['terminal_announced']=False


def advance(db,mission):
    if mission.get('plan_review'): return
    update_view(mission)
    task=next((item for item in mission['tasks'] if item['status'] in {'READY','EXECUTING','WAITING_ON_EXTERNAL'}),None)
    if not task: return
    mission['step']+=1
    parking=task_for(mission,'parking.select')
    if mission['demo']=='parking-change' and not mission['demo_event_fired'] and parking and parking['candidate'] and parking['candidate']['id']=='p1':
        external_change(mission,{'parking_full':True});mission['demo_event_fired']=True
        event(mission,'DEMO_EVENT','Office garage became full after the initial candidate was selected')
    action=task['tool'];world=mission['world']
    validate(action,mission['authorized'])
    if action=='contact.negotiate':
        if task['status']=='READY':
            if task['attempts']>=2:
                transition(mission,task,'BLOCKED','Two call attempts exhausted; ask the user to intervene');return
            effect(db,mission,task,'notify-intent','contact.delay_queued',{'contact':'Ananya','delay_minutes':task['inputs']['delay_minutes']})
            task['attempts']+=1;world['contact']['call_state']='DIALING'
            effect(db,mission,task,'call:'+str(task['attempts']),'contact.call',{'contact':'Ananya','proposed_time':'16:30','attempt':task['attempts']})
            transition(mission,task,'WAITING_ON_EXTERNAL','Calling Ananya, attempt '+str(task['attempts']))
        else:
            call_state=world['contact']['call_state']
            stages={'DIALING':('RINGING','Synthetic call ringing'),
                    'RINGING':('CONNECTED','Synthetic call connected'),
                    'CONNECTED':('REQUEST_COMMUNICATED','Delay and 4:30 request communicated')}
            if call_state in stages and (call_state=='DIALING' or world['contact']['response']!='no_answer'):
                world['contact']['call_state'],message=stages[call_state]
                event(mission,'CALL_STATE',message,task['id']);return
            output=services.contact(world)
            event(mission,'CALL_RESULT','Structured simulated response received: '+output['response'],task['id'])
            if output['response']!='no_answer':
                effect(db,mission,task,'notify','contact.notify_delay',{'contact':'Ananya','delay_minutes':task['inputs']['delay_minutes']})
            if output['response']=='no_answer':
                world['contact']['call_state']='NO_ANSWER'
                transition(mission,task,'REPLANNING','No answer; retry the same notification request once',output)
                transition(mission,task,'READY' if task['attempts']<2 else 'BLOCKED','Retry queued' if task['attempts']<2 else 'No answer after two attempts')
            elif output['response']=='rejected':
                world['contact']['call_state']='DECLINED'
                event(mission,'REPLANNING','Ananya declined 4:30'+('; offered '+output['counter_offer'] if output['counter_offer'] else '; no alternative provided'),task['id'])
                transition(mission,task,'COMPLETED' if output['counter_offer'] else 'BLOCKED','Counter-offer requires user approval' if output['counter_offer'] else 'Meeting time rejected',output)
            else:
                world['contact']['call_state']='ACCEPTED';output['accepted_time']='16:30'
                transition(mission,task,'COMPLETED','Ananya accepted 4:30',output)
    elif action=='calendar.reschedule':
        contact=task_for(mission,'contact.negotiate')['output']
        agreed=contact['accepted_time'] or contact['counter_offer']
        proposal=pending_confirmation(mission,task,action,{'meeting_id':'demo-meeting','time':agreed},'Move the demo meeting to '+display_time(agreed))
        approved=proposal['id'] in mission['approved_confirmations']
        if not validate_calendar_change(mission['authorized'],contact,agreed,approved):
            transition(mission,task,'AWAITING_CONFIRMATION','Ananya proposed '+display_time(agreed)+'; calendar waits for explicit approval')
        else:
            effect(db,mission,task,'calendar:'+agreed,action,{'meeting_id':'demo-meeting','time':agreed})
            world['calendar']['time']=agreed;mission['confirmation']=None
            transition(mission,task,'COMPLETED','Calendar updated after verified agreement',{'time':agreed,'simulated':True})
    else:
        kind=action.split('.')[0]
        if kind=='fuel' and not mission['requirements']['include_fuel']:
            mission['route'][kind]=None;transition(mission,task,'SKIPPED','User removed the fuel requirement');refresh_route(mission,'Fuel removed');return
        used=mission['route']['parking']['detour_minutes'] if kind=='fuel' and mission['route']['parking'] else 0
        limit=min(task['inputs']['max_detour_minutes'],mission['requirements']['max_detour_minutes'])-used
        if task['status']=='READY':
            choices=services.candidates(world,kind,limit)
            if not choices:
                mission['route'][kind]=None
                transition(mission,task,'SKIPPED' if kind=='fuel' else 'BLOCKED','No '+kind+' candidate within the shared detour limit')
            else:
                task['candidate']=choices[0]
                transition(mission,task,'EXECUTING','Checking '+choices[0]['name']+' before choosing the route')
        else:
            candidate=services.verify(world,kind,task['candidate']['id'])
            if not candidate['available'] or candidate['detour_minutes']>limit:
                mission['route'][kind]=None
                transition(mission,task,'REPLANNING',candidate['name']+' is unavailable or exceeds the current detour limit')
                task['candidate']=None;task['generation']+=1
                transition(mission,task,'READY','Check the next feasible candidate')
            else:
                mission['route'][kind]=candidate
                effect(db,mission,task,kind+':'+str(task['generation'])+':'+candidate['id'],action,candidate)
                transition(mission,task,'COMPLETED',candidate['name']+' verified and selected',{**candidate,'simulated':True})
        refresh_route(mission,'Route recalculated')


def command(mission_id,operation,request):
    fingerprint=digest({'operation':operation,**request})
    with connection() as db:
        mission=load(db,mission_id)
        old=db.execute('SELECT fingerprint FROM mission_commands WHERE mission_id=? AND key=?',(mission_id,request['request_key'])).fetchone()
        if old:
            if old[0]!=fingerprint: raise ValueError('Command key belongs to a different action')
            return mission
        if mission['revision']!=request['expected_revision']: raise ValueError('Mission changed; refresh before applying the command')
        if operation=='advance': advance(db,mission)
        elif operation=='world': external_change(mission,request['changes'])
        elif operation=='requirements':
            changes={key:value for key,value in request['changes'].items() if mission['requirements'][key]!=value}
            mission['requirements'].update(changes)
            if changes: mission['requirements_version']+=1
            notes=[]
            if 'max_detour_minutes' in changes: notes.append('User limited total route detour to '+str(changes['max_detour_minutes'])+' minutes')
            if 'include_fuel' in changes: notes.append('User '+('included' if changes['include_fuel'] else 'removed')+' the fuel stop')
            if notes: event(mission,'REPLANNING','; '.join(notes))
            if 'max_detour_minutes' in changes:
                mission['route']={'parking':None,'fuel':None}
                reopen(mission,task_for(mission,'parking.select'),'Recheck parking under the new detour limit')
                reopen(mission,task_for(mission,'fuel.select'),'Recheck fuel under the new remaining budget')
            elif 'include_fuel' in changes:
                mission['route']['fuel']=None;reopen(mission,task_for(mission,'fuel.select'),'User changed fuel requirement')
            if mission.get('confirmation'):
                pending=mission['confirmation'];task=next((t for t in mission['tasks'] if t['id']==pending['task_id']),None)
                pending_confirmation(mission,task,pending['action'],pending['arguments'],pending['label'])
            refresh_route(mission,'User requirement changed')
        elif operation=='confirm':
            pending=mission.get('confirmation')
            if not pending or pending['id']!=request['confirmation_id']: raise ValueError('Confirmation is missing or stale')
            if not request['approved']:
                if pending['action']=='plan.review':
                    mission['plan_review']=False
                    for task in mission['tasks']: transition(mission,task,'CANCELLED','User declined the proposed plan')
                else:
                    task=next(task for task in mission['tasks'] if task['id']==pending['task_id'])
                    transition(mission,task,'BLOCKED','User declined calendar change')
                mission['confirmation']=None
            else:
                mission['approved_confirmations'].append(pending['id']);mission['plan_review']=False
                if pending['task_id']:
                    task=next(task for task in mission['tasks'] if task['id']==pending['task_id'])
                    transition(mission,task,'READY','Exact calendar action approved')
                mission['confirmation']=None
            event(mission,'CONFIRMATION','User '+('approved' if request['approved'] else 'declined')+' the concrete proposed action')
        else: raise ValueError('Unknown mission command')
        update_view(mission);mission['revision']+=1;mission['updated_at']=now()
        db.execute('UPDATE active_missions SET state=? WHERE id=?',(encoded(mission),mission_id))
        db.execute('INSERT INTO mission_commands VALUES (?,?,?)',(mission_id,request['request_key'],fingerprint))
        return mission
