"""Conservative normalization: preserve names, numbers and code-mixed words."""
import unicodedata
import re

def normalize(text):
    return ' '.join(unicodedata.normalize('NFC',text).replace('’',"'").split())

def fixture_key(text):
    """Finite demo matching, never discard names, constraints or unknown clauses."""
    text=normalize(text).lower()
    text=re.sub(r'\b(?:um|uh|erm)\b', ' ', text)
    text=re.sub(r'^\s*(?:(?:please|okay|ok)[,\s]+)+', '', text)
    for before,after in [('i am',"i'm"),('does not',"doesn't"),('four thirty','4:30'),
                         ('04:30','4:30'),('5 minutes','five minutes')]:
        text=text.replace(before,after)
    return ' '.join(text.translate(str.maketrans('', '', '.,!?;')).split())
