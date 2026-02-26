import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_dynamic_greeting():
    print("\n--- Testing Dynamic Greeting ---")
    query = "hi"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Response:\n{text}")
    
    # Assertions
    assert "Hello! I'm CollegeBot" in text
    assert "- Madras Christian College" in text or "- SSN College of Engineering" in text
    assert "- Hindustan Institute of Technology and Science" in text
    
    print("\n✅ Dynamic Greeting test passed!")

if __name__ == "__main__":
    try:
        test_dynamic_greeting()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
