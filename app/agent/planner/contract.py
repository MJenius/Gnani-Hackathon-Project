"""Frozen DriveOS planning contract v1. Providers propose; engine owns execution."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class ContactArgs(StrictModel):
    contact: Literal['Ananya']
    delay_minutes: int = Field(ge=1, le=120)
    proposed_time: Literal['16:30']

class CalendarArgs(StrictModel):
    meeting_id: Literal['demo-meeting']
    proposed_time: Literal['16:30']

class SearchArgs(StrictModel):
    destination: Literal['office']
    max_detour_minutes: int = Field(ge=0, le=5)

class ContactTask(StrictModel):
    id: str = Field(pattern=r'^t[0-9]+$')
    action: Literal['contact.negotiate']
    arguments: ContactArgs
    depends_on: list[str] = Field(max_length=12)

class CalendarTask(StrictModel):
    id: str = Field(pattern=r'^t[0-9]+$')
    action: Literal['calendar.reschedule']
    arguments: CalendarArgs
    depends_on: list[str] = Field(max_length=12)

class SearchTask(StrictModel):
    id: str = Field(pattern=r'^t[0-9]+$')
    action: Literal['parking.select', 'fuel.select']
    arguments: SearchArgs
    depends_on: list[str] = Field(max_length=12)

class MissionPlan(StrictModel):
    version: Literal['1']
    goal: str = Field(min_length=1, max_length=300)
    tasks: list[Annotated[ContactTask | CalendarTask | SearchTask, Field(discriminator='action')]] = Field(max_length=12)
    needs_confirmation: bool

    @model_validator(mode='after')
    def validate_graph(self):
        nodes={task.id:task for task in self.tasks}
        if len(nodes)!=len(self.tasks): raise ValueError('Duplicate task IDs')
        actions=[task.action for task in self.tasks]
        if len(set(actions))!=len(actions): raise ValueError('One task per supported action')
        done=set()
        while len(done)<len(nodes):
            ready={key for key,task in nodes.items() if key not in done and set(task.depends_on)<=done}
            if not ready: raise ValueError('Unknown dependency or cycle')
            done.update(ready)
        for task in self.tasks:
            if task.action=='calendar.reschedule':
                if not any(nodes[key].action=='contact.negotiate' for key in task.depends_on):
                    raise ValueError('Calendar update must depend on negotiation')
            if task.action=='fuel.select' and 'parking.select' in actions:
                if not any(nodes[key].action=='parking.select' for key in task.depends_on):
                    raise ValueError('Fuel selection must depend on the parking detour')
        return self

TOOLS=['contact.negotiate','calendar.reschedule','parking.select','fuel.select']

def planning_input(mission):
    return {'version':'1','mission':mission,
            'context':{'contact':'Ananya','meeting_id':'demo-meeting','destination':'office',
                       'eta_delay_minutes':25,'meeting_time':'16:00','requested_new_time':'16:30',
                       'source':'synthetic demo fixtures'},
            'available_tools':TOOLS,
            'constraints':['No real calls or purchases','Calendar change only after explicit acceptance',
                           'At most five total added route minutes','Unknown or ambiguous requests escalate']}
