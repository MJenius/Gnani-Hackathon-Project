import base64
from typing import Literal
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.agent.planner.contract import MissionPlan
from app.mission.execution import persistent
from app.mission.execution.engine import execute
from app.config import capabilities
from app.speech.gnani import ProviderError, wav_info
from app.speech.loop import run as run_voice, mission_speech
from app.speech.usage import BudgetExceeded

app = FastAPI(title="DriveOS", version="0.1.0")

class StrictRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)

class StartMission(StrictRequest):
    transcript: str = Field(min_length=1,max_length=2000)
    request_key: str = Field(min_length=1,max_length=100)
    authorized: bool = False
    demo: Literal['none','parking-change'] = 'none'
    plan: MissionPlan | None = None

class CommandRequest(StrictRequest):
    request_key: str = Field(min_length=1,max_length=100)
    expected_revision: int = Field(ge=0)

class WorldChanges(StrictRequest):
    parking_full: bool | None = None
    alternative_parking_full: bool | None = None
    contact_response: Literal['accepted','rejected','no_answer'] | None = None
    counter_offer: Literal['16:45'] | None = '16:45'
    fuel_detour_minutes: int | None = Field(default=None,ge=0,le=30)
    base_travel_minutes: int | None = Field(default=None,ge=1,le=120)

    @model_validator(mode='after')
    def supplied(self):
        if not self.model_fields_set: raise ValueError('Supply a condition change')
        if any(getattr(self,key) is None for key in self.model_fields_set if key!='counter_offer'):
            raise ValueError('Condition values cannot be null')
        return self

class RequirementChanges(StrictRequest):
    max_detour_minutes: int | None = Field(default=None,ge=0,le=5)
    include_fuel: bool | None = None

    @model_validator(mode='after')
    def supplied(self):
        if not self.model_fields_set or any(getattr(self,key) is None for key in self.model_fields_set):
            raise ValueError('Supply concrete requirement changes')
        return self

class ChangeWorld(CommandRequest):
    changes: WorldChanges

class ChangeRequirements(CommandRequest):
    changes: RequirementChanges

class ConfirmAction(CommandRequest):
    confirmation_id: str = Field(min_length=64,max_length=64)
    approved: bool

def mission_operation(call,*args):
    try: return call(*args)
    except LookupError as error: raise HTTPException(404,str(error)) from error
    except PermissionError as error: raise HTTPException(403,str(error)) from error
    except ValueError as error: raise HTTPException(409,str(error)) from error
    except ProviderError as error: raise HTTPException(502,str(error)) from error
    except BudgetExceeded as error: raise HTTPException(429,str(error)) from error

@app.post('/missions/start')
def start_mission(request: StartMission):
    return mission_operation(persistent.start,request.model_dump())

@app.get('/missions/{mission_id}')
def read_mission(mission_id: str):
    return mission_operation(persistent.get,mission_id)

@app.post('/missions/{mission_id}/advance')
def advance_mission(mission_id: str,request: CommandRequest):
    return mission_operation(persistent.command,mission_id,'advance',request.model_dump())

@app.patch('/missions/{mission_id}/world')
def change_world(mission_id: str,request: ChangeWorld):
    return mission_operation(persistent.command,mission_id,'world',request.model_dump(exclude_unset=True))

@app.patch('/missions/{mission_id}/requirements')
def change_requirements(mission_id: str,request: ChangeRequirements):
    return mission_operation(persistent.command,mission_id,'requirements',request.model_dump(exclude_unset=True))

@app.post('/missions/{mission_id}/confirm')
def confirm_action(mission_id: str,request: ConfirmAction):
    return mission_operation(persistent.command,mission_id,'confirm',request.model_dump())

class DemoScenario(BaseModel):
    contact_response: Literal['accepted','rejected','no_answer'] = 'accepted'
    parking_full: bool = False
    max_detour_minutes: int = Field(default=5,ge=0,le=5)

class MissionRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=2000)
    request_key: str = Field(min_length=1, max_length=100)
    authorized: bool = False
    mode: Literal['simulation', 'live', 'speech_test'] = 'simulation'
    scenario: DemoScenario = Field(default_factory=DemoScenario)

@app.get('/health')
def health():
    return {'status': 'ok', **capabilities()}

@app.post('/missions')
def create_mission(request: MissionRequest):
    try:
        return execute(request.model_dump())
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except ProviderError as error:
        raise HTTPException(502, str(error)) from error
    except BudgetExceeded as error:
        raise HTTPException(429, str(error)) from error

@app.post('/voice/missions')
def voice_mission(audio: UploadFile = File(...), language: Literal['en-IN','kn-IN','hi-IN'] = Form('en-IN'),
                  request_key: str = Form(..., min_length=1, max_length=100), authorized: bool = Form(False),
                  mode: Literal['live','speech_test'] = Form('speech_test'),
                  persistent_mission: bool = Form(False), demo: Literal['none','parking-change'] = Form('none')):
    if not authorized:
        raise HTTPException(403, 'Authorize the synthetic notification before starting voice capture')
    if mode == 'live' and not capabilities()['evon_configured']:
        raise HTTPException(503, 'Evon is not configured; full Gnani live mode is unavailable')
    if not capabilities()['speech_configured']:
        raise HTTPException(503,'Gnani speech credentials are not configured')
    content = audio.file.read(4_000_001)
    try:
        wav_info(content)
        mission, output, speech_error = run_voice(content, language, request_key, authorized, mode,persistent_mission,demo)
        return {**mission, 'audio_base64':base64.b64encode(output).decode('ascii') if output else None,
                'audio_type':'audio/wav', 'speech_error':speech_error}
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except ProviderError as error:
        raise HTTPException(502, str(error)) from error
    except BudgetExceeded as error:
        raise HTTPException(429, str(error)) from error

class SpeechRequest(StrictRequest):
    expected_revision: int = Field(ge=0)

@app.post('/missions/{mission_id}/speech')
def speak_mission(mission_id: str,request: SpeechRequest):
    output=mission_operation(mission_speech,mission_id,request.expected_revision)
    return {'audio_base64':base64.b64encode(output).decode('ascii'),'audio_type':'audio/wav'}
