import io
import os
import wave
import httpx
from app import config  # Loads only the server-side local environment.
from app.speech.usage import measured

BASE = 'https://api.vachana.ai'
VOICES = {'en-IN': 'Kaveri', 'kn-IN': 'Saanvi', 'hi-IN': 'Nalini', 'hi-en': 'Poorvi', 'auto': 'Saanvi'}

class ProviderError(RuntimeError):
    pass

def wav_info(audio):
    if not audio or len(audio) > 4_000_000:
        raise ValueError('WAV audio must be between 1 byte and 4 MB')
    try:
        with wave.open(io.BytesIO(audio)) as wav:
            duration = wav.getnframes()/wav.getframerate()
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() not in {8000,16000,22050,24000,44100,48000} or not 0 < duration <= 30:
                raise ValueError('Use mono 16-bit WAV audio, at most 30 seconds')
            expected = wav.getnframes() * 2
            if len(wav.readframes(wav.getnframes())) != expected:
                raise ValueError('Truncated WAV audio')
            return {'audio_seconds': round(duration,3), 'sample_rate': wav.getframerate()}
    except (wave.Error, EOFError, ZeroDivisionError) as error:
        raise ValueError('Invalid WAV audio') from error

def post(path, model, operation, units, **kwargs):
    key = os.getenv('GNANI_API_KEY')
    if not key:
        raise ProviderError('Gnani speech credentials are not configured')
    with measured(model, operation, units) as metadata:
        try:
            response = httpx.post(BASE+path, headers={'X-API-Key-ID': key}, timeout=45, **kwargs)
        except httpx.HTTPError:
            raise ProviderError(f'{operation} connection failed or timed out; no automatic retry') from None
        metadata['status'] = response.status_code
        if response.status_code != 200:
            # Do not relay provider bodies, which may contain echoed inputs or credentials.
            raise ProviderError(f'{operation} provider returned HTTP {response.status_code}')
        return response

def transcribe(audio, language='en-IN'):
    if language not in {'en-IN', 'hi-IN', 'kn-IN'}:
        raise ValueError('Unsupported transcription language')
    units = wav_info(audio)
    response = post('/stt/v3', 'gnani-prisma-v2.5', 'transcribe', units,
                    files={'audio_file': ('utterance.wav', audio, 'audio/wav')},
                    data={'language_code': language, 'format': 'transcribe'})
    try:
        result = response.json()
        text = result['transcript']
        if result.get('success') is False or not isinstance(text, str) or not text.strip() or len(text)>2000:
            raise ValueError()
        return text.strip()
    except (ValueError, KeyError, TypeError):
        raise ProviderError('Prisma returned an invalid or empty transcript') from None

def synthesize(text, language='en-IN'):
    if language not in VOICES or not isinstance(text, str) or not 1 <= len(text) <= 500:
        raise ValueError('Use a supported language and 1–500 characters')
    response = post('/api/v1/tts/inference', 'timbre-v2.5', 'synthesize', {'text_characters': len(text)},
                    json={'text': text, 'voice': VOICES[language], 'model': 'timbre-v2.5',
                          'language': language, 'speed': 1.0,
                          'audio_config': {'sample_rate': 16000, 'num_channels': 1, 'sample_width': 2,
                                           'encoding': 'linear_pcm', 'container': 'wav'}})
    audio = response.content
    try:
        # Observed live Timbre responses use an unfinished streaming WAV frame count.
        # Rebuild only that known header form; never weaken inbound audio validation.
        with wave.open(io.BytesIO(audio)) as wav:
            if wav.getnframes() in {2147483647, 4294967295}:
                pcm = wav.readframes(wav.getnframes())
                if len(pcm) % (wav.getnchannels()*wav.getsampwidth()):
                    raise ValueError('Truncated output sample')
                output = io.BytesIO()
                with wave.open(output, 'wb') as fixed:
                    fixed.setparams((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), 0, 'NONE', 'not compressed'))
                    fixed.writeframes(pcm)
                audio = output.getvalue()
        wav_info(audio)
    except (ValueError, wave.Error, EOFError):
        raise ProviderError('Timbre returned invalid WAV audio') from None
    return audio
