
import os
import sys
import re

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat.settings')
django.setup()

# Mocking the _normalize function as it is internal if needed or just use the one in responder
from chatbot.engine.responder import extract_college_names, extract_course, detect_intent, _normalize

query = "ri balaji bca fees"
colleges = extract_college_names(query)
course = extract_course(query)
intent = detect_intent(query)

print(f"Query: {query}")
print(f"Detected Intent: {intent}")
print(f"Extracted Colleges: {colleges}")
print(f"Extracted Course: {course}")

# Test matching with normalization
from chatbot.engine.search import get_college_by_key
if colleges:
    col = get_college_by_key(colleges[0])
    if col:
        print(f"College found: {col['name']}")
        target_norm = _normalize(course)
        print(f"Target Normalized: '{target_norm}'")
        matches = []
        for ci in col.get('courses', []):
            c_name_norm = _normalize(ci.get('course', ''))
            c_spec_norm = _normalize(ci.get('specialization', ''))
            if target_norm in c_name_norm or target_norm in c_spec_norm:
                matches.append(ci)
        print(f"Course matches found: {[c['course'] for c in matches]}")
