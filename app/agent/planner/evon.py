import json
import os
from typing import Literal
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from app import config
from app.speech.gnani import ProviderError
from app.speech.usage import measured

class Task(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    tool: Literal['contact.notify_delay']
    contact: Literal['Ananya']
    delay_minutes: int = Field(ge=1, le=120)

class Plan(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    goal: str = Field(min_length=1, max_length=300)
    tasks: list[Task] = Field(max_length=1)
    next_action: Literal['contact.notify_delay', 'escalate']
    needs_confirmation: bool

def complete(messages, schema=None):
    base, model = os.getenv('EVON_BASE_URL', ''), os.getenv('EVON_MODEL', '')
    if not base or not model:
        raise ProviderError('Evon endpoint and model are not configured. Live mode is unavailable.')
    parsed = urlparse(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not (
        parsed.scheme == 'https' or (parsed.scheme == 'http' and parsed.hostname in {'localhost','127.0.0.1'})):
        raise ProviderError('Evon requires HTTPS or a loopback HTTP deployment')
    headers = {}
    if os.getenv('EVON_API_KEY'):
        headers['Authorization'] = 'Bearer '+os.environ['EVON_API_KEY']
    payload={'model':model,'messages':messages,'max_tokens':512,'temperature':0.6,'top_p':0.95,
             'repetition_penalty':1.1,'chat_template_kwargs':{'enable_thinking':False}}
    if os.getenv('EVON_INFERENCE_BACKEND')=='llama_cpp':
        payload['response_format']={'type':'json_schema','schema':schema or Plan.model_json_schema()}
    with measured(model, 'plan', {'input_characters':sum(len(item['content']) for item in messages), 'max_output_tokens':512}) as metadata:
        try:
            response = httpx.post(base.rstrip('/')+'/chat/completions', headers=headers, timeout=45,
                                  json=payload)
        except httpx.HTTPError:
            raise ProviderError('Evon connection failed or timed out') from None
        metadata['status'] = response.status_code
        if response.status_code != 200:
            raise ProviderError(f'Evon provider returned HTTP {response.status_code}')
        try:
            return response.json()['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError, ValueError, ValidationError):
            raise ProviderError('Evon returned an invalid mission plan; no action executed') from None

class EvonClient:
    """DriveOS contract independent of inference mechanism; completion returns JSON text.

    Default completion uses a separately configured OpenAI-compatible Evon deployment.
    A local inference implementation can be injected without changing the mission engine.
    No Hugging Face hosted endpoint is assumed and the speech key is never reused.
    """
    def __init__(self, completion=complete):
        self.completion = completion

    def plan(self, transcript):
        prompt = ('Return only a JSON object matching this schema: '+json.dumps(Plan.model_json_schema())+
                  '. Only act on an explicit instruction to tell/notify the synthetic contact Ananya of a delay. '
                  'Do not invent a delay, contact, or authorization. For ambiguity or additional tasks return tasks=[], '
                  'next_action=escalate. No chain of thought. The deterministic server owns authorization.')
        content = self.completion([{'role':'system','content':prompt},{'role':'user','content':transcript}])
        try:
            result = Plan.model_validate_json(content)
            if bool(result.tasks) != (result.next_action == 'contact.notify_delay'):
                raise ValueError()
            return result
        except (ValueError, TypeError, ValidationError):
            raise ProviderError('Evon returned an invalid mission plan; no action executed') from None

    def extract(self, transcript):
        result = self.plan(transcript)
        if result.needs_confirmation or not result.tasks:
            return None
        task = result.tasks[0]
        return {'contact': task.contact, 'delay_minutes': task.delay_minutes}

    def plan_mission(self, request):
        from app.agent.planner.contract import MissionPlan
        prompt='Return only JSON matching '+json.dumps(MissionPlan.model_json_schema())+'. Use only supplied tools and facts. Unsupported requests return tasks=[]. No reasoning. Calendar must depend on contact acceptance.'
        messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps(request,ensure_ascii=False)}]
        content=complete(messages,MissionPlan.model_json_schema()) if self.completion is complete else self.completion(messages)
        try:
            return MissionPlan.model_validate_json(content)
        except (ValueError,TypeError,ValidationError):
            raise ProviderError('Evon returned an invalid mission graph; no action executed') from None

class MockEvon(EvonClient):
    """Offline deterministic fallback. No model inference or network calls."""
    def plan(self, transcript):
        from app.agent.planner.demo import extract
        inputs=extract(transcript)
        return Plan(goal='Notify Ananya of delay' if inputs else 'Unsupported demo mission',
                    tasks=[Task(tool='contact.notify_delay',**inputs)] if inputs else [],
                    next_action='contact.notify_delay' if inputs else 'escalate',needs_confirmation=False)

    def plan_mission(self, request):
        from app.agent.planner.contract import MissionPlan
        text=request['mission'].strip().lower().replace('’',"'").rstrip('.!?')
        signature={"i'm running late for my meeting. tell ananya, ask if 4:30 works, find parking, and get fuel if it doesn't add more than five minutes",
                   "i'm running 25 minutes late. tell ananya, ask if 4:30 works, find parking near her office, and get fuel if it doesn't add more than five minutes"}
        negotiation={"i'm 20 minutes late. tell ananya and ask if 4:30 works",
                     'ನಾನು ಇಪ್ಪತ್ತು ನಿಮಿಷ ತಡವಾಗುತ್ತೇನೆ. ಅನನ್ಯ ಅವರಿಗೆ ತಿಳಿಸಿ ಮತ್ತು ನಾಲ್ಕೂವರೆ ಗಂಟೆಗೆ ಭೇಟಿಯಾಗಬಹುದೇ ಎಂದು ಕೇಳಿ'}
        parking={"find parking near the office, but don't add more than 5 minutes"}
        tasks=[]
        def add(action,arguments,depends_on=None):
            tasks.append({'id':'t'+str(len(tasks)+1),'action':action,'arguments':arguments,'depends_on':depends_on or []})
        if text in signature or text in negotiation:
            add('contact.negotiate',{'contact':'Ananya','delay_minutes':20 if text in negotiation else request['context']['eta_delay_minutes'],'proposed_time':'16:30'})
            add('calendar.reschedule',{'meeting_id':'demo-meeting','proposed_time':'16:30'},['t1'])
        if text in signature or text in parking:
            add('parking.select',{'destination':'office','max_detour_minutes':5})
        if text in signature:
            add('fuel.select',{'destination':'office','max_detour_minutes':5},['t3'])
        return MissionPlan(version='1',goal='Handle the synthetic mission' if tasks else 'Unsupported demo mission',tasks=tasks,needs_confirmation=False)

def mission_planner(mode='simulation'):
    selected=os.getenv('EVON_MODE','mock')
    if selected not in {'mock','remote'}: raise ValueError('Invalid EVON_MODE')
    if mode=='live' and selected!='remote':
        raise ProviderError('Live mode requires EVON_MODE=remote; no mock substitution')
    return EvonClient() if mode=='live' else MockEvon()
