
import re

# Simulate the data structure
colleges = [
    {
        'name': 'Ethiraj College for Women',
        'details': {'Location': 'Egmore, Chennai – 600008, Tamil Nadu, India'}
    },
    {
        'name': 'Loyola College',
        'details': {'Location': 'Nungambakkam, Chennai – 600034, Tamil Nadu, India'}
    }
]

# Simulate current responder.py logic
query = "Colleges in Egmore"
q_lower = query.lower()

target_loc = None
location_match = re.search(r'\bin\s+([a-zA-Z\s]+)\b', query, re.IGNORECASE)
if location_match:
    target_loc = location_match.group(1).strip().lower()

print(f"Extracted target_loc: {target_loc}")

if target_loc:
    noise_words = ['the', 'area', 'city', 'district', 'near', 'around', 'region', 'locality', 'part of', 'colleges', 'college']
    for word in noise_words:
        target_loc = re.sub(rf'\b{word}\b', '', target_loc).strip()
    
    print(f"Cleaned target_loc: {target_loc}")
    
    found_colleges = []
    for c in colleges:
        loc_str = c.get('details', {}).get('Location', '').lower()
        if target_loc in loc_str:
            found_colleges.append(c)

    print(f"Found: {[f['name'] for f in found_colleges]}")
