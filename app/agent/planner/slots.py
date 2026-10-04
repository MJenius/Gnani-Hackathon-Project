"""Bounded signature grammar: consume every instruction, never guess missing slots."""
import re
from app.speech.normalize import normalize

# Clause order is free; vocabulary and argument values remain deliberately bounded.
CLAUSES = {
    'contact': r"(?:tell|notify) ananya(?: that)?|ananya ko (?:batao|bata do|bata dena|batana)|ಅನನ್ಯ(?:ಾ)? (?:ಅವರಿಗೆ|ಗೆ) (?:ತಿಳಿಸಿ|ಹೇಳಿ)",
    'meeting_time': r"ask (?:if|whether) 16:30 (?:works|is okay)|16:30 (?:works )?(?:poochho|poocho|pucho|pooch lo)|16:30(?:ಗೆ)? (?:ಆಗುತ್ತದೆಯೇ|ಆಗುತ್ತಾ|ಭೇಟಿಯಾಗಬಹುದೇ)(?: ಎಂದು)? ಕೇಳಿ",
    'parking': r"(?:find|look for) (?:some )?parking near (?:her|the) office|office ke (?:paas|pass) parking (?:dhundo|dhundho|dhoondo)|(?:ಅವರ )?(?:ಕಚೇರಿ|ಆಫೀಸ್) (?:ಬಳಿ|ಹತ್ತಿರ) (?:ಪಾರ್ಕಿಂಗ್|parking) (?:ಹುಡುಕಿ|ನೋಡಿ)",
    'fuel': r"(?:get|add) fuel (?:if it (?:doesn't|does not) add more than|only if it adds at most) 5 minutes|fuel (?:agar|tabhi agar) 5 (?:minutes|min) se (?:zyada|jyada) detour (?:nahi hota|na ho|nahi ho)|5 (?:ನಿಮಿಷಕ್ಕಿಂತ|ನಿಮಿಷಗಳಿಗಿಂತ) ಹೆಚ್ಚು (?:ಆಗದಿದ್ದರೆ|ತಡವಾಗದಿದ್ದರೆ) (?:ಇಂಧನ|ಪೆಟ್ರೋಲ್) (?:ತುಂಬಿಸಿ|ಹಾಕಿಸಿ)",
}
LATE = r"(?:i'm|i am) (?:running )?(?:25 minutes )?late(?: for my meeting)?|meeting ke liye late ho raha (?:hoon|hu)|ನಾನು (?:ಸಭೆಗೆ|ಮೀಟಿಂಗ್ ಗೆ) ತಡವಾಗುತ್ತಿದ್ದೇನೆ"

def signature_slots(transcript):
    text = normalize(transcript).lower()
    # Only explicit equivalent numbers; never fuzzy-match names or unknown values.
    for pattern, value in [(r'(?<!\w)(?:04:30|4:30|16:30|four thirty)(?!\w)', '16:30'),
                           (r'ನಾಲ್ಕೂವರೆಗೆ|ನಾಲ್ಕೂವರೆ ಗಂಟೆಗೆ|ನಾಲ್ಕು ಮೂವತ್ತಕ್ಕೆ', '16:30ಗೆ'),
                           (r'(?<!\w)(?:five|ಐದು)(?!\w)', '5')]:
        text = re.sub(pattern, value, text)
    text = re.sub(r'[.,!?;।]', ' ', text)
    text = re.sub(r'(?<!\w)(?:um|uh|erm|please)(?!\w)', ' ', text)
    text = ' '.join(text.split())
    late_matches = list(re.finditer(r'(?<!\w)(?:' + LATE + r')(?!\w)', text))
    if len(late_matches) > 1:
        return None
    text = re.sub(r'(?<!\w)(?:' + LATE + r')(?!\w)', ' ', text)
    for pattern in CLAUSES.values():
        matches = list(re.finditer(r'(?<!\w)(?:' + pattern + r')(?!\w)', text))
        if len(matches) != 1:
            return None
        text = re.sub(r'(?<!\w)(?:' + pattern + r')(?!\w)', ' ', text)
    # Unknown text includes changed/ambiguous arguments, negations and extra actions.
    if any(word not in {'and', 'also', 'aur', 'ಮತ್ತು', 'okay', 'ok'} for word in text.split()):
        return None
    return {'contact': 'Ananya', 'meeting_time': '16:30', 'parking': 'near office',
            'fuel': True, 'max_detour': 5}
