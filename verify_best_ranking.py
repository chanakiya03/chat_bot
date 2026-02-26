
import os
import sys

# isolated test for semantic ranking fix
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response

def test_best_ranking():
    query = "Which is the best college for B.Tech?"
    print(f"\nQuery: {query}")
    try:
        response = generate_response(query)
        print("-" * 30)
        print(f"Bot Response Snippet:\n{response['text'][:500]}...")
        print(f"Intent: {response.get('intent')}")
        print(f"Type: {response.get('type')}")
        
        # Check if BIHER or similar high-package colleges are at the top
        if "BIHER" in response['text'][:300] or "Bharath" in response['text'][:300]:
            print("✅ SUCCESS: BIHER/Bharath is ranked high based on Package/Placement outcomes.")
        else:
            print("⚠️ WARNING: Check if the ranking still prioritizes low fees over ROI.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

test_best_ranking()
