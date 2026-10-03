"""Synthetic tool facts. No external calls, calendar access, routing or payment."""
import json

PARKING=[{'id':'p1','name':'Office garage','detour_minutes':2},
         {'id':'p2','name':'East lot','detour_minutes':3}]
FUEL=[{'id':'f1','name':'Route fuel stop','detour_minutes':2},
      {'id':'f2','name':'Far fuel stop','detour_minutes':7}]

def perform(db, mission_id, task, scenario, completed):
    action=task.action; args=task.arguments
    if action=='contact.negotiate':
        response=scenario['contact_response']
        result={'contact':'Ananya','delay_minutes':args.delay_minutes,'proposed_time':args.proposed_time,
                'response':response,'attempts':1,'simulated':True}
    elif action=='calendar.reschedule':
        agreed=any(completed[key].get('response')=='accepted' for key in task.depends_on)
        if not agreed: return {'status':'blocked','reason':'No explicit acceptance','simulated':True}
        result={'meeting_id':args.meeting_id,'new_time':args.proposed_time,'simulated':True}
    else:
        parking=action=='parking.select'
        candidates=PARKING if parking else FUEL
        used=0 if parking else sum(value.get('detour_minutes',0) for value in completed.values() if value.get('kind')=='parking')
        available=[item for item in candidates if not parking or not scenario['parking_full'] or item['id']!='p1']
        limit=min(args.max_detour_minutes,scenario['max_detour_minutes'])
        candidate=next((item for item in available if item['detour_minutes']+used<=limit),None)
        if not candidate: return {'status':'skipped','reason':'No candidate within total detour limit','simulated':True}
        result={**candidate,'kind':'parking' if parking else 'fuel','total_detour_minutes':used+candidate['detour_minutes'],
                'candidate_count':len(candidates),'replanned':parking and scenario['parking_full'],'simulated':True}
    db.execute('INSERT INTO tool_effects VALUES (?,?,?,?)',(mission_id,task.id,action,json.dumps(result)))
    return result
