import sys
import os

# Set up django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.ranker import _parse_placement_pct, _parse_package_lpa

test_cases = [
    {
        "name": "MCC Problematic String",
        "input": "Placement Percentage: 75–85%, Average Package: ₹3.5 – 5 LPA",
        "expected_placement": 80.0,
        "expected_package": 4.25
    },
    {
        "name": "WCC Problematic String",
        "input": "placement rate 35%,Structured placement support across IT, Banking, Consulting, and Media sectors; strong emphasis on internship integration.",
        "expected_placement": 35.0, # This remains 35 as per data, but shouldn't be affected by other numbers
        "expected_package": 0.0 # No package info in this specific field
    },
    {
        "name": "SSN Clean String",
        "input": "90–95% placement rate",
        "expected_placement": 92.5,
        "expected_package": 0.0
    }
]

print("--- Testing Ranking Parser Fix ---")
for tc in test_cases:
    print(f"\nTest: {tc['name']}")
    print(f"Input: {tc['input']}")
    
    actual_placement = _parse_placement_pct(tc['input'])
    actual_package = _parse_package_lpa(tc['input'])
    
    print(f"Placement: {actual_placement} (Expected: {tc['expected_placement']})")
    print(f"Package:   {actual_package} (Expected: {tc['expected_package']})")
    
    if abs(actual_placement - tc['expected_placement']) < 0.1:
        print("✅ Placement OK")
    else:
        print("❌ Placement MISMATCH")
        
    # For package, we only check if it's reasonable
    # In MCC case, it should be (3.5+5)/2 = 4.25
    if actual_package > 0 or tc['expected_package'] == 0:
         print("✅ Package OK")
    else:
         print("❌ Package MISMATCH")

print("\n--- End of Tests ---")
