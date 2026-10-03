"""Bounded v1 dependency execution; synthetic effects commit with mission state."""
from datetime import datetime, timezone
from app.agent.policies.actions import validate
from app.tools.simulated import perform

LABELS={'contact.negotiate':'Ask Ananya if 4:30 works','calendar.reschedule':'Update meeting after acceptance',
        'parking.select':'Find parking within the detour limit','fuel.select':'Find fuel within remaining detour budget'}

def run(db,mission,plan,request,event):
    scenario=request.get('scenario') or {'contact_response':'accepted','parking_full':False,'max_detour_minutes':5}
    if plan.needs_confirmation:
        mission['status']='AWAITING_CONFIRMATION'
        mission['spoken_response']='This plan needs review. No simulated action was taken.'
        event(mission['status'],mission['spoken_response']);return
    # Authorize the entire graph before any mutation.
    for task in plan.tasks:
        validate(task.action,request['authorized'])
    db.execute('CREATE TABLE IF NOT EXISTS tool_effects (mission_id TEXT, task_id TEXT, action TEXT, result TEXT, PRIMARY KEY(mission_id,task_id))')
    nodes={task.id:task for task in plan.tasks}; completed={}
    now=mission['created_at']
    for task in plan.tasks:
        mission['tasks'].append({'id':task.id,'description':LABELS[task.action],'tool':task.action,
            'inputs':task.arguments.model_dump(),'dependencies':task.depends_on,'status':'PLANNED',
            'output':None,'created_at':now,'updated_at':now,'confirmation_required':False,'retry_policy':{'max_attempts':1}})
    while len(completed)<len(nodes):
        ready=[task for task in mission['tasks'] if task['id'] not in completed and set(task['dependencies'])<=completed.keys()]
        if not ready: raise ValueError('Invalid mission dependencies')
        for task in ready:
            mission['status']='EXECUTING';task['status']='EXECUTING'
            event('EXECUTING',task['description'])
            if any(completed[key].get('status') in {'blocked','failed'} for key in task['dependencies']):
                output={'status':'blocked','reason':'Dependency did not succeed','simulated':True}
            else:
                output=perform(db,mission['id'],nodes[task['id']],scenario,completed)
            if task['tool']=='contact.negotiate' and output['response']!='accepted':
                output['status']='blocked'
                event('WAITING_ON_EXTERNAL','Ananya '+('declined 4:30' if output['response']=='rejected' else 'did not answer')+'; no calendar change')
            if output.get('replanned'):
                event('REPLANNING','Office garage is full. Verified East lot and recalculated the detour.')
            completed[task['id']]=output;task['output']=output
            task['status']={'blocked':'BLOCKED','skipped':'SKIPPED'}.get(output.get('status'),'COMPLETED')
            task['updated_at']=datetime.now(timezone.utc).isoformat()
    blocked=any(task['status']=='BLOCKED' for task in mission['tasks'])
    mission['status']='ESCALATED' if blocked else 'COMPLETED'
    parts=['Simulation complete.']
    if any(task['tool']=='contact.negotiate' for task in mission['tasks']):
        parts.append('Ananya accepted 4:30; the demo calendar was updated.' if not blocked else 'Agreement was not reached; the calendar was left unchanged.')
    for task in mission['tasks']:
        if task['tool'] in {'parking.select','fuel.select'}:
            output=task['output']
            parts.append(output['name']+' selected.' if task['status']=='COMPLETED' else task['tool'].split('.')[0].title()+' omitted: no option within the detour limit.')
    detour=sum(item.get('detour_minutes',0) for item in completed.values())
    if detour: parts.append(f'Total added route time: {detour} minutes. No reservation or fuel purchase was made.')
    mission['spoken_response']=' '.join(parts)
    event(mission['status'],mission['spoken_response'])
