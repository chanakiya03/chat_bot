import os
import django
import json
import logging
import sys

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.router import analyze_query_advanced

def debug_extraction(query):
    print(f"\n--- DEBUGGING QUERY: {query} ---")
    try:
        print("Starting analyze_query_advanced...")
        analysis = analyze_query_advanced(query, [])
        print("Success!")
        print(f"Intent: {analysis.intent}")
        print(f"Colleges: {analysis.raw_colleges}")
        print(f"Courses: {analysis.raw_courses}")
        print(f"Target Metric: {analysis.target_metric}")
        print(f"Metric Range: {analysis.metric_range}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_q = "What colleges have 70-85% placement?"
    debug_extraction(test_q)
