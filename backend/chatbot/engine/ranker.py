"""
Weighted College Ranking Algorithm.
Scores colleges based on composite criteria: affordability, placement,
average package, and accreditation quality.
"""
import re
from .loader import get_all_colleges


def _parse_placement_pct(placement_str: str) -> float:
    """Extract a numeric placement percentage from a string."""
    if not placement_str:
        return 0.0
    
    # Try high-confidence match: numbers followed by %
    matches = re.findall(r'(\d+)\s*%', placement_str)
    if matches:
        vals = [int(m) for m in matches if 0 <= int(m) <= 100]
        if vals:
            return sum(vals) / len(vals)
            
    # Fallback: look for "placement rate X" or "X% placement" or numbers in a likely range [40, 100]
    # to avoid picking up small package numbers like "3" or "5" from "3-5 LPA"
    nums = re.findall(r'\d+', placement_str)
    if nums:
        vals = [int(n) for n in nums if 40 <= int(n) <= 100] # Usually placement is > 40%
        if vals:
            return sum(vals) / len(vals)
            
    return 0.0


def _parse_package_lpa(pkg_str: str) -> float:
    """Extract average package in LPA from string."""
    if not pkg_str:
        return 0.0
    
    # Priority 1: Numbers followed by LPA/lpa
    matches = re.findall(r'([\d.]+)\s*(?:LPA|lpa|Lakh|Lakhs|Lacks)', pkg_str, re.I)
    if matches:
        vals = [float(m) for m in matches]
        return sum(vals) / len(vals)
        
    # Priority 2: Numbers after currency symbols
    matches = re.findall(r'(?:₹|Rs\.?)\s*([\d.]+)', pkg_str, re.I)
    if matches:
        vals = [float(m) for m in matches if float(m) < 100] # Cap to avoid huge absolute numbers
        if vals:
            return sum(vals) / len(vals)

    # Fallback to general numbers if they are small (typical LPA range)
    nums = re.findall(r'[\d.]+', pkg_str)
    if nums:
        vals = [float(n) for n in nums if 1.0 <= float(n) <= 50.0]
        return sum(vals) / len(vals) if vals else 0.0
        
    return 0.0


def _parse_accreditation_score(acc_str: str) -> float:
    """Score accreditation quality out of 10."""
    acc_lower = (acc_str or '').lower()
    score = 0.0
    if 'naac a++' in acc_lower:
        score = 10.0
    elif 'naac a+' in acc_lower:
        score = 9.0
    elif 'naac a' in acc_lower:
        score = 8.0
    elif 'naac b++' in acc_lower:
        score = 7.0
    elif 'naac b+' in acc_lower:
        score = 6.0
    elif 'naac b' in acc_lower:
        score = 5.0
    elif 'nba' in acc_lower or 'ugc' in acc_lower:
        score = 6.0
    elif 'na' in acc_lower or acc_lower == '':
        score = 2.0
    return score


def _parse_established_year(est_str: str) -> int:
    """Extract established year (e.g. '1837' or '1984 (University status: 2003)')."""
    if not est_str:
        return 9999  # Default to very new if unknown
    nums = re.findall(r'\d{4}', str(est_str))
    if nums:
        # Take the first 4-digit number as the founding year
        return int(nums[0])
    return 9999


def _avg_course_fee(courses: list) -> float:
    """Compute average annual fee across all courses."""
    fees = [c.get('annual_fees_inr', 0) for c in courses if isinstance(c.get('annual_fees_inr'), (int, float))]
    return sum(fees) / len(fees) if fees else 0.0


def rank_colleges(criteria: dict = None, college_keys: list = None, course_keyword: str = None, institution_type: str = None) -> list:
    """
    Rank colleges by a weighted composite score.

    criteria (all optional, defaults used if not specified):
        affordability_weight  (default 0.30)
        placement_weight      (default 0.35)
        package_weight        (default 0.25)
        accreditation_weight  (default 0.10)

    college_keys: if given, only rank those colleges.
    course_keyword: if given, only rank colleges offering this course and
                    use that course's fee for affordability score.
    institution_type: if given (e.g., "autonomous"), filter colleges by this type.

    Returns list of (score, college_entry, details_dict) sorted descending.
    """
    if criteria is None:
        criteria = {}

    w_afford = criteria.get('affordability_weight', 0.30)
    w_place = criteria.get('placement_weight', 0.35)
    w_pkg = criteria.get('package_weight', 0.25)
    w_acc = criteria.get('accreditation_weight', 0.10)

    colleges = get_all_colleges()
    if college_keys:
        colleges = [c for c in colleges if c['key'] in college_keys]

    if institution_type:
        type_norm = institution_type.lower()
        colleges = [c for c in colleges if type_norm in c['details'].get('Type', '').lower()]

    kw = course_keyword.lower() if course_keyword else None
    
    scored = []
    for college in colleges:
        details = college['details']
        courses = college['courses']
        
        # --- STRICT DOMAIN FILTERING ---
        col_type = details.get('Type', '').lower()
        
        # If looking for engineering, strictly ban non-engineering colleges
        if kw == 'engineering' and 'engineering' not in col_type and 'technology' not in col_type:
            continue
            
        # If looking for arts/science, ban strictly engineering colleges
        if kw in ['arts', 'science', 'commerce', 'b.sc', 'b.a', 'b.com']:
            if 'engineering' in col_type and 'arts' not in col_type and 'science' not in col_type:
                continue

        relevant_courses = courses
        if kw and kw != 'engineering': 
            kw_parts = kw.split()
            relevant_courses = []
            for c in courses:
                # MERGE the DB fields into one giant string
                db_string = f"{c.get('course', '')} {c.get('specialization', '')} {c.get('stream', '')}".lower()
                # Check if ALL parts of the user's keyword are inside this merged DB string
                if all(part in db_string for part in kw_parts):
                    relevant_courses.append(c)
            
            if not relevant_courses:
                continue
        elif kw == 'engineering':
            # Map "engineering" to B.E/B.Tech courses
            relevant_courses = [
                c for c in courses 
                if 'b.e' in c.get('course','').lower() 
                or 'b.tech' in c.get('course','').lower() 
                or 'm.e' in c.get('course','').lower() 
                or 'engineering' in c.get('stream', '').lower()
            ]
            if not relevant_courses: continue

        placement_pct = _parse_placement_pct(details.get('PLACEMENT DATA', ''))
        avg_pkg = _parse_package_lpa(details.get('Average Package', ''))
        acc_score = _parse_accreditation_score(details.get('Accreditation', ''))
        est_year = _parse_established_year(details.get('Established', ''))
        
        # Use average fee of relevant courses only
        avg_fee = _avg_course_fee(relevant_courses)
        
        # FIND MIN FEE COURSE for specific "Cheapest" queries
        # If a course is requested, we MUST use its specific fee for the affordability score
        min_course_fee = avg_fee
        best_course_name = None
        if relevant_courses:
            # Sort relevant courses by fee and pick the lowest non-zero
            valid_fees = [c for c in relevant_courses if isinstance(c.get('annual_fees_inr'), (int, float)) and c.get('annual_fees_inr') > 0]
            if valid_fees:
                best_c = min(valid_fees, key=lambda x: x['annual_fees_inr'])
                min_course_fee = best_c['annual_fees_inr']
                best_course_name = f"{best_c.get('course', '')} {best_c.get('specialization', '')}".strip()
            elif kw:
                # If course requested but NO fees found for it, effectively treat as infinite fee for ranking
                min_course_fee = 999999
        
        # Determine which fee to use for the affordability score
        # If a course was specified, use the specific course fee (min_course_fee)
        target_fee = min_course_fee if kw else avg_fee

        # Normalize to 0-10
        # Affordability: lower fee = higher score (invert), max ~300k/yr
        afford_score = max(0, (300000 - target_fee) / 300000 * 10)
        placement_score = min(placement_pct / 10, 10)
        pkg_score = min(avg_pkg, 10)  # LPA capped at 10

        composite = (
            w_afford * afford_score
            + w_place * placement_score
            + w_pkg * pkg_score
            + w_acc * acc_score
        )

        scored.append((
            round(composite, 3),
            college,
            {
                'placement_pct': placement_pct,
                'avg_package_lpa': avg_pkg,
                'avg_annual_fee': avg_fee,
                'min_fee': min_course_fee,
                'best_course_name': best_course_name,
                'accreditation_score': acc_score,
                'established_year': est_year,
                'composite_score': round(composite, 3),
                'matched_courses_count': len(relevant_courses)
            }
        ))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
