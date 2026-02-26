import re
from spellchecker import SpellChecker

# Re-implementing for standalone test due to Django setup issues
_spell = SpellChecker()
CUSTOM_WORDS = [
    'ssn', 'hits', 'mcc', 'wcc', 'biher', 'peri', 'loyola', 'ethiraj',
    'b.tech', 'm.tech', 'b.sc', 'm.sc', 'b.com', 'm.com', 'b.a', 'm.a',
    'bca', 'mca', 'bba', 'mba', 'll.b', 'll.m', 'ph.d', 'naac', 'nba',
    'lpa', 'hostel', 'placement', 'placements', 'fees', 'syllabus'
]
_spell.word_frequency.load_words(CUSTOM_WORDS)

def autocorrect_query(raw_query: str) -> str:
    if not raw_query: return ""
    clean_text = re.sub(r'[^\w\s\.\+]', ' ', raw_query)
    words = clean_text.split()
    corrected_words = []
    for word in words:
        if word.isnumeric() or len(word) <= 1 or '.' in word or '+' in word:
            corrected_words.append(word)
            continue
        misspelled = _spell.unknown([word.lower()])
        if misspelled:
            correction = _spell.correction(word.lower())
            if correction:
                if word.isupper(): correction = correction.upper()
                elif word[0].isupper(): correction = correction.capitalize()
                corrected_words.append(correction)
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)
    return " ".join(corrected_words)

if __name__ == "__main__":
    queries = [
        "wat is the placment feese at hits",
        "MCC admision criteria?",
        "Compare SSN and HITS for B.Tech",
        "What are the hostal facilities?"
    ]
    for q in queries:
        corrected = autocorrect_query(q)
        print(f"'{q}' -> '{corrected}'")
