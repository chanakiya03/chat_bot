import sys
import os

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
import django
django.setup()

from chatbot.engine.responder import generate_response_advanced

def verify_mcc():
    query = "mcc ug courses"
    print(f"\nTesting Query: '{query}'")
    
    # Mock history
    history = []
    
    try:
        response = generate_response_advanced(query, history)
        print(f"Detected Intent: {response.get('intent')}")
        print(f"Detected Type: {response.get('type')}")
        print(f"Response Snippet: {response.get('text', '')[:200]}...")
        
        if "Madras Christian College" in response.get('text', ''):
            print("✅ SUCCESS: Madras Christian College detected and courses retrieved!")
        else:
            print("❌ FAILURE: Madras Christian College NOT found in response.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_mcc()
