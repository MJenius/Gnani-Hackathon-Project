import os
import tempfile
from unittest.mock import patch
from app.mission.execution.engine import execute

def main():
    cases = [('Tell Ananya I am 25 minutes late.', 'COMPLETED'),
             ('Tell Ananya I am 0 minutes late.', 'ESCALATED'),
             ('Buy petrol for me', 'ESCALATED')]
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, DRIVEOS_DB=directory+'/eval.sqlite3'):
        passed = sum(execute({'transcript': text, 'request_key': str(index), 'authorized': True})['status'] == expected
                     for index, (text, expected) in enumerate(cases))
    print(f'Deterministic text slice: {passed}/{len(cases)} expected outcomes')
    if passed != len(cases): raise SystemExit(1)

if __name__ == '__main__': main()
