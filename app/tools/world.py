"""Deterministic, mutable per-mission services. No network or real-world effects."""
from copy import deepcopy

def initial(scenario):
    return {'contact':{'response':scenario.get('contact_response','accepted'),'counter_offer':'16:45','call_state':'IDLE'},
            'calendar':{'meeting_id':'demo-meeting','time':'16:00'},
            'parking':[{'id':'p1','name':'Office garage','available':not scenario.get('parking_full',False),'detour_minutes':2},
                       {'id':'p2','name':'East lot','available':True,'detour_minutes':3}],
            'fuel':[{'id':'f1','name':'Route fuel stop','available':True,'detour_minutes':2},
                    {'id':'f2','name':'Far fuel stop','available':True,'detour_minutes':7}],
            'maps':{'departure':'16:00','base_minutes':25},'version':0}

def change(world,patch):
    world=deepcopy(world)
    for key,value in patch.items():
        if key=='parking_full': world['parking'][0]['available']=not value
        elif key=='alternative_parking_full': world['parking'][1]['available']=not value
        elif key=='contact_response': world['contact']['response']=value
        elif key=='counter_offer': world['contact']['counter_offer']=value
        elif key=='fuel_detour_minutes': world['fuel'][0]['detour_minutes']=value
        elif key=='base_travel_minutes': world['maps']['base_minutes']=value
        else: raise ValueError('Unknown synthetic condition')
    world['version']+=1
    return world

def contact(world):
    response=world['contact']['response']
    return {'response':response,'accepted_time':None,'counter_offer':world['contact']['counter_offer'] if response=='rejected' else None,'simulated':True}

def candidates(world,kind,remaining):
    return [deepcopy(item) for item in world[kind] if item['available'] and item['detour_minutes']<=remaining]

def verify(world,kind,candidate_id):
    return deepcopy(next(item for item in world[kind] if item['id']==candidate_id))

def eta(world,route):
    detour=sum(item['detour_minutes'] for item in route.values() if item)
    hour,minute=map(int,world['maps']['departure'].split(':'))
    total=hour*60+minute+world['maps']['base_minutes']+detour
    return {'arrival':f'{total//60:02}:{total%60:02}','base_minutes':world['maps']['base_minutes'],
            'added_minutes':detour,'travel_minutes':world['maps']['base_minutes']+detour,'simulated':True}
