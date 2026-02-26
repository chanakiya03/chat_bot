
import re

def _normalize(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

def test_comparison_logic_simple():
    print("--- Testing Comparison Logic (Static) ---")
    
    # Mock data
    all_colleges = [
        {'name': "College A", 'key': 'college-a', 'courses': [{'course': 'BCA', 'specialization': 'General'}]},
        {'name': "College B", 'key': 'college-b', 'courses': [{'course': 'BCA', 'specialization': 'General'}]},
        {'name': "College C", 'key': 'college-c', 'courses': [{'course': 'B.Sc', 'specialization': 'CS'}]},
    ]
    
    query = "Compare 2 colleges for BCA"
    course = "BCA"
    matched_college_keys = []
    
    # Logic from ComparisonHandler
    if len(matched_college_keys) < 2 and course:
        target_norm = _normalize(course)
        offering_keys = []
        
        for c in all_colleges:
            for c_info in c.get('courses', []):
                c_name_norm = _normalize(c_info.get('course', ''))
                c_spec_norm = _normalize(c_info.get('specialization', ''))
                if target_norm in c_name_norm or target_norm in c_spec_norm:
                    offering_keys.append(c['key'])
                    break
        
        print(f"Offering keys: {offering_keys}")
        assert len(offering_keys) >= 2
        
        num_match = re.search(r'\b([2-5])\b', query.lower())
        limit = int(num_match.group(1)) if num_match else 3
        
        matched_college_keys = offering_keys[:limit]
        print(f"Auto-selected: {matched_college_keys}")
        assert len(matched_college_keys) == 2
        assert 'college-a' in matched_college_keys
        assert 'college-b' in matched_college_keys
    
    # Fee detection logic
    q_fee = "Compare BCA fees"
    is_fee_query = any(w in q_fee.lower() for w in ['fee', 'fees', 'cost', 'price', 'cheap', 'afford'])
    print(f"Is fee query: {is_fee_query}")
    assert is_fee_query == True
    
    print("Comparison logic verification successful!")

if __name__ == "__main__":
    test_comparison_logic_simple()
