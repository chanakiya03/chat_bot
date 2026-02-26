import re

def _normalize(text: str) -> str:
    if not text: return ""
    return re.sub(r'[.\s\W]+', '', text.lower())

def normalize_course_string(course_str: str) -> str:
    if not course_str: return ""
    clean = course_str.lower().strip()
    clean = re.sub(r'[\.\-\,]', '', clean)
    return " ".join(clean.split())

def _format_course_table_logic(courses, course_filter=None):
    if course_filter:
        tokens = normalize_course_string(course_filter).split()
        noise = {'and', 'in', 'of', 'for', 'the', 'with', 'at'}
        tokens = [t for t in tokens if t.lower() not in noise]
        
        courses = [
            c for c in courses 
            if all(_normalize(t) in _normalize(f"{c.get('course', '')} {c.get('specialization', '')}") for t in tokens)
        ]
    return courses

# Mock data
courses = [
    {"course": "B.Tech Aeronautical Engineering", "specialization": "Aeronautical"},
    {"course": "B.Tech CSE (AI & ML – IBM)", "specialization": "AI & ML (IBM)"},
    {"course": "B.Tech Artificial Intelligence & Data Science", "specialization": "AI & DS"},
    {"course": "B.Sc Mathematics", "specialization": "Mathematics"}
]

print("Test 1: 'btech ai and ml'")
res = _format_course_table_logic(courses, "btech ai and ml")
for c in res: print(f" - {c['course']}")

print("\nTest 2: 'bsc math'")
res = _format_course_table_logic(courses, "bsc math")
for c in res: print(f" - {c['course']}")
