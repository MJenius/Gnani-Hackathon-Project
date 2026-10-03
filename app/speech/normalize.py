"""Conservative normalization: preserve names, numbers and code-mixed words."""
import unicodedata

def normalize(text):
    return ' '.join(unicodedata.normalize('NFC',text).replace('’',"'").split())
