import json
import unittest
from unittest.mock import patch

import httpx

from app.evaluation.runners.evon_smoke import run


class EvonSmokeTests(unittest.TestCase):
    def test_gate_and_real_transport_failures(self):
        with patch.dict('os.environ', {'EVON_BASE_URL': '', 'EVON_MODEL': 'explicit'}), patch('httpx.post') as post:
            self.assertEqual(run()['reason'], 'missing_explicit_endpoint_or_model')
            post.assert_not_called()
        valid = {'goal': 'Notify Ananya', 'tasks': [{'tool': 'contact.notify_delay',
                 'contact': 'Ananya', 'delay_minutes': 25}],
                 'next_action': 'contact.notify_delay', 'needs_confirmation': False}
        bodies = [(401, {'error': 'SECRET'}), (200, {'response': 'SECRET'}),
                  (200, {'choices': [{'message': {'content': json.dumps(valid)}}]})]
        with patch.dict('os.environ', {'EVON_BASE_URL': 'https://example.invalid/v1', 'EVON_MODEL': 'explicit'}), patch('app.agent.planner.evon.measured'):
            for status, body in bodies:
                with self.subTest(status=status, body_shape=list(body)), patch('httpx.post', return_value=httpx.Response(status, json=body)) as post:
                    result = run()
                    self.assertEqual(result['http_status'], status)
                    self.assertEqual(result['success'], 'choices' in body)
                    self.assertNotIn('SECRET', json.dumps(result))
                    post.assert_called_once()


if __name__ == '__main__':
    unittest.main()
