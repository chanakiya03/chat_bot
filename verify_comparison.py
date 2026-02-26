import sys
import os

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
import django
django.setup()

from chatbot.engine.responder import generate_response_advanced

def verify_comparison():
    query = "compare hits and mcc"
    print(f"\nTesting Query: '{query}'")
    
    # Mock history
    history = []
    
    try:
        response = generate_response_advanced(query, history)
        print(f"Detected Intent: {response.get('intent')}")
        print(f"Detected Type: {response.get('type')}")
        print(f"Response Table:\n{response.get('message', '')}")
        
        table = response.get('message', '')
        if "| Fees |" in table and "N/A" not in table:
             print("✅ SUCCESS: Comparison table shows valid data!")
        else:
             print("❌ FAILURE: Comparison table still contains N/A or is missing rows.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_comparison()
