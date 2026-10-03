import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)

def mode():
    value = os.getenv('DRIVEOS_MODE', 'simulation')
    if value not in {'simulation', 'live', 'speech_test'}:
        raise ValueError('Invalid DRIVEOS_MODE')
    return value

def capabilities():
    return {'mode': mode(), 'speech_configured': bool(os.getenv('GNANI_API_KEY')),
            'evon_configured': bool(os.getenv('EVON_MODE','mock')=='remote' and os.getenv('EVON_BASE_URL') and os.getenv('EVON_MODEL')),
            'evon_mode':os.getenv('EVON_MODE','mock'),
            'external_tools': 'simulated', 'gnani_connected': False}
