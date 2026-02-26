import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_shorthand_fees():
    print("\n--- Testing Shorthand Fees ('bsc cs fees in Sri Balaji') ---")
    query = "bsc cs fees in Sri Balaji"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if Sri Balaji was mapped
    assert "Sri Balaji Arts & Science College" in text or "sri-balaji" in response.get('sources', [])
    # Check if fees were found
    assert "Fee" in text
    assert "₹" in text
    print("✅ Shorthand fee test successful.")

def test_peri_shorthand():
    print("\n--- Testing Peri Shorthand ('peri bsc cs fees') ---")
    query = "peri bsc cs fees"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if Peri was mapped
    assert "Peri College" in text or "peri" in response.get('sources', [])
    # Check if fees were found
    assert "Fee" in text
    print("✅ Peri shorthand test successful.")

if __name__ == "__main__":
    try:
        test_shorthand_fees()
        test_peri_shorthand()
        print("\n✨ All shorthand verification tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
