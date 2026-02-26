import os
import sys
import django
import logging

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

from chatbot.engine.responder import generate_response_advanced
from chatbot.engine.router import detect_intent, extract_colleges, ALIASES
from chatbot.engine.utils import extract_course

def trace_query(query):
    print(f"\n{'#'*60}")
    print(f"TRACING: {query}")
    print(f"{'#'*60}")
    
    q_lower = query.lower()
    intent = detect_intent(q_lower)
    colleges = extract_colleges(query, ALIASES)
    course = extract_course(query)
    
    print(f"Intent detected (router): {intent}")
    print(f"Colleges extracted: {colleges}")
    print(f"Course extracted: {course}")
    
    try:
        response = generate_response_advanced(query, [])
        print(f"\nResponse Type: {response.get('type')}")
        print(f"Response Intent: {response.get('intent')}")
        print(f"Response Text (start): {response.get('text', '')[:150]}...")
        
        if '_meta' in response:
            print(f"Meta Intent: {response['_meta'].get('intent')}")
            print(f"Meta Colleges: {response['_meta'].get('colleges_matched')}")
            
    except Exception as e:
        print(f"ERROR: {e}")

trace_query("B.Tech fees at HITS?")
trace_query("Compare MBA fees")
