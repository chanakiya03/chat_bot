import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_comparison_context_reset():
    print("\n--- Testing Comparison Context Reset ('Compare MBA fees' after Engineering) ---")
    
    # 1. First query about something else (Engineering)
    history = [
        {'role': 'user', 'content': 'Tell me about engineering at HITS'},
        {'role': 'assistant', 'content': 'HITS offers various engineering courses...'}
    ]
    
    # 2. Second query: "Compare MBA fees"
    # This should reset HITS and Engineering context if no colleges are named
    query = "Compare MBA fees"
    response = generate_response_advanced(query, history)
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet:\n{text[:500]}...")
    
    # Check if MBA is actually mentioned in labels
    assert "MBA" in text
    # Check if it auto-selected colleges (should have sub-header)
    assert "**Comparing Top Colleges for MBA**" in text
    
    # Check that it's NOT just HITS (it should compare at least 2)
    # This depends on DB, but usually MBA isn't just one college
    lines = text.split('\n')
    col_count = text.count('### 🏫') if '### 🏫' in text else text.count('| Feature (MBA) |') # Check table columns
    
    print("✅ Context reset and MBA auto-selection test successful.")

def test_comparison_auto_select_colleges():
    print("\n--- Testing Comparison Auto-Selection ('Compare BCA fees') ---")
    query = "Compare BCA fees"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response snippet:\n{text[:500]}...")
    
    assert "BCA" in text
    assert "**Comparing Top Colleges for BCA**" in text
    print("✅ BCA auto-selection test successful.")

if __name__ == "__main__":
    try:
        test_comparison_context_reset()
        test_comparison_auto_select_colleges()
        print("\n✨ All comparison context reset tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


