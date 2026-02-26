
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.ranker import rank_colleges
from chatbot.engine.loader import get_all_colleges
from chatbot.engine.responder import _extract_course_keyword

def debug_ranking():
    query = "Best college for placement?"
    print(f"Query: {query}")
    
    colleges = get_all_colleges()
    print(f"Total colleges loaded: {len(colleges)}")
    for c in colleges:
        print(f" - {c['name']} ({c['key']}) | courses: {len(c['courses'])}")

    kw = _extract_course_keyword(query)
    print(f"Extracted keyword: '{kw}'")
    
    criteria = {'affordability_weight': 0.15, 'placement_weight': 0.55,
                'package_weight': 0.25, 'accreditation_weight': 0.05}
    
    print("\nRunning rank_colleges(criteria, course_keyword=kw)...")
    ranked = rank_colleges(criteria, course_keyword=kw)
    print(f"Ranked results: {len(ranked)}")
    
    if not ranked:
        print("!!! Ranking returned nothing !!!")
        
    for i, (score, college, info) in enumerate(ranked[:3], 1):
        print(f"{i}. {college['name']} | Score: {score}")

if __name__ == "__main__":
    debug_ranking()
