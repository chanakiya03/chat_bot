
import os
import sys
import re

# isolated test for intent and college extraction
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import detect_intent, extract_college_names, extract_course

query = "Which college is cheaper for M.A. HRM, Ethiraj or WCC?"
print(f"Query: {query}")
print(f"Intent: {detect_intent(query)}")
print(f"Colleges: {extract_college_names(query)}")
print(f"Course: {extract_course(query)}")

# Check WCC acronym generation
from chatbot.engine.loader import get_all_colleges
all_c = get_all_colleges()
wcc = next((c for c in all_c if "Women's Christian College" in c['name']), None)
if wcc:
    print(f"\nWCC Name: {wcc['name']}")
    name = wcc['name'].lower().replace("’", "").replace("'", "")
    name_clean = re.sub(r'[()]', ' ', name)
    name_parts = [n.strip() for n in name_clean.split() if n.strip()]
    COLLEGE_STOPWORDS = {
        'college', 'university', 'institute', 'arts', 'science', 'technology',
        'management', 'engineering', 'research', 'higher', 'education',
        'for', 'and', 'the', 'with', 'about', 'from', 'near', 'in', 'of',
        'women', 'womens', 'men', 'mens', 'co-educational', 'coeducational'
    }
    sig_parts = [p for p in name_parts if p not in COLLEGE_STOPWORDS]
    acronym = ''.join(w[0] for w in sig_parts if len(w) > 1)
    print(f"Name Parts: {name_parts}")
    print(f"Sig Parts: {sig_parts}")
    print(f"Generated Acronym: {acronym}")
