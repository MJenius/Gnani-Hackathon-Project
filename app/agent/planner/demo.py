import re

def extract(transcript):
    text = transcript.lower()
    # ponytail: narrow English demo parser; verified Evon replaces it for general missions.
    match = re.fullmatch(r"\s*(?:tell|notify) ananya (?:that )?(?:i am|i'm|i’m) (\d{1,3}) minutes? late[.!]?\s*", text)
    if not match or not 1 <= int(match[1]) <= 120:
        return None
    return {'contact': 'Ananya', 'delay_minutes': int(match[1])}
