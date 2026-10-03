import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

class BudgetExceeded(RuntimeError):
    pass

@contextmanager
def measured(model, operation, units):
    path = Path(os.getenv('DRIVEOS_USAGE_DB', 'data/gnani-usage.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = os.getenv('DRIVEOS_API_STAGE', 'dev')
    if stage not in {'dev', 'eval', 'demo', 'final'}:
        raise ValueError('Invalid API budget stage')
    maximum = int(os.getenv('DRIVEOS_API_MAX_REQUESTS', '40'))
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY, timestamp TEXT, stage TEXT, model TEXT, operation TEXT, latency_ms REAL, success INTEGER, units TEXT, status INTEGER)')
        db.execute('BEGIN IMMEDIATE')
        count = db.execute('SELECT count(*) FROM usage WHERE stage=?', (stage,)).fetchone()[0]
        if count >= maximum:
            raise BudgetExceeded('Local API request budget exhausted; review dashboard usage before increasing the cap')
        import json
        row_id = db.execute('INSERT INTO usage (timestamp,stage,model,operation,units) VALUES (?,?,?,?,?)',
                            (datetime.now(timezone.utc).isoformat(), stage, model, operation, json.dumps(units))).lastrowid
    started = perf_counter()
    metadata = {'status': None}
    success = False
    try:
        yield metadata
        success = True
    finally:
        with closing(sqlite3.connect(path, timeout=10)) as db, db:
            db.execute('UPDATE usage SET latency_ms=?, success=?, status=? WHERE id=?',
                       (round((perf_counter()-started)*1000, 1), int(success), metadata['status'], row_id))
