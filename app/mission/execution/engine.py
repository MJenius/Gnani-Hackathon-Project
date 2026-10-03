import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from app.agent.planner.demo import extract
from app.agent.policies.actions import validate
from app.tools.calls.simulated import notify_delay

def execute(request):
    path = Path(os.getenv('DRIVEOS_DB', 'data/driveos.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = json.dumps(request, sort_keys=True)
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS missions (key TEXT PRIMARY KEY, request TEXT, result TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS notifications (mission_id TEXT PRIMARY KEY, contact TEXT, delay INTEGER)')
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT request, result FROM missions WHERE key=?', (request['request_key'],)).fetchone()
        if old:
            if old[0] != fingerprint:
                raise ValueError('Request key already belongs to a different mission')
            return json.loads(old[1])
        now = datetime.now(timezone.utc).isoformat()
        mission = {'id': str(uuid4()), 'status': 'PLANNING', 'transcript': request['transcript'],
                   'tasks': [], 'events': [], 'created_at': now, 'mode': 'simulation'}
        def event(status, message):
            mission['events'].append({'status': status, 'message': message,
                                      'timestamp': datetime.now(timezone.utc).isoformat()})
        event('PLANNING', 'Understanding the requested mission')
        inputs = extract(request['transcript'])
        if inputs is None:
            mission['status'] = 'ESCALATED'
            mission['spoken_response'] = 'Try: Tell Ananya I am 25 minutes late. Other missions are not supported yet.'
            event('ESCALATED', 'Mission outside the current demo scope')
        else:
            validate('contact.notify_delay', request['authorized'])
            task = {'id': str(uuid4()), 'description': 'Notify Ananya of delay', 'status': 'EXECUTING',
                    'dependencies': [], 'priority': 1, 'tool': 'contact.notify_delay', 'inputs': inputs,
                    'output': None, 'confirmation_required': False, 'retry_policy': {'max_attempts': 1},
                    'created_at': now, 'updated_at': now}
            mission['tasks'].append(task)
            mission['status'] = 'EXECUTING'
            event('EXECUTING', 'Sending simulated delay notification')
            task['output'] = notify_delay(db, mission['id'], inputs)
            task['status'] = 'COMPLETED'
            task['updated_at'] = datetime.now(timezone.utc).isoformat()
            mission['status'] = 'COMPLETED'
            mission['spoken_response'] = f"Demo notification sent. Ananya knows you are {inputs['delay_minutes']} minutes late."
            event('COMPLETED', mission['spoken_response'])
        db.execute('INSERT INTO missions VALUES (?, ?, ?)',
                   (request['request_key'], fingerprint, json.dumps(mission)))
        return mission
