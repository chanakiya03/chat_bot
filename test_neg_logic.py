
import re

def test_logic(query):
    # Mock triggers and data as per responder.py
    _acc_triggers = {'naac a++': 'NAAC A++', 'nba': 'NBA'}
    _type_triggers = {'autonomous': 'Autonomous', 'deemed': 'Deemed'}
    
    q_lower = query.lower()
    matched_acc  = next((label for kw, label in _acc_triggers.items() if kw in q_lower), None)
    matched_type = next((label for kw, label in _type_triggers.items() if kw in q_lower), None)

    is_negative = False
    if matched_acc or matched_type:
        neg_pattern = r'\b(non|not|no)[-\s]+(?:' + '|'.join(list(_acc_triggers.keys()) + list(_type_triggers.keys())) + r')\b'
        if re.search(neg_pattern, q_lower):
            is_negative = True
            
    # Mock filtering function
    def check_college(details, matched_acc, matched_type, is_neg):
        acc_val = str(details.get('Accreditation', '')).upper()
        type_val = str(details.get('Type', '')).lower()
        
        acc_ok  = (not matched_acc)  or ((matched_acc.upper()  in acc_val) != is_neg)
        type_ok = (not matched_type) or ((matched_type.lower() in type_val) != is_neg)
        return acc_ok and type_ok

    college_hits = [
        {"name": "Loyola", "Accreditation": "NAAC A++", "Type": "Autonomous"},
        {"name": "HITS", "Accreditation": "NAAC A+", "Type": "Deemed"},
        {"name": "MCC", "Accreditation": "NAAC A++", "Type": "Autonomous"}
    ]
    
    hits = [c for c in college_hits if check_college(c, matched_acc, matched_type, is_negative)]
    return is_negative, hits

queries = [
    "Autonomous colleges list",
    "non Autonomous colleges list",
    "not NAAC A++ colleges"
]

for q in queries:
    is_neg, hits = test_logic(q)
    print(f"Query: {q}")
    print(f"Is Negative detected: {is_neg}")
    print(f"Hits: {[c['name'] for c in hits]}\n")

# Verify
_, non_auto_hits = test_logic("non Autonomous colleges list")
if "HITS" in [c['name'] for c in non_auto_hits] and "Loyola" not in [c['name'] for c in non_auto_hits]:
    print("✅ Logic Verified: 'non-Autonomous' works.")
else:
    print("❌ Logic Failed: 'non-Autonomous' logic is incorrect.")
