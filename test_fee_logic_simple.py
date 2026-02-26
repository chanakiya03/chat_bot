
import re

class MockQueryAnalysis:
    def __init__(self, intent, raw_courses):
        self.intent = intent
        self.raw_courses = raw_courses
        self.is_comparison = False

def _normalize(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

def test_sorting_and_filtering():
    print("--- Testing Fee Logic (Static) ---")
    
    # Mock data
    matches = [
        ({'name': "College A"}, {'course': "B.Sc", 'specialization': "Computer Science", 'annual_fees_inr': 40000}),
        ({'name': "College B"}, {'course': "B.Tech", 'specialization': "Computer Science", 'annual_fees_inr': 150000}),
        ({'name': "College C"}, {'course': "B.Sc", 'specialization': "Information Technology", 'annual_fees_inr': 35000}),
    ]
    
    q_lower = "cheapest b.sc cs college"
    course = "B.Sc CS"
    
    # Logic from handlers.py
    target_norm = _normalize(course)
    filtered = []
    for c, c_info in matches:
        c_name_norm = _normalize(c_info.get('course', ''))
        c_spec_norm = _normalize(c_info.get('specialization', ''))
        
        # Strict degree matching
        if 'bsc' in q_lower.replace('.', '') and ('btech' in c_name_norm or 'be' in c_name_norm):
            continue
        filtered.append((c, c_info))
    
    print(f"Filtered count: {len(filtered)} (Expected 2, B.Tech should be gone)")
    assert len(filtered) == 2
    
    # Sorting
    filtered.sort(key=lambda x: x[1]['annual_fees_inr'])
    print(f"Cheapest: {filtered[0][0]['name']} (Expected College C, fee 35000)")
    assert filtered[0][0]['name'] == "College C"
    
    print("Logic verification successful!")

if __name__ == "__main__":
    test_sorting_and_filtering()
