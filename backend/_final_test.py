import os
import sys
import django
import logging

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_query(query):
    print(f"\nTESTING: {query}")
    response = generate_response_advanced(query, [])
    print(f"Response: {response['text'][:500]}...")
    print("-" * 30)

test_query("hits btech ai and ml")
test_query("Compare MBA fees")
test_query("B.Tech fees at HITS?")
