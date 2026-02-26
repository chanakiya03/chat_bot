
import re

def extract_course(query):
    q_lower = query.lower()
    typo_map = {
        r'\bb\.?sc\b': 'b.sc',
        r'\bm\.?sc\b': 'm.sc',
        # MISSING M.A.
    }
    _spec_keywords = [
        ('hrm|human resource', 'hrm'),
    ]
    _broad_prefixes = {'m.a', 'b.a', 'b.sc', 'm.sc'}
    
    # Simulating the logic
    for pattern, rep in typo_map.items():
        if re.search(pattern, q_lower):
            broad = rep
            print(f"Matched broad: {broad}")
            if broad.lower().rstrip('.') in {b.rstrip('.') for b in _broad_prefixes}:
                for spec_pat, spec_rep in _spec_keywords:
                    if re.search(spec_pat, q_lower):
                        return spec_rep
            return broad
    
    multi_courses = [('human resource management', 'hrm')]
    for pattern, rep in multi_courses:
        if re.search(pattern, q_lower):
            return rep
            
    return None

def extract_college_names(query):
    all_colleges = [
        {'key': 'mcc', 'name': 'Madras Christian College (MCC)'},
        {'key': 'ethiraj', 'name': 'Ethiraj College for Women'},
        {'key': 'wcc', 'name': 'Women\'s Christian College (WCC)'}
    ]
    q_lower = query.lower()
    q_norm = q_lower.replace("’", "").replace("'", "")
    q_clean = re.sub(r'[,;/]+', ' ', q_norm)
    q_clean = re.sub(r'[^\w\s]', ' ', q_clean)
    
    COLLEGE_STOPWORDS = {'college', 'university', 'and', 'the', 'for', 'women', 'womens', 'in', 'of'}
    scores = {}
    
    for college in all_colleges:
        name = college['name'].lower().replace("’", "").replace("'", "")
        name_clean = re.sub(r'[()]', ' ', name)
        name_parts = [n.strip() for n in name_clean.split() if n.strip()]
        sig_parts = [p for p in name_parts if p not in COLLEGE_STOPWORDS]
        
        score = 0
        if re.search(rf'\b{re.escape(college["key"])}\b', q_clean):
            score = 100
            
        acronym_parts = [p for p in name_parts if p not in COLLEGE_STOPWORDS]
        acronym = ''.join(w[0] for w in acronym_parts if len(w) > 0)
        if len(acronym) >= 2 and f" {acronym} " in f" {q_clean} ":
            score = max(score, 90)
            
        matched_sig_parts = 0
        for part in sig_parts:
            if re.search(rf'\b{re.escape(part)}\b', q_clean):
                matched_sig_parts += 1
        
        if sig_parts:
            score = max(score, int((matched_sig_parts / len(sig_parts)) * 80))
            
        scores[college['key']] = score
        print(f"College: {college['key']}, Score: {score}, Sig Parts: {sig_parts}, Matched Parts: {matched_sig_parts}")

    return scores

query = "Which college is cheaper for M.A. HRM, Ethiraj or WCC?"
print(f"Testing Query: {query}")
scores = extract_college_names(query)
print(f"Course: {extract_course(query)}")
