"""One backend-only request through EvonClient; no fallback or raw response logs."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import httpx

from app.agent.planner.evon import EvonClient

REQUEST = 'Notify Ananya that I am 25 minutes late.'


def run():
    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'endpoint_configured': bool(os.getenv('EVON_BASE_URL', '').strip()),
        'model_configured': bool(os.getenv('EVON_MODEL', '').strip()),
        'evon_credential_configured': bool(os.getenv('EVON_API_KEY')),
        'participant_credential_configured': bool(os.getenv('GNANI_API_KEY')),
        'credential_used': 'EVON_API_KEY' if os.getenv('EVON_API_KEY') else 'none',
        'request_sent': False, 'http_status': None, 'latency_ms': None,
        'response_shape': None, 'response_valid_json': None,
        'plan_valid_json': None, 'plan_schema_valid': False,
        'required_intent_expressed': None, 'model_identifier_accepted': None,
        'returned_model_matches': None, 'success': False,
    }
    if not result['endpoint_configured'] or not result['model_configured']:
        result['reason'] = 'missing_explicit_endpoint_or_model'
        return result

    # Observe the existing transport, without replacing completion or its validation.
    post = httpx.post

    def observe(*args, **kwargs):
        result['request_sent'] = True
        started = perf_counter()
        try:
            response = post(*args, **kwargs)
        finally:
            result['latency_ms'] = round((perf_counter() - started) * 1000, 1)
        result['http_status'] = response.status_code
        try:
            body = response.json()
        except ValueError:
            result['response_valid_json'] = False
            result['response_shape'] = 'non_json'
            return response
        result['response_valid_json'] = True
        result['response_shape'] = type(body).__name__
        if isinstance(body, dict):
            choices = body.get('choices')
            result['response_shape'] = {
                'root': 'object', 'choices': type(choices).__name__,
                'response': type(body.get('response')).__name__,
            }
            if isinstance(body.get('model'), str):
                result['returned_model_matches'] = body['model'] == os.environ['EVON_MODEL']
            try:
                content = choices[0]['message']['content']
                result['response_shape']['content'] = type(content).__name__
                json.loads(content)
                result['plan_valid_json'] = True
            except (KeyError, IndexError, TypeError, ValueError):
                result['plan_valid_json'] = False
            # A completion is evidence that the supplied identifier was accepted;
            # it does not independently establish the identity of the served weights.
            if response.status_code == 200 and isinstance(choices, list) and choices:
                result['model_identifier_accepted'] = True
        return response

    try:
        with patch('app.agent.planner.evon.httpx.post', side_effect=observe):
            plan = EvonClient().plan(REQUEST)
        result['plan_schema_valid'] = True
        result['required_intent_expressed'] = (
            len(plan.tasks) == 1 and plan.tasks[0].contact == 'Ananya'
            and plan.tasks[0].delay_minutes == 25
            and plan.next_action == 'contact.notify_delay' and not plan.needs_confirmation
        )
        result['success'] = result['required_intent_expressed']
        result['reason'] = 'ok' if result['success'] else 'required_intent_not_expressed'
    except Exception:
        # Never serialize exceptions, URLs, headers, body text, or model identifiers.
        result['reason'] = (
            'http_failure' if result['http_status'] not in (None, 200)
            else 'invalid_response_or_plan' if result['http_status'] == 200
            else 'transport_or_preflight_failure'
        )
    return result


def main():
    result = run()
    output = Path(__file__).resolve().parents[3] / 'data/evon-smoke-results.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
