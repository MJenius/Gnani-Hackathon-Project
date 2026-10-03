import base64
from typing import Literal
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from app.mission.execution.engine import execute
from app.config import capabilities
from app.speech.gnani import ProviderError, wav_info
from app.speech.loop import run as run_voice
from app.speech.usage import BudgetExceeded

app = FastAPI(title="DriveOS", version="0.1.0")

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
                  mode: Literal['live','speech_test'] = Form('live')):
    if not authorized:
        raise HTTPException(403, 'Authorize the synthetic notification before starting voice capture')
    if mode == 'live' and not capabilities()['evon_configured']:
        raise HTTPException(503, 'Evon is not configured; full Gnani live mode is unavailable')
    content = audio.file.read(4_000_001)
    try:
        wav_info(content)
        mission, output, speech_error = run_voice(content, language, request_key, authorized, mode)
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
