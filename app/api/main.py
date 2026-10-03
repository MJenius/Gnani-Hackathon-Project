from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.mission.execution.engine import execute

app = FastAPI(title="DriveOS", version="0.1.0")

class MissionRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=2000)
    request_key: str = Field(min_length=1, max_length=100)
    authorized: bool = False

@app.get('/health')
def health():
    return {'status': 'ok', 'mode': 'simulation', 'gnani_connected': False}

@app.post('/missions')
def create_mission(request: MissionRequest):
    try:
        return execute(request.model_dump())
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
