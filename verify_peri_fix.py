import sys
import os

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
import django
django.setup()

from chatbot.engine.responder import generate_response_advanced

def verify_peri():
    query = "peri bsc fees"
    print(f"\nTesting Query: '{query}'")
    
    # Mock history
    history = []
    
    try:
        response = generate_response_advanced(query, history)
        print(f"Detected Intent: {response.get('intent')}")
        print(f"Detected Type: {response.get('type')}")
        print(f"Response Message: {response.get('message', '')[:200]}...")
        
        if "PERI" in response.get('message', '') and "₹" in response.get('message', ''):
             print("✅ SUCCESS: PERI identified and fees returned!")
        else:
             print("❌ FAILURE: PERI not identified or fees missing.")
             print(f"Sources: {response.get('sources')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_peri()
