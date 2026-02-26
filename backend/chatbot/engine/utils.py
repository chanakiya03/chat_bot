import re
import logging
import random as _random
from .loader import get_college_by_key, get_all_colleges
from chatbot.models import KnowledgeBaseQA
from spellchecker import SpellChecker

logger = logging.getLogger(__name__)

# Fast pre-built suggestions per intent
_FAST_SUGGESTIONS = {
    'fee': [
        "Which college is cheapest?", "Compare MBA fees", "Courses under ₹50K?",
        "B.Tech fees at HITS?", "Loyola M.A. Social Work fee?", "MCC B.Sc fees?",
        "Cheapest BCA college?", "SSN engineering fees", "Fee for Ph.D at Loyola?",
        "Compare Shift I and Shift II fees", "WCC B.Com fees?",
    ],
    'placement': [
        "Highest package at SSN?", "Top recruiters list", "Best CSE placements",
        "HITS placement percentage?", "Loyola placement stats", "Average package at MCC?",
        "BIHER placement record", "Which college has Amazon as recruiter?",
        "Top placement college for MBA?", "Guru Nanak placement data",
    ],
    'admission': [
        "Eligibility criteria?", "Merit vs counselling?", "Cutoff for engineering",
        "Admission process at HITS?", "Tamil Nadu counselling colleges",
        "Documents needed for admission?", "MCC admission mode?",
        "Which colleges accept NEET?", "Loyola B.Sc admission criteria",
    ],
    'hostel': [
        "Hostel for girls?", "Compare hostel facilities", "Which has boys hostel?",
        "HITS hostel fees?", "MCC hostel availability", "Loyola hostel details?",
        "SSN hostel for girls?", "Best hostel facilities?", "WCC hostel?",
    ],
    'about': [
        "NAAC A++ colleges?", "Autonomous colleges list", "Colleges on OMR",
        "Tell me about SSN", "History of MCC", "About BIHER?",
        "Loyola college type?", "What is HITS known for?", "Guru Nanak college info",
    ],
    'course': [
        "List all B.Tech courses", "Compare BCA fees", "Which offers MSW?",
        "MBA colleges in Chennai?", "MCC UG courses", "Data Science colleges?",
        "Ph.D programs in Loyola", "B.Com specializations at WCC", "Which offers B.Arch?",
        "Engineering courses at SSN", "M.Sc options at MCC",
    ],
    'ranking': [
        "Best for placements?", "Cheapest college?", "Top NAAC colleges",
        "Best MBA college?", "Top engineering college?", "Highest package college?",
        "Most affordable college?", "Best for computer science?", "Which has NBA accreditation?",
        "NAAC A++ colleges list", "Best autonomous college?",
    ],
    'comparison': [
        "Compare MCC vs Loyola", "HITS vs SSN fees", "Best for MBA",
        "BIHER vs HITS placement", "WCC vs MCC B.Com fees", "Guru Nanak vs MCC",
        "Loyola vs SSN ranking", "Cheapest between HITS and Loyola?",
        "Compare 3 colleges for BCA", "HITS vs BIHER hostel",
    ],
    'location': [
        "Colleges in Tambaram?", "Which is on OMR?", "Colleges in Egmore",
        "Colleges near T.Nagar?", "Nungambakkam colleges?", "Colleges in Adyar?",
        "Which colleges are in North Chennai?", "Colleges near Anna Nagar?",
    ],
    'facility': [
        "Which has coding lab?", "Hostel with Wi-Fi?", "Smart classrooms",
        "Library facilities at MCC?", "Sports complex at HITS?", "Medical center at SSN?",
        "Which college has gym?", "Campus size of Loyola?", "Labs at BIHER?",
    ],
}

# ─── Formatting Helpers ───────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Standardize course names for comparison (e.g. 'B.C.A' -> 'bca')."""
    if not text: return ""
    res = re.sub(r'[.\s\W]+', '', text.lower())
    return res

# 🚨 UPDATED: Added LL.M, B.Com, B.Arch to the translator
COURSE_ALIASES = {
    "b.sc": "bsc", "m.sc": "msc", 
    "b.com": "bcom", "m.com": "mcom",
    "b.tech": "btech", "m.tech": "mtech",
    "b.a": "ba", "m.a": "ma",
    "b.arch": "barch", "m.arch": "march",
    "ll.b": "llb", "ll.m": "llm", 
    "ph.d": "phd", "ph.d.": "phd"
}

def normalize_course_string(course_str: str) -> str:
    if not course_str: return ""
    clean = course_str.lower().strip()
    for typo, fix in COURSE_ALIASES.items():
        if typo in clean:
            clean = clean.replace(typo, fix)
    clean = re.sub(r'[\.\-\,]', '', clean)
    return " ".join(clean.split())

# 🚨 NEW: The Ultimate College Finder
def find_college_in_db(target_key: str, colleges_db: list) -> dict:
    if not target_key: return None
    tk = target_key.lower().strip()
    
    for c in colleges_db:
        # Support both 'key' and 'id' as per user request and existing structure
        c_id = str(c.get('key', c.get('id', ''))).lower()
        
        # Check both 'details' and 'college_details' for names
        details = c.get('college_details', c.get('details', {}))
        c_name = str(details.get('College Name', '')).lower()
        
        # Check standard ID or Name
        if tk == c_id or tk in c_name:
            # 🚨 Safety Alias: Ensure both keys exist so handlers don't crash
            if 'college_details' not in c: c['college_details'] = details
            if 'details' not in c: c['details'] = details
            return c
            
        # Hardcoded Safety Nets for tricky acronyms
        if tk == 'mcc' and 'madras christian' in c_name: 
            if 'college_details' not in c: c['college_details'] = details
            return c
        if tk == 'hits' and 'hindustan' in c_name:
            if 'college_details' not in c: c['college_details'] = details
            return c
        if tk == 'wcc' and 'women' in c_name and 'christian' in c_name:
            if 'college_details' not in c: c['college_details'] = details
            return c
        if tk == 'ssn' and 'ssn' in c_name:
            if 'college_details' not in c: c['college_details'] = details
            return c
        if tk == 'biher' and 'bharath' in c_name:
            if 'college_details' not in c: c['college_details'] = details
            return c
        if tk == 'peri' and 'peri' in c_name:
            if 'college_details' not in c: c['college_details'] = details
            return c
        
    return None
def _map_sources_to_names(keys: list) -> list:
    """Convert college slugs to friendly names for UI display."""
    names = []
    for k in keys:
        college = get_college_by_key(k)
        if college:
            names.append(college.get('details', {}).get('College Name', college['name']))
        else:
            names.append(str(k).replace('-', ' ').title())
    return list(set(names))

def get_standard_attribute(college: dict, attr: str) -> str:
    """
    Robustly extracts standard attributes (Fee, Placement, Hostel, etc.)
    from varying JSON structures.
    """
    details = college.get('college_details', college.get('details', {}))
    
    # 1. FEES
    if attr.lower() == 'fee':
        # Try explicit keys first
        for key in ['Fee Range', 'FEE STRUCTURE', 'FEE DATA', 'Annual Fees']:
            if details.get(key): return str(details[key])
        
        # Fallback: Calculate range from course list
        fees = [c.get('annual_fees_inr') for c in college.get('courses', []) if isinstance(c.get('annual_fees_inr'), (int, float))]
        if fees:
            return f"₹{min(fees):,} - ₹{max(fees):,}"
        return "N/A"

    # 2. PLACEMENT
    if attr.lower() == 'placement':
        for key in ['PLACEMENT DATA', 'Placement Statistics', 'Placement Percentage', 'Placements']:
            if details.get(key): return str(details[key]).split(',')[0] # Usually first part has the % or summary
        
        pkg = details.get('Average Package')
        if pkg: return f"Avg: {pkg}"
        return "N/A"

    # 3. HOSTEL
    if attr.lower() == 'hostel':
        for key in ['Hostel Available', 'HOSTEL FACILITIES', 'Hostel']:
            if details.get(key): return str(details[key])
        return "N/A"

    # Default fallback for other attributes
    return details.get(attr, "N/A")

def _format_ranking(ranked: list, course: str = None, custom_header: str = None) -> str:
    if not ranked: return "Could not compute or filter rankings for the given criteria."
    
    if custom_header:
        title = custom_header
    else:
        title = f"🏆 **Verified {course.upper() + ' ' if course else ''}College Rankings**"
        
    lines = [f"{title} _(based on placement, fees, packages)_\n"]
    for i, (score, college, info) in enumerate(ranked[:15], 1): # Show up to 15 in range/rank results
        name = college['details'].get('College Name', college['name'])
        
        # Determine Display Labels (Course-specific override)
        best_course = info.get('best_course_name')
        if best_course:
            fee_val = info.get('min_fee', info['avg_annual_fee'])
            fee_display = f"Course: {best_course} | Fee: ₹{fee_val:,.0f}"
        elif course:
            # If course was requested but we somehow don't have a best_match, skip this row
            continue
        else:
            fee_display = f"Avg Fee: ₹{info['avg_annual_fee']:,.0f}"
            
        lines.append(
            f"**{i}. {name}**  "
            f"_({fee_display}/yr | "
            f"Placement: {info['placement_pct']:.0f}% | "
            f"Pkg: {info['avg_package_lpa']:.1f} LPA)_"
        )
    return '\n'.join(lines)

def _format_comparison(college_keys: list, course: str = None) -> str:
    selected = [get_college_by_key(k) for k in college_keys if get_college_by_key(k)]
    if not selected: return "I couldn't find those colleges for comparison."

    label = f" ({course.upper()})" if course else ""
    # Build a properly terminated header + separator
    col_names = [c['details'].get('College Name', c['name']) for c in selected]
    header = "| Feature" + label + " | " + " | ".join(col_names) + " |"
    sep    = "|:--- |" + ":--- |" * len(selected)

    fields = [
        ('Type',         'Type'),
        ('Accreditation','Accreditation'),
        ('Placement %',  'PLACEMENT DATA'),
        ('Avg Package',  'Average Package'),
        ('Hostel',       'Hostel Available'),
        ('Location',     'Location'),
    ]

    rows = [header, sep]
    for row_label, key in fields:
        cells = " | ".join(str(c['details'].get(key, 'N/A')) for c in selected)
        rows.append(f"| **{row_label}** | {cells} |")

    # Fee range row (computed, not stored as a single field)
    def _fee_range(c):
        fees = [ci.get('annual_fees_inr') for ci in c.get('courses', [])
                if isinstance(ci.get('annual_fees_inr'), (int, float))]
        return f"₹{min(fees):,.0f} – ₹{max(fees):,.0f}" if fees else 'N/A'

    fee_cells = " | ".join(_fee_range(c) for c in selected)
    rows.append(f"| **Fee Range** | {fee_cells} |")

    if course:
        fee_row      = []
        duration_row = []
        for c in selected:
            found_course = None
            for ci in c.get('courses', []):
                db_string = f"{ci.get('course', '')} {ci.get('specialization', '')}".lower()
                if all(part in db_string for part in course.lower().split()):
                    found_course = ci
                    break
            if found_course:
                fee = found_course.get('annual_fees_inr', 'N/A')
                fee_row.append(f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee))
                duration_row.append(f"{found_course.get('duration_years', 'N/A')} yrs")
            else:
                fee_row.append("N/A")
                duration_row.append("N/A")
        rows.append(f"| **Fee ({course.upper()})** | " + " | ".join(fee_row) + " |")
        rows.append(f"| **Duration ({course.upper()})** | " + " | ".join(duration_row) + " |")

    return "\n".join(rows)

def _format_detailed_report(college: dict) -> str:
    details = college.get('details', {})
    courses = college.get('courses', [])
    lines = [f"# 🏛️ {college['name']} — Detailed Overview\n"]
    about = details.get('About', details.get('RANKING & REPUTATION', 'No description available.'))
    lines.append(f"> {about}\n")
    lines.append("### 📊 Quick Facts")
    lines.append("| Feature | Details |")
    lines.append("|:--- |:--- |")
    est = details.get('Established', 'N/A')
    if est == '[Year Not Provided]' or not est: est = 'N/A'
    lines.append(f"| **Established** | {est} |")
    lines.append(f"| **Type** | {details.get('Type', 'N/A')} |")
    lines.append(f"| **Accreditation** | {details.get('Accreditation', 'N/A')} |")
    lines.append(f"| **Location** | {details.get('Location', 'N/A')} |")
    lines.append("")
    if courses:
        lines.append("### 📚 Popular Courses")
        lines.append("| Course | Specialization | Duration | Fee (Annual) |")
        lines.append("|:--- |:--- |:--- |:--- |")
        for c in courses[:8]:
            fee = c.get('annual_fees_inr', 'N/A')
            fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
            lines.append(f"| {c.get('course', 'N/A')} | {c.get('specialization', 'N/A')} | {c.get('duration_years', 'N/A')} yrs | {fee_fmt} |")
    return "\n".join(lines)

def _format_fee_comparison(college_keys: list, course: str = None) -> str:
    selected = [get_college_by_key(k) for k in college_keys if get_college_by_key(k)]
    if not selected: return "I couldn't find those colleges for comparison."

    # ── CASE 1: No course specified → General side-by-side overview table ──
    if not course:
        names = [c['details'].get('College Name', c['name']) for c in selected]
        lines = ["💰 **Fee & Overview Comparison**\n"]

        # Build markdown table header dynamically
        header = "| Feature | " + " | ".join(names) + " |"
        sep    = "|:--- |" + ":--- |" * len(selected)
        lines += [header, sep]

        # Fee Range row
        def _fee_range(c):
            fees = [ci.get('annual_fees_inr') for ci in c.get('courses', [])
                    if isinstance(ci.get('annual_fees_inr'), (int, float))]
            if not fees: return 'N/A'
            return f"₹{min(fees):,.0f} – ₹{max(fees):,.0f}"

        lines.append("| **Fee Range** | " + " | ".join(_fee_range(c) for c in selected) + " |")

        # Accreditation row
        lines.append("| **Accreditation** | "
                     + " | ".join(c['details'].get('Accreditation', 'N/A') for c in selected) + " |")

        # Type row
        lines.append("| **Type** | "
                     + " | ".join(c['details'].get('Type', 'N/A') for c in selected) + " |")

        # Avg placement row
        lines.append("| **Avg Placement %** | "
                     + " | ".join(c['details'].get('PLACEMENT DATA', 'N/A') for c in selected) + " |")

        # Highest package row
        lines.append("| **Highest Package** | "
                     + " | ".join(c['details'].get('Average Package', 'N/A') for c in selected) + " |")

        # Hostel row
        lines.append("| **Hostel** | "
                     + " | ".join(c['details'].get('Hostel Available', 'N/A') for c in selected) + " |")

        lines.append("")
        lines.append("_💡 Ask about a specific course or metric to dive deeper, e.g. 'Compare BCA fees at SSN and HITS'._")
        return "\n".join(lines)

    # ── CASE 2: Course specified → per-college course table + direct winner ──
    title_course = f" — {course.upper()}"
    lines = [f"💰 **Fee Comparison{title_course}**\n"]
    for c in selected:
        name = c['name']
        courses_list = c.get('courses', [])
        norm_target = _normalize(course)
        kw_parts = norm_target.split() if norm_target else []
        courses_list = [
            ci for ci in courses_list
            if kw_parts and all(
                p in _normalize(f"{ci.get('course','')} {ci.get('specialization','')}")
                for p in kw_parts
            )
        ]
        if not courses_list:
            lines.append(f"### 🏫 {name}\n_No verified fee data for **{course.upper()}**._\n")
            continue
        lines.append(f"### 🏫 {name}")
        lines.append("| Course | Specialization | Annual Fee |")
        lines.append("|:--- |:--- |:--- |")
        for ci in courses_list[:10]:
            fee = ci.get('annual_fees_inr', 'N/A')
            fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
            lines.append(f"| {ci.get('course','N/A')} | {ci.get('specialization','—')} | {fee_fmt} |")
        lines.append("")

    # Direct winner summary
    if len(selected) >= 2:
        stats = []
        for c in selected:
            norm_target = _normalize(course)
            kw_parts = norm_target.split() if norm_target else []
            matches = [
                ci for ci in c.get('courses', [])
                if kw_parts and all(
                    p in _normalize(f"{ci.get('course','')} {ci.get('specialization','')}")
                    for p in kw_parts
                ) and isinstance(ci.get('annual_fees_inr'), (int, float))
            ]
            if matches:
                avg_f = sum(m['annual_fees_inr'] for m in matches) / len(matches)
                stats.append((c['name'], avg_f))
        if len(stats) >= 2:
            stats.sort(key=lambda x: x[1])
            cheap, pricey = stats[0], stats[-1]
            summary = (f"🎯 **Direct Answer**: **{cheap[0]}** is more affordable for **{course.upper()}** "
                       f"(₹{cheap[1]:,.0f}/yr vs ₹{pricey[1]:,.0f}/yr).")
            lines.insert(1, summary + "\n\n---\n")
    return "\n".join(lines)

def _format_college_directory() -> str:
    colleges = get_all_colleges()
    lines = ["## 🏛️ Comprehensive College Directory\n", "| College | Type | Location |", "|:--- |:--- |:--- |"]
    for c in sorted(colleges, key=lambda x: x['name']):
        details = c.get('details', {})
        lines.append(f"| **{c['name']}** | {details.get('Type', 'N/A')} | {details.get('Location', 'N/A').split(',')[0]} |")
    return "\n".join(lines)

def _format_course_table(college: dict, batch_filter: str = None, course_filter: str = None) -> str:
    details = college.get('details', {})
    courses = college.get('courses', [])
    
    # Apply batch filter (UG/PG)
    if batch_filter:
        courses = [c for c in courses if str(c.get('batch', '')).upper().startswith(batch_filter.upper())]
    
    # Apply course filter (e.g. "B.Com" or "btech ai and ml")
    if course_filter:
        tokens = normalize_course_string(course_filter).split()
        # Skip noise words to allow flexible matching like "ai and ml" -> "ai", "ml"
        noise = {'and', 'in', 'of', 'for', 'the', 'with', 'at'}
        tokens = [t for t in tokens if t.lower() not in noise]
        
        courses = [
            c for c in courses 
            if all(_normalize(t) in _normalize(f"{c.get('course', '')} {c.get('specialization', '')}") for t in tokens)
        ]
        
    if not courses: 
        msg = f"No verified information found for **{course_filter.upper() if course_filter else 'those courses'}** at {college['name']}."
        return msg

    lines = [f"🏛️ **{college['name']}** - Course Info\n", "| Course | Specialization | Annual Fee |", "|:--- |:--- |:--- |"]
    for c in courses[:25]:  # Limit to 25 rows to prevent message overflow
        fee = c.get('annual_fees_inr', 'N/A')
        fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
        lines.append(f"| {c.get('course', 'N/A')} | {c.get('specialization', '—')} | {fee_fmt} |")
    return "\n".join(lines)

# ─── Chennai Area Mapping ────────────────────────────────────────────────────
CHENNAI_AREA_MAP = {
    'omr': ['padur', 'kelambakkam', 'navalur', 'semmancheri', 'sholinganallur', 'siruseri', 'karapakkam', 'thuraipakkam', 'kalavakkam', 'chennai - 603110'],
    'ecr': ['kanathur', 'muttukadu', 'uithandi', 'injambakkam', 'neelankarai', 'palavakkam'],
    'gst': ['tambaram', 'chromepet', 'pallavaram', 'vandalur', 'potheri', 'kattankulathur', 'guduvanchery'],
}

# ─── Course Extraction ────────────────────────────────────────────────────────

def extract_course(query: str) -> str | None:
    """Extract course keyword + specialization from query.
    
    e.g. "mcc bsc mathematics fees" -> "b.sc mathematics"
         "bca fees" -> "bca"
         "ethiraj m com fees" -> "m.com"
         "engineering courses" -> "engineering"
    """
    q_norm = normalize_course_string(query)
    
    # Pre-process: collapse space-separated degree names
    # e.g. 'm com' -> 'mcom', 'b sc' -> 'bsc', 'b tech' -> 'btech'
    SPACE_DEGREE_MAP = {
        r'\bm\s+com\b': 'mcom', r'\bb\s+com\b': 'bcom',
        r'\bm\s+sc\b': 'msc', r'\bb\s+sc\b': 'bsc',
        r'\bb\s+tech\b': 'btech', r'\bm\s+tech\b': 'mtech',
        r'\bb\s+arch\b': 'barch', r'\bm\s+arch\b': 'march',
        r'\bb\s+ed\b': 'bed', r'\bm\s+ed\b': 'med',
        r'\bb\s+a\b': 'ba', r'\bm\s+a\b': 'ma',
    }
    for pat, replacement in SPACE_DEGREE_MAP.items():
        q_norm = re.sub(pat, replacement, q_norm)
    
    # Known specialization words to capture after a degree keyword
    SPECIALIZATIONS = [
        'mathematics', 'physics', 'chemistry', 'zoology', 'botany',
        'computer science', 'data science', 'statistics', 'psychology',
        'microbiology', 'biotechnology', 'biochemistry', 'nutrition',
        'visual communication', 'information technology', 'it',
        'ai', 'ml', 'ai & ml', 'ai & data science',
        'plant biology', 'radiology', 'medical',
        'general', 'honours', 'accounting', 'finance',
        'corporate secretaryship', 'bank management', 'marketing',
        'computer applications', 'business administration',
        'english', 'tamil', 'history', 'economics', 'political science',
        'philosophy', 'public administration', 'social work',
        'hrm', 'human resource management', 'communication',
        'mechanical', 'civil', 'aerospace', 'electrical',
        'cse', 'ece', 'eee', 'electronics',
        'nursing', 'pharmacy', 'architecture',
        'hospitality', 'tourism', 'physical education', 'yoga',
        'commerce', 'law',
    ]
    
    # Degree patterns: map regex -> canonical prefix
    degree_mapping = {
        r'\bbca\b': 'bca', r'\bbba\b': 'bba',
        r'\bbcom\b': 'b.com', r'\bmcom\b': 'm.com',
        r'\bmba\b': 'mba', r'\bmca\b': 'mca',
        r'\bbtech\b': 'b.tech', r'\bmtech\b': 'm.tech',
        r'\bbsc\b': 'b.sc', r'\bmsc\b': 'm.sc',
        r'\bba\b': 'b.a', r'\bma\b': 'm.a',
        r'\bbarch\b': 'b.arch', r'\bmarch\b': 'm.arch',
        r'\bme\b': 'm.e', r'\bbe\b': 'b.e',
        r'\bbed\b': 'b.ed', r'\bmed\b': 'm.ed',
        r'\bbpt\b': 'bpt', r'\bmpt\b': 'mpt',
        r'\bbpharm\b': 'b.pharm', r'\bmpharm\b': 'm.pharm',
        r'\bpharmd\b': 'pharm.d', r'\bpharm\s*d\b': 'pharm.d',
        r'\bmbbs\b': 'mbbs', r'\bbds\b': 'bds',
        r'\bbhms\b': 'bhms', r'\bbams\b': 'bams',
        r'\blaw\b': 'law', r'\bphd\b': 'phd'
    }
    
    for pat, degree in degree_mapping.items():
        m = re.search(pat, q_norm)
        if m:
            # Look for a specialization AFTER the degree in the normalized query
            after_degree = q_norm[m.end():].strip()
            # Remove noise words from the beginning
            after_degree = re.sub(r'^(in|of|for|the|at|and|with)\s+', '', after_degree, flags=re.I).strip()
            # Remove trailing noise (including comparison words, college names, etc.)
            after_degree = re.sub(
                r'\s+(fees?|cost|price|college|university|at|in|of|the|courses?|'
                r'details?|info|this|that|dataset|data|available|highest|lowest|'
                r'cheapest|most|expensive|average|more|than|compared|better|worse|'
                r'vs|versus|or|between|from|offered|provide|annual|per\s+year).*$',
                '', after_degree, flags=re.I
            ).strip()
            # Remove if after_degree is entirely a noise word or a known college alias
            from .router import ALIASES
            noise_only = {'this', 'that', 'here', 'all', 'any', 'our', 'your', 'their', 'its',
                          'more', 'less', 'which', 'what', 'how', 'much'}
            # Also treat known college aliases as noise (e.g., 'loyola', 'hits', 'mcc')
            college_aliases = set(ALIASES.keys())
            if after_degree.lower() in noise_only or after_degree.lower() in college_aliases:
                after_degree = ''
            # Also strip if after_degree starts with a known college name
            for alias in college_aliases:
                if after_degree.lower().startswith(alias):
                    after_degree = ''
                    break

            
            if after_degree:
                # Check if what remains is a known specialization
                for spec in SPECIALIZATIONS:
                    if after_degree.startswith(spec):
                        return f"{degree} {spec}"
                # Even if not in the list, if it's a meaningful word (>2 chars), include it
                first_word = after_degree.split()[0]
                if len(first_word) > 2 and first_word.isalpha():
                    return f"{degree} {first_word}"
            
            return degree
        
    # Generic course keywords (no degree prefix)
    generic_courses = ['hrm', 'economics', 'english', 'history', 'commerce', 'engineering', 'nursing', 'medical', 'physical education', 'yoga']
    for c in generic_courses:
        if re.search(rf'\b{re.escape(c)}\b', q_norm): return c
        
    return None

def detect_batch_filter(query: str) -> str | None:
    q = query.lower()
    if re.search(r'\bug\b|\bunder\s*grad\b', q): return 'UG'
    if re.search(r'\bpg\b|\bpost\s*grad\b', q): return 'PG'
    return None

def find_strict_qa_match(query: str):
    """Matches specific questions against KnowledgeBaseQA model."""
    q_lower = query.lower().strip()
    # 1. Exact match first
    match = KnowledgeBaseQA.objects.filter(question__iexact=q_lower, is_verified=True).first()
    if match: return match, 1.0
    
    # 2. Keyword fallback
    words = list(set(re.findall(r'\b\w{4,}\b', q_lower)))[:5]
    if not words: return None, 0
    qs = KnowledgeBaseQA.objects.filter(is_verified=True)
    for w in words:
        qs = qs.filter(question__icontains=w)
    candidate = qs.first()
    if candidate:
        qa_words = set(re.findall(r'\b\w{4,}\b', candidate.question.lower()))
        score = len(set(words) & qa_words) / max(len(words), 1)
        return (candidate, score) if score >= 0.8 else (None, 0)
    return None, 0

# ─── Query Auto-Correction ──────────────────────────────────────────────────

# Initialize the spell checker globally
_spell = SpellChecker()

# 🚨 CRITICAL: Teach the spell checker our special domain words!
# If we don't do this, it will try to "fix" your college acronyms.
CUSTOM_WORDS = [
    'ssn', 'hits', 'mcc', 'wcc', 'biher', 'peri', 'loyola', 'ethiraj',
    'gnc', 'balaji',
    'b.tech', 'm.tech', 'b.sc', 'm.sc', 'b.com', 'm.com', 'b.a', 'm.a',
    'bca', 'mca', 'bba', 'mba', 'll.b', 'll.m', 'ph.d', 'naac', 'nba',
    'btech', 'mtech', 'bsc', 'msc', 'bcom', 'mcom', 'barch', 'march',
    'bpt', 'mpt', 'mbbs', 'bds', 'bhms', 'bams', 'bpharm', 'mpharm',
    'bed', 'med', 'bsw', 'msw', 'phd', 'pharmd',
    'lpa', 'hostel', 'placement', 'placements', 'fees', 'syllabus',
    'tnea', 'neet', 'cheapest', 'costliest', 'autonomous',
]

# 🚨 HARD SKIP SET: Words that must NEVER be corrected, regardless of spell checker confidence.
# This catches cases where pyspellchecker's frequency dict overrides our custom words.
_SKIP_CORRECTION = {
    # College acronyms
    'ssn', 'hits', 'mcc', 'wcc', 'biher', 'peri', 'gnc', 'loyola', 'ethiraj', 'balaji',
    # Degree acronyms (the biggest source of corruption)
    'bca', 'mca', 'bba', 'mba', 'bsc', 'msc', 'bcom', 'mcom',
    'btech', 'mtech', 'barch', 'march', 'bpt', 'mpt', 'bed', 'med',
    'bsw', 'msw', 'mbbs', 'bds', 'bhms', 'bams', 'bpharm', 'mpharm',
    'phd', 'pharmd',
    # Domain terms
    'lpa', 'naac', 'nba', 'tnea', 'neet', 'ug', 'pg',
    'cse', 'ece', 'eee', 'mech', 'biomed', 'biotech',
    'hostel', 'placements', 'placement', 'cheapest', 'costliest',
    'autonomous', 'syllabus', 'fees',
}

# Load our custom words into the spell checker's dictionary
_spell.word_frequency.load_words(CUSTOM_WORDS)

def autocorrect_query(raw_query: str) -> str:
    """
    Takes a raw user query, fixes spelling mistakes, and returns the cleaned query.
    """
    if not raw_query:
        return ""
        
    # 1. Strip punctuation to isolate words (keep dots and pluses safe!)
    clean_text = re.sub(r'[^\w\s\.\+]', ' ', raw_query)
    
    # 2. Split into individual words
    words = clean_text.split()
    
    corrected_words = []
    for word in words:
        # Ignore numbers, single characters, or words with special symbols
        if word.isnumeric() or len(word) <= 1 or '.' in word or '+' in word:
            corrected_words.append(word)
            continue

        # 🚨 HARD SKIP: Never touch domain-specific acronyms
        if word.lower() in _SKIP_CORRECTION:
            corrected_words.append(word)
            continue
            
        # Find those words that may be misspelled
        misspelled = _spell.unknown([word.lower()])
        
        if misspelled:
            # Get the one `most likely` answer
            correction = _spell.correction(word.lower())
            # If correction is None (can't find a fix), keep the original word
            # Preserve original case if possible (simple heuristic)
            if correction:
                if word.isupper(): correction = correction.upper()
                elif word[0].isupper(): correction = correction.capitalize()
                corrected_words.append(correction)
            else:
                corrected_words.append(word)
        else:
            # Word is spelled correctly
            corrected_words.append(word)
            
    # Rejoin the corrected words into a single sentence
    return " ".join(corrected_words)

def suggest_refined_query(query: str, intent: str, context: list = None) -> list:
    """Return randomly shuffled suggestions from the pool for this intent."""
    if not query or len(query) < 5: return []
    pool = _FAST_SUGGESTIONS.get(intent, [
        "Tell me about courses", "Best colleges ranking", "Show overall directory",
        "Compare two colleges", "NAAC A++ colleges?", "Cheapest MBA college?",
    ])
    # Randomly pick 3
    pick = min(3, len(pool))
    return _random.sample(pool, pick)
