
import re

def extract_college_names_mock(query, colleges):
    found = []
    q_lower = query.lower()
    q_clean = re.sub(r'[,;/]+', ' ', q_lower)
    q_clean = re.sub(r'[^\w\s]', ' ', q_clean)
    
    COLLEGE_STOPWORDS = {
        'college', 'university', 'institute', 'arts', 'science', 'technology',
        'management', 'engineering', 'research', 'higher', 'education',
        'for', 'and', 'the', 'with', 'about', 'from', 'near', 'in', 'of'
    }

    for college in colleges:
        name_clean = re.sub(r'[()]', ' ', college['name'].lower())
        name_parts = [n.strip() for n in name_clean.split() if n.strip()]

        matched = False
        for part in name_parts:
            if part in COLLEGE_STOPWORDS:
                continue
            if (len(part) >= 2 and part.isalnum()) or len(part) > 3:
                if re.search(rf'\b{re.escape(part)}\b', q_clean):
                    found.append(college['key'])
                    matched = True
                    break
    return found

colleges = [
    {'key': 'ethiraj', 'name': 'Ethiraj College for Women'},
    {'key': 'wcc', 'name': 'Women’s Christian College (WCC)'}
]

query = "Ethiraj College for Women details"
print(f"Query: {query}")
print(f"Results (Original): {extract_college_names_mock(query, colleges)}")

def extract_college_names_fixed(query, colleges):
    found = []
    q_lower = query.lower()
    # Normalize women's -> womens
    q_lower = q_lower.replace("’", "").replace("'", "")
    q_clean = re.sub(r'[,;/]+', ' ', q_lower)
    q_clean = re.sub(r'[^\w\s]', ' ', q_clean)
    
    COLLEGE_STOPWORDS = {
        'college', 'university', 'institute', 'arts', 'science', 'technology',
        'management', 'engineering', 'research', 'higher', 'education',
        'for', 'and', 'the', 'with', 'about', 'from', 'near', 'in', 'of',
        'women', 'womens', 'men', 'mens', 'co-educational', 'coeducational'
    }

    for college in colleges:
        name_clean = college['name'].lower().replace("’", "").replace("'", "")
        name_clean = re.sub(r'[()]', ' ', name_clean)
        name_parts = [n.strip() for n in name_clean.split() if n.strip()]

        matched = False
        for part in name_parts:
            if part in COLLEGE_STOPWORDS:
                continue
            if (len(part) >= 2 and part.isalnum()) or len(part) > 3:
                if re.search(rf'\b{re.escape(part)}\b', q_clean):
                    found.append(college['key'])
                    matched = True
                    break
    return found

print(f"Results (Fixed): {extract_college_names_fixed(query, colleges)}")
