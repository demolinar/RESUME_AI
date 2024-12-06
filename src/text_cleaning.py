import re
import string
from unidecode import unidecode

def clean_text(text):
    text = unidecode(text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = ''.join(filter(lambda x: x in string.printable, text))
    text = re.sub(r'\s+', ' ', text)
    symbols_to_remove = ['♂', '½', '±', '', '', '', 'Q', 'Ó', 'Ô', '', '', '', '±', '½', '']
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    return text.strip()
