import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.main import app
from app.agent.policies.actions import validate
from app.mission.execution.engine import execute

class Missions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = self.temp.name + '/test.sqlite3'
        self.env = patch.dict(os.environ, DRIVEOS_DB=self.path)
        self.env.start()
        self.client = TestClient(app)
        self.request = {'transcript': 'Tell Ananya I am 25 minutes late.', 'request_key': 'one', 'authorized': True}

    def tearDown(self):
        self.env.stop(); self.temp.cleanup()

    def test_end_to_end_and_replay(self):
        first = self.client.post('/missions', json=self.request)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()['status'], 'COMPLETED')
        self.assertEqual(first.json()['tasks'][0]['output']['delay_minutes'], 25)
        self.assertEqual(self.client.post('/missions', json=self.request).json(), first.json())
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0], 1)

    def test_key_collision(self):
        self.client.post('/missions', json=self.request)
        self.request['transcript'] = 'Tell Ananya I am 30 minutes late.'
        self.assertEqual(self.client.post('/missions', json=self.request).status_code, 409)

    def test_unauthorized_has_no_mutation(self):
        self.request['authorized'] = False
        self.assertEqual(self.client.post('/missions', json=self.request).status_code, 403)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0], 0)

    def test_unsupported_and_limits(self):
        for text in ['Buy fuel', 'Tell Ananya I am 121 minutes late.', 'Tell Ananya I am 25 minutes late and buy fuel']:
            request = dict(self.request, transcript=text, request_key=text)
            self.assertEqual(self.client.post('/missions', json=request).json()['status'], 'ESCALATED')
        self.assertEqual(self.client.post('/missions', json=dict(self.request, transcript='')).status_code, 422)

    def test_sensitive_and_unknown_actions_blocked(self):
        for tool in ['payment.purchase', 'untrusted.tool']:
            with self.assertRaises(PermissionError): validate(tool, authorized=True)

    def test_concurrent_retries_execute_once(self):
        # Initialize the schema before testing concurrent transaction contention.
        execute(dict(self.request, request_key='initialize', transcript='Unsupported'))
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: execute(self.request), range(4)))
        self.assertEqual(len({result['id'] for result in results}), 1)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0], 1)

    def test_tool_failure_rolls_back(self):
        def fail(db, mission_id, inputs):
            db.execute('INSERT INTO notifications VALUES (?, ?, ?)', (mission_id, 'Ananya', 25))
            raise RuntimeError('Simulated failure')
        with patch('app.mission.execution.engine.notify_delay', side_effect=fail):
            with self.assertRaises(RuntimeError): execute(self.request)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0], 0)
        self.assertEqual(execute(self.request)['status'], 'COMPLETED')

if __name__ == '__main__': unittest.main()
