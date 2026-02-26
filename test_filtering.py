"""Lightweight test: no Django required, just test pure functions."""
import re

# Copy of COURSE_ALIASES and normalize_course_string
COURSE_ALIASES = {
    "b.sc": "bsc", "m.sc": "msc", 
    "b.com": "bcom", "m.com": "mcom",
    "b.tech": "btech", "m.tech": "mtech",
    "b.a": "ba", "m.a": "ma",
    "b.arch": "barch", "m.arch": "march",
    "ll.b": "llb", "ll.m": "llm", 
    "ph.d": "phd", "ph.d.": "phd"
}

def normalize_course_string(course_str):
    if not course_str: return ""
    clean = course_str.lower().strip()
    for typo, fix in COURSE_ALIASES.items():
        if typo in clean:
            clean = clean.replace(typo, fix)
    clean = re.sub(r'[\.\-\,]', '', clean)
    return " ".join(clean.split())

SPECIALIZATIONS = [
    'mathematics', 'physics', 'chemistry', 'zoology', 'botany',
    'computer science', 'data science', 'statistics', 'psychology',
    'microbiology', 'biotechnology', 'biochemistry', 'nutrition',
    'visual communication', 'information technology', 'it',
    'ai', 'ml', 'ai & ml', 'ai & data science',
    'plant biology', 'radiology', 'medical',
    'general', 'honours', 'accounting', 'finance',
    'corporate secretaryship', 'bank management', 'marketing',
    'computer applications', 'business administration',
    'english', 'tamil', 'history', 'economics', 'political science',
    'philosophy', 'public administration', 'social work',
    'hrm', 'human resource management', 'communication',
    'mechanical', 'civil', 'aerospace', 'electrical',
    'cse', 'ece', 'eee', 'electronics',
    'nursing', 'pharmacy', 'architecture',
    'hospitality', 'tourism', 'physical education', 'yoga',
    'commerce', 'law',
]

def extract_course(query):
    q_norm = normalize_course_string(query)
    degree_mapping = {
        r'\bbca\b': 'bca', r'\bbcom\b': 'b.com', 
        r'\bmba\b': 'mba', r'\bmca\b': 'mca', r'\bbtech\b': 'b.tech', 
        r'\bmtech\b': 'm.tech', r'\bbsc\b': 'b.sc', r'\bmsc\b': 'm.sc', 
        r'\bme\b': 'm.e', r'\bbe\b': 'b.e',
        r'\blaw\b': 'law', r'\bphd\b': 'phd'
    }
    
    for pat, degree in degree_mapping.items():
        m = re.search(pat, q_norm)
        if m:
            after_degree = q_norm[m.end():].strip()
            after_degree = re.sub(r'^(in|of|for|the|at|and)\s+', '', after_degree, flags=re.I).strip()
            after_degree = re.sub(r'\s+(fees?|cost|price|college|university|at|in|of|the|courses?|details?|info).*$', '', after_degree, flags=re.I).strip()
            
            if after_degree:
                for spec in SPECIALIZATIONS:
                    if after_degree.startswith(spec):
                        return f"{degree} {spec}"
                first_word = after_degree.split()[0]
                if len(first_word) > 2 and first_word.isalpha():
                    return f"{degree} {first_word}"
            
            return degree
    
    generic_courses = ['hrm', 'economics', 'english', 'history', 'commerce', 'engineering', 'nursing', 'medical', 'physical education', 'yoga']
    for c in generic_courses:
        if re.search(rf'\b{re.escape(c)}\b', q_norm): return c
    return None

# ============== TESTS ==============
print("=" * 60)
print("TEST 1: extract_course captures specialization")
print("=" * 60)

test_cases = [
    ("mcc bsc Mathematics fees",       "b.sc mathematics"),
    ("MCC B.Sc fees",                   "b.sc"),
    ("bsc physics fee at loyola",       "b.sc physics"),
    ("B.Sc Mathematics [Aided] fee",    "b.sc mathematics"),
    ("bca fees",                        "bca"),
    ("mba colleges",                    "mba"),
    ("btech computer science fees",     "b.tech computer science"),
    ("m.sc data science at wcc",        "m.sc data science"),
    ("SSN engineering fees",            "engineering"),
    ("mcc bsc fees",                    "b.sc"),
    ("b.com honours fees at mcc",       "b.com honours"),
]

all_pass = True
for query, expected in test_cases:
    result = extract_course(query)
    status = "PASS" if result == expected else "FAIL"
    if result != expected:
        all_pass = False
    print(f"  [{status}] extract_course('{query}') = '{result}' (expected '{expected}')")

print(f"\n{'ALL TESTS PASSED!' if all_pass else 'SOME TESTS FAILED.'}")

print("\n" + "=" * 60)
print("TEST 2: Token matching simulation")
print("=" * 60)

course = "b.sc mathematics"
target_norm = normalize_course_string(course)
kw_parts = target_norm.split()
print(f"  Course: '{course}' -> tokens: {kw_parts}")

db_entries = [
    "B.Sc Mathematics [Aided] Mathematics Science",
    "B.Sc Statistics [Aided] Statistics Science",
    "B.Sc Physics [Aided] Physics Science",
    "B.Sc Mathematics [Self-Financed] Mathematics Science",
    "M.Sc Mathematics [Aided] Mathematics Science",
]

print(f"  Matching against DB entries:")
for entry in db_entries:
    db_norm = normalize_course_string(entry)
    matches = all(part in db_norm for part in kw_parts)
    label = "MATCH" if matches else "skip "
    print(f"    [{label}] '{entry}' -> norm='{db_norm}'")

print("\n  Expected: Only B.Sc entries with Mathematics should match.")
print("  (M.Sc Mathematics should NOT match because 'bsc' is not in 'msc mathematics')")
