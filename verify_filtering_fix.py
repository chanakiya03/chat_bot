"""
Test Phase 15: Precise Fee & Course Filtering
Tests extract_course and normalize_course_string without Django/Groq.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')

# We need Django setup because utils.py imports from chatbot.models
import django
django.setup()

from chatbot.engine.utils import extract_course, normalize_course_string

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
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_pass = False
    print(f"  {status} extract_course('{query}') = '{result}' (expected '{expected}')")

print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")

print("\n" + "=" * 60)
print("TEST 2: normalize_course_string preserves tokens")
print("=" * 60)

norm_cases = [
    ("B.Sc Mathematics [Aided]",   "bsc mathematics [aided]"),
    ("B.Tech Computer Science & Engineering", "btech computer science & engineering"),
    ("M.Sc Data Science",          "msc data science"),
]

for raw, expected in norm_cases:
    result = normalize_course_string(raw)
    status = "✅" if result == expected else "❌"
    print(f"  {status} normalize('{raw}') = '{result}' (expected '{expected}')")

print("\n" + "=" * 60)
print("TEST 3: Token matching simulation")
print("=" * 60)

# Simulate what FeeHandler does
course = "b.sc mathematics"
target_norm = normalize_course_string(course)
kw_parts = target_norm.split()
print(f"  Course: '{course}' -> tokens: {kw_parts}")

# Sample DB entries  
db_entries = [
    "B.Sc Mathematics [Aided] Mathematics Science",
    "B.Sc Statistics [Aided] Statistics Science",
    "B.Sc Physics [Aided] Physics Science",
    "B.Sc Mathematics [Self-Financed] Mathematics Science",
]

for entry in db_entries:
    db_norm = normalize_course_string(entry)
    matches = all(part in db_norm for part in kw_parts)
    status = "✅ MATCH" if matches else "   skip"
    print(f"  {status}: '{entry}' -> norm='{db_norm}'")

print("\nExpected: Only 'Mathematics' entries should match.")
