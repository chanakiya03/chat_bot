import json
import logging
import re
import pkg_resources
from pydantic import BaseModel, Field
from typing import List, Optional
from rapidfuzz import process, fuzz
from symspellpy import SymSpell, Verbosity
from .loader import get_all_colleges, get_college_by_key
from .groq_client import ask_groq_json

logger = logging.getLogger(__name__)

# Explicit high-confidence mappings for acronyms and common aliases
ALIASES = {
    'wcc': 'womens-christian-college-wcc',
    'women christian college': 'womens-christian-college-wcc',
    'mcc': 'madras-christian-college-mcc',
    'madras christian college': 'madras-christian-college-mcc',
    'ssn': 'ssn-college-of-engineering',
    'hits': 'hindustan-institute-of-technology-and-science-hits',
    'hindustan': 'hindustan-institute-of-technology-and-science-hits',
    'gnc': 'guru-nanak-college',
    'guru nanak': 'guru-nanak-college',
    'peri': 'peri-college-of-arts-and-science',
    'loyola': 'loyola-college',
    'ethiraj': 'ethiraj-college-for-women',
    'biher': 'bharath-institute-of-higher-education-and-research-biher',
    'bharath': 'bharath-institute-of-higher-education-and-research-biher',
    'sri balaji': 'sri-balaji-arts-science-college',
    'balaji': 'sri-balaji-arts-science-college'
}

# Mapping for degree formats that often contain dots or unusual punctuation
TRICKY_DEGREE_ALIASES = {
    "ll.b": "law",
    "llb": "law",
    "ph.d": "phd",
    "ph.d.": "phd",
    "m.e.": "me",
    "b.a.": "ba",
    "b.sc": "bsc",
    "m.sc": "msc"
}

# Common typos and shorthand misspellings
TYPO_MAP = {
    'hit': 'hits',
    'its': 'hits',  # Handled contextually in pre_process_query
    'hitz': 'hits',
    'sssn': 'ssn',
    'snn': 'ssn',
    'mccc': 'mcc',
    'wccc': 'wcc',
    'perii': 'peri',
    'pery': 'peri',
    'loyolaa': 'loyola',
    'loyolla': 'loyola',
    # Fee superlative typos
    'lowes': 'lowest',
    'lowst': 'lowest',
    'loweet': 'lowest',
    'cheepest': 'cheapest',
    'chepest': 'cheapest',
    'cheapeast': 'cheapest',
    'expensiv': 'expensive',
    'expencive': 'expensive',
    'afforable': 'affordable',
    'affordble': 'affordable',
    # Course typos
    'cources': 'courses',
    'coures': 'courses',
    'coursees': 'courses',
    'cousers': 'courses',
    'coruses': 'courses',
}

# ---------------------------------------------------------------------------
# Course Abbreviation Aliases
# Maps common acronyms/abbreviations to their full DB equivalents.
# These are expanded BEFORE LLM + fuzzy matching so 'bsc cs' finds 'Computer Science'.
# ---------------------------------------------------------------------------
COURSE_ALIASES: dict = {
    r'\bcs\b': 'Computer Science',
    r'\bit\b': 'Information Technology',
    r'\bai\b': 'Artificial Intelligence',
    r'\bml\b': 'Machine Learning',
    r'\bds\b': 'Data Science',
    r'\bece\b': 'Electronics and Communication',
    r'\beee\b': 'Electrical and Electronics',
    r'\bmech\b': 'Mechanical Engineering',
    r'\bcivil\b': 'Civil Engineering',
    r'\bbiomed\b': 'Biomedical Engineering',
    r'\bbiotech\b': 'Biotechnology',
    r'\bsw\b': 'Social Work',       # MSW
    r'\bhr\b': 'Human Resource',
    r'\bfm\b': 'Financial Management',
    r'\bib\b': 'International Business',
}


def apply_course_aliases(text: str) -> str:
    """
    Expands short course abbreviations to their full form.
    Uses strict word-boundary regex so 'bsccs' is NOT affected, only '\bcs\b'.
    Called AFTER TYPO_MAP so typos are already fixed first.
    """
    result = text
    for pattern, full_name in COURSE_ALIASES.items():
        result = re.sub(pattern, full_name, result, flags=re.IGNORECASE)
    return result


# ---------------------------------------------------------------------------
# SymSpell Initialization
# ---------------------------------------------------------------------------
_sym_spell: Optional[SymSpell] = None

def _get_sym_spell() -> SymSpell:
    """Lazy-initializer for SymSpell instance. Loads dictionary once and caches."""
    global _sym_spell
    if _sym_spell is not None:
        return _sym_spell

    sym = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    # Load the bundled English frequency dictionary
    dict_path = pkg_resources.resource_filename(
        'symspellpy', 'frequency_dictionary_en_82_765.txt'
    )
    sym.load_dictionary(dict_path, term_index=0, count_index=1)

    # CRITICAL: Inject all college aliases as ultra-high-frequency entries
    # so SymSpell never alters acronyms like 'mcc', 'ssn', 'hits', 'peri', etc.
    for alias in ALIASES.keys():
        for token in alias.split():
            sym.create_dictionary_entry(token.lower(), 999_999_999)

    # Also protect common domain terms from being mis-corrected
    protected_terms = [
        'bsc', 'btech', 'msc', 'mtech', 'mba', 'mca', 'bca', 'bba', 'bcom',
        'mcom', 'phd', 'lpa', 'inr', 'ug', 'pg', 'cs', 'it', 'ai', 'ml',
        'eee', 'ece', 'cse', 'mech', 'civil', 'biomed', 'biotech', 'aided',
        'shift', 'hostel', 'placement', 'admission', 'autonomous', 'affiliation',
        # Fee superlative typos — protect so TYPO_MAP runs before SymSpell corrupts them
        'lowes', 'lowst', 'loweet', 'cheepest', 'chepest', 'cheapeast',
        'expensiv', 'expencive', 'afforable', 'affordble',
    ]
    for term in protected_terms:
        sym.create_dictionary_entry(term, 999_999_999)

    _sym_spell = sym
    logger.info("[SymSpell] Dictionary loaded and college aliases injected.")
    return _sym_spell


def spell_check_query(raw_text: str) -> str:
    """
    Corrects spelling in user query while preserving:
    - College acronyms / aliases (mcc, ssn, hits, peri, etc.)
    - Domain terms (bsc, btech, lpa, etc.)
    - Words containing digits (50k, 2024, etc.)
    Returns the spell-corrected string.
    """
    # Skip spell-check for very short queries or numeric-heavy input
    if len(raw_text.strip()) <= 3:
        return raw_text

    try:
        sym = _get_sym_spell()
        # lookup_compound corrects an entire phrase
        suggestions = sym.lookup_compound(
            raw_text,
            max_edit_distance=2,
            ignore_non_words=True  # preserves numbers like 50k, 2024
        )
        if suggestions:
            corrected = suggestions[0].term
            if corrected.lower() != raw_text.lower():
                logger.debug(f"[SymSpell] '{raw_text}' -> '{corrected}'")
            return corrected
    except Exception as e:
        logger.warning(f"[SymSpell] Spell check failed: {e}")

    return raw_text

def pre_process_query(query: str) -> str:
    """
    Cleans typos and corrects common acronym misspellings before analysis.
    Specifically handles the 'its' -> 'hits' edge case contextually.
    """
    words = query.split()
    if not words:
        return query
        
    q_lower = query.lower()
    processed_words = []
    
    # Check for course context (seeds for 'its' -> 'hits' correction)
    course_context = bool(re.search(r'\b(bsc|btech|be|msc|mtech|mba|mca|bcom|bca|bba|cs|it|specialization|fees?|package|placement)\b', q_lower))

    for i, word in enumerate(words):
        w_clean = re.sub(r'[^\w]', '', word).lower()
        
        # SPECIAL RULE: 'its' -> 'hits'
        if w_clean == 'its':
            # Replace if first word OR if there is course context
            if i == 0 or course_context:
                processed_words.append(word.lower().replace('its', 'hits'))
                continue
        
        # Standard TYPO_MAP check
        if w_clean in TYPO_MAP and w_clean != 'its':
            # Maintain original capitalization if possible (simplified here)
            processed_words.append(word.lower().replace(w_clean, TYPO_MAP[w_clean]))
        else:
            processed_words.append(word)
            
    joined = " ".join(processed_words)
    # COURSE ALIAS EXPANSION: expand 'cs' -> 'Computer Science' etc.
    return apply_course_aliases(joined)

class QueryAnalysis(BaseModel):
    intent: str = Field(description="Must be one of: greeting, fee, placement, hostel, admission, course, directory, about, location, facility, comparison, ranking, general")
    
    # --- CORE ENTITIES ---
    raw_colleges: List[str] = Field(default_factory=list, description="Raw college names exactly as mentioned by the user")
    raw_courses: List[str] = Field(default_factory=list, description="Raw course names exactly as mentioned by the user")
    
    # --- ADVANCED ROUTING VARIABLES ---
    is_comparison: bool = Field(default=False, description="True if the user is comparing two or more things")
    target_metric: Optional[str] = Field(default=None, description="The specific metric asked for filtering, e.g., 'placement', 'fee', 'package'")
    metric_range: Optional[List[float]] = Field(default=None, description="A two-item list representing the [min, max] range. E.g., [70, 85].")
    degree_level: Optional[str] = Field(default=None, description="UG for Undergrad/Bachelor, PG for Postgrad/Master")
    target_location: Optional[str] = Field(default=None, description="Extracted city, area, or road, e.g., OMR, Adyar, Tambaram, North Chennai")

def expand_course_acronyms(text: str) -> str:
    """Expands common compound shorthands like 'bsc cs' to full searchable terms."""
    shorthands = {
        r"\bbsc\s*cs\b": "B.Sc Computer Science",
        r"\bb\.?sc\s+cs\b": "B.Sc Computer Science",
        r"\bb\.?sc\s*computer\s*science\b": "B.Sc Computer Science",
        r"\bbtech\s*cse\b": "B.Tech Computer Science",
        r"\bbe\s*cse\b": "B.E Computer Science",
        r"\bbcom\s*af\b": "B.Com Accounting & Finance",
        r"\bbcom\s*pa\b": "B.Com Professional Accounting",
        r"\bbcom\s*cs\b": "B.Com Corporate Secretaryship"
    }
    expanded = text.lower()
    for pattern, full_name in shorthands.items():
        expanded = re.sub(pattern, full_name, expanded, flags=re.I)
    return expanded

def match_course_regex(text: str) -> Optional[str]:
    """
    Extract course keyword from text using specific regex patterns.
    Strips noise words to isolate the core degree/specialization.
    """
    lower = text.lower()
    patterns: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"b\.?sc\.?\s+((?:computer\s+science|ai|ml|data\s+science|mathematics|physics|chemistry|biochemistry|microbiology|psychology|biotechnology|it|information\s+technology|visual\s+communication|zoology|plant\s+biology|nutrition|radiology|medical)[\w\s&]*)", re.I), "B.Sc"),
        (re.compile(r"b\.?sc", re.I), "B.Sc"),
        (re.compile(r"(?:b\.?tech|b\.?e\.?)\s+((?:computer\s+science|cse|ai|ml|data\s+science|mechanical|civil|aerospace|electrical)[\w\s&]*)", re.I), "B.Tech"),
        (re.compile(r"b\.?tech|b\.?e\.?", re.I), "B.Tech"),
        (re.compile(r"b\.?com\.?\s+((?:general|honours|accounting|finance|bank|corporate|computer|marketing|professional)[\w\s&]*)", re.I), "B.Com"),
        (re.compile(r"b\.?com", re.I), "B.Com"),
        (re.compile(r"b\.?c\.?a", re.I), "BCA"),
        (re.compile(r"b\.?b\.?a", re.I), "BBA"),
        (re.compile(r"m\.?sc\.?\s+((?:computer\s+science|mathematics|physics|chemistry|biochemistry|zoology|psychology|nutrition|clinical)[\w\s&]*)", re.I), "M.Sc"),
        (re.compile(r"m\.?sc", re.I), "M.Sc"),
        (re.compile(r"m\.?com", re.I), "M.Com"),
        (re.compile(r"m\.?b\.?a", re.I), "MBA"),
        (re.compile(r"m\.?c\.?a", re.I), "MCA"),
        (re.compile(r"m\.?tech\.?\s+([\w\s&]+)", re.I), "M.Tech"),
        (re.compile(r"m\.?tech", re.I), "M.Tech"),
        (re.compile(r"ph\.?d", re.I), "Ph.D"),
    ]
    for pattern, prefix in patterns:
        m = pattern.search(lower)
        if m:
            raw = m.group(0).strip()
            # Remove trailing noise words
            raw = re.sub(r"\s+(fees?|at|in|of|college|cost|price|for|the)\b.*$", "", raw, flags=re.I).strip()
            return raw
    return None
    
def extract_degree_level(text: str) -> Optional[str]:
    """Identify if the user is asking for UG or PG courses."""
    lower = text.lower()
    if re.search(r"\b(ug|under\s*grad|bachelor|degree|under\s*graduate)\b", lower):
        return "UG"
    if re.search(r"\b(pg|post\s*grad|master|higher\s*studies|post\s*graduate)\b", lower):
        return "PG"
    return None

def normalize_numerical_range(raw_range: List[float], metric: str) -> List[float]:
    """Corrects shorthand like '50k' or '6 LPA' that the LLM might pass as raw numbers."""
    if not raw_range:
        return raw_range
    
    # If LLM returns a single value instead of a range, assume [0, val]
    if len(raw_range) == 1:
        raw_range = [0.0, float(raw_range[0])]
    elif len(raw_range) > 2:
        raw_range = [float(raw_range[0]), float(raw_range[1])]
    else:
        raw_range = [float(r) for r in raw_range]
        
    rmin, rmax = raw_range
    # Note: If LLM extracts 50 for '50k', we need to multiply.
    if metric == 'fee':
        # If value is too small for a fee (e.g. < 500), it's likely 'k' shorthand
        if 0 < rmin < 1000: rmin *= 1000
        if 0 < rmax < 1000: rmax *= 1000
    
    return [rmin, rmax]

def match_range_regex(text: str) -> Optional[dict]:
    """
    Backfill range extraction if LLM fails due to currency symbols/shorthand.
    Matches: 'under 50k', 'below ₹50000', 'above 80%', '6-8 LPA'.
    """
    lower = text.lower()
    
    # Range Patterns
    # 1. Fees (under/below/above/between)
    fee_patterns = [
        (r"(?:under|below|less\s*than|within|max(?:imum)?)\s*(?:₹|rs\.?|inr|rupees)?\s*(\d+(?:\.\d+)?)\s*(k|lakh|lpa)?", "fee", "below"),
        (r"(?:above|more\s*than|greater\s*than|over|min(?:imum)?)\s*(?:₹|rs\.?|inr|rupees)?\s*(\d+(?:\.\d+)?)\s*(k|lakh|lpa)?", "fee", "above"),
        (r"(?:between|from)\s*(?:₹|rs\.?|inr|rupees)?\s*(\d+)\s*(k)?\s*(?:to|and|-)\s*(?:₹|rs\.?|inr|rupees)?\s*(\d+)\s*(k)?", "fee", "between")
    ]
    
    for pattern, metric, direction in fee_patterns:
        m = re.search(pattern, lower)
        if m:
            val1 = float(m.group(1).replace(',', ''))
            mult1 = m.group(2) if len(m.groups()) >= 2 else None
            if mult1 == 'k': val1 *= 1000
            elif mult1 in ['lpa', 'lakh']: val1 *= 100000
            
            if direction == "below":
                return {"target_metric": "fee", "metric_range": [0.0, val1]}
            elif direction == "above":
                return {"target_metric": "fee", "metric_range": [val1, 500000.0]} # Cap for fees
            elif direction == "between":
                val2 = float(m.group(3).replace(',', ''))
                mult2 = m.group(4) if len(m.groups()) >= 4 else None
                if mult2 == 'k': val2 *= 1000
                return {"target_metric": "fee", "metric_range": [val1, val2]}
                
    # 2. Placement/Package shorthand (LPA, %)
    if "lpa" in lower or "package" in lower:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*lpa", lower)
        if m: return {"target_metric": "package", "metric_range": [float(m.group(1)), float(m.group(2))]}
        m = re.search(r"(?:above|over|min)\s*(\d+(?:\.\d+)?)\s*lpa", lower)
        if m: return {"target_metric": "package", "metric_range": [float(m.group(1)), 25.0]} # Cap
        m = re.search(r"(?:under|below|max)\s*(\d+(?:\.\d+)?)\s*lpa", lower)
        if m: return {"target_metric": "package", "metric_range": [0.0, float(m.group(1))]}

    return None

def analyze_query_advanced(query: str, context_history: list) -> QueryAnalysis:
    """Uses Groq JSON mode to perform semantic intent routing and raw entity extraction."""
    # 🚨 STEP 1: Run the autocorrect FIRST!
    from .utils import autocorrect_query
    corrected_text = autocorrect_query(query)
    
    logger.debug(f"[Router] Spell Correction: '{query}' -> '{corrected_text}'")
    
    # Use corrected text for the rest of the pipeline
    query_lower = corrected_text.lower()
    
    # 🚨 FIX 1: Strip punctuation but KEEP dots (.) and plus (+) symbols!
    # This turns "MCC?" into "mcc " and keeps "A++" intact.
    clean_query_punc = re.sub(r'[^\w\s\.\+]', ' ', query_lower)
    
    # --- PRE-PROCESSING ---
    # Step 1: SymSpell correction (ultra-fast, protects acronyms/domain terms)
    spell_corrected = spell_check_query(clean_query_punc)
    # Step 2: Rule-based typo correction and acronym normalization
    processed_query = pre_process_query(spell_corrected)
    
    # Format history for the LLM context
    history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in context_history[-3:]])
    
    sys_prompt = f"""
    Analyze the user's latest query in the context of the conversation history. 
    Extract intent, raw college names, and course names. 
    Resolve pronouns using history.
    
    NEW: Degree Level Extraction
    If the user specifies a degree level like "UG", "PG", "Undergrad", "Masters":
    - degree_level: "UG" or "PG"
    
    NEW: Numerical Range Extraction (STRICT)
    If the user specifies a range:
    - target_metric: 'placement' (%), 'fee' (INR), 'package' (LPA).
    - metric_range: [min, max] list. 
    - Convert 'k' to 1000s, 'Lakh' to 100000s.
    
    Recent History:
    {history_str}
    
    Output ONLY valid JSON in this format:
    {{
      "intent": "intent_here",
      "raw_colleges": ["name1"],
      "raw_courses": ["course1"],
      "is_comparison": false,
      "target_metric": "metric_name_or_null",
      "metric_range": [min, max]_or_null,
      "degree_level": "UG_or_PG_or_null",
      "target_location": "OMR/Adyar/etc_or_null"
    }}

    CRITICAL: Extract ANY mentioned area, road, or city into 'target_location' (e.g., 'Colleges in Adyar' -> target_location: 'Adyar').
    """
    
    response_json = ask_groq_json(sys_prompt, processed_query)
    # 🚨 FIX: Handle None or empty response
    if not response_json:
        logger.error("[Router] ask_groq_json returned None. Using default analysis.")
        return QueryAnalysis(intent="general", raw_colleges=[], raw_courses=[], is_comparison=False)
        
    try:
        data = json.loads(response_json)
        # Ensure the LLM didn't invent new fields
        cleaned_data = {k: v for k, v in data.items() if k in QueryAnalysis.__fields__}
        
        # --- INTENT FORCING ---
        # Explicitly force superlative intents to ignore standard fee/course defaults
        if any(w in processed_query.lower() for w in [
                'cheapest', 'cheepest', 'lowest fee', 'lowest fees', 'lowes fee', 'lowes fees',
                'lowst fee', 'lowst fees', 'most affordable', 'most affordble', 'lowest cost', 'cheapest fees']):
            cleaned_data['intent'] = 'cheapest'
        elif any(w in processed_query.lower() for w in ['most expensive', 'highest fee', 'costliest', 'highest cost']):
            cleaned_data['intent'] = 'most_expensive'
        # Force course intent if degree-level keywords or course-related words are present
        elif re.search(r'\bcourses?\b|\bug\b|\bpg\b|\bundergrad\b|\bpostgrad\b', processed_query.lower()):
            if cleaned_data.get('intent') not in ('fee', 'comparison', 'ranking'):
                cleaned_data['intent'] = 'course'
            # Also backfill degree_level in case LLM missed it
            if not cleaned_data.get('degree_level'):
                cleaned_data['degree_level'] = extract_degree_level(processed_query)

        # Integration: Expansion of shorthands
        expanded_query = expand_course_acronyms(processed_query)
        
        # Integration: If LLM missed a course name but regex finds it, backfill it
        regex_course = match_course_regex(expanded_query)
        if regex_course and not cleaned_data.get('raw_courses'):
            cleaned_data['raw_courses'] = [regex_course]
            
        # Integration: Degree Level
        if not cleaned_data.get('degree_level'):
            cleaned_data['degree_level'] = extract_degree_level(expanded_query)
            
        # Integration: Range Correction (REGEX BACKFILL)
        if not cleaned_data.get('metric_range') or not cleaned_data.get('target_metric'):
            regex_range = match_range_regex(processed_query)
            if regex_range:
                cleaned_data['target_metric'] = regex_range['target_metric']
                cleaned_data['metric_range'] = regex_range['metric_range']
        
        # Integration: Range Correction (LLM Normalization)
        if cleaned_data.get('metric_range') and cleaned_data.get('target_metric'):
            cleaned_data['metric_range'] = normalize_numerical_range(
                cleaned_data['metric_range'], cleaned_data['target_metric']
            )
            
        # --- BULLETPROOF ALIAS & PUNCTUATION EXTRACTION ---
        # 1. Strip punctuation (preserve dots for B.Tech/B.Sc)
        clean_query = re.sub(r'[^\w\s.]', '', query.lower())
        
        # 2-4. Loop through every alias and check exact word boundaries
        matched_set = set()
        for alias, db_slug in ALIASES.items():
            if re.search(rf'\b{re.escape(alias)}\b', clean_query):
                matched_set.add(alias) # Store alias to be fuzzy-resolved later or slugs if preferred
        
        # 5. Assign to model (overwrite LLM to be deterministic)
        if matched_set:
            cleaned_data['raw_colleges'] = list(matched_set)
            logger.debug(f"[Router] Bulletproof extraction: {cleaned_data['raw_colleges']}")

        # --- ATTRIBUTE INTENT OVERRIDE ---
        # Force attribute_search intent for accreditation/status queries
        # FIXED: Moving a++ outside \b word boundaries
        if re.search(r'\b(naac|nba|autonomous|accreditation)\b|a\+\+', clean_query):
            cleaned_data['intent'] = 'attribute_search'
            logger.debug(f"[Router] Attribute keyword detected. Forced intent='attribute_search'.")

        # --- VS / COMPARE / BETWEEN INTENT FORCER ---
        # If user wrote 'a vs b' or 'between a and b', force comparison intent
        if re.search(r'\bvs\b|\bversus\b|\bcompare\b|\bbetween\b', clean_query_punc):
            cleaned_data['intent'] = 'comparison'
            cleaned_data['is_comparison'] = True
            logger.debug(f"[Router] Comparison keyword detected. Forced intent='comparison'.")

        # --- ENTITY COLLISION RESOLVER ---
        # Prevents a college alias (e.g. 'peri', 'mcc', 'hits') from being stored
        # in target_location instead of raw_colleges when the LLM misclassifies it.
        _loc = cleaned_data.get('target_location')
        if _loc:
            _loc_clean = _loc.lower().strip()
            if _loc_clean in ALIASES:
                logger.debug(
                    f"[Router] Entity collision: '{_loc_clean}' was target_location but is a college alias. "
                    f"Moving to raw_colleges."
                )
                cleaned_data['target_location'] = None
                _rc = cleaned_data.get('raw_colleges', [])
                if _loc_clean not in [r.lower() for r in _rc]:
                    _rc.append(_loc_clean)
                cleaned_data['raw_colleges'] = _rc

                # --- INTENT CORRECTION ---
                # If intent was 'location' and we just nulled the only location entity,
                # re-derive intent from query keywords.
                if cleaned_data.get('intent') == 'location':
                    _ql = query.lower()
                    if any(w in _ql for w in ['fee', 'fees', 'cost', 'price', 'cheap', 'afford', 'expensive']):
                        cleaned_data['intent'] = 'fee'
                    elif any(w in _ql for w in ['placement', 'salary', 'package', 'recruit']):
                        cleaned_data['intent'] = 'placement'
                    elif any(w in _ql for w in ['course', 'degree', 'program', 'subject']):
                        cleaned_data['intent'] = 'course'
                    elif any(w in _ql for w in ['hostel', 'accommodation', 'dorm']):
                        cleaned_data['intent'] = 'hostel'
                    elif any(w in _ql for w in ['facility', 'lab', 'library', 'sports']):
                        cleaned_data['intent'] = 'facility'
                    else:
                        cleaned_data['intent'] = 'about'
                    logger.debug(
                        f"[Router] Intent corrected from 'location' to '{cleaned_data['intent']}' "
                        f"after entity collision fix."
                    )

        return QueryAnalysis(**cleaned_data)
    except Exception as e:
        logger.error(f"Semantic analysis parsing failed: {e}")
        return QueryAnalysis(intent="general", raw_colleges=[], raw_courses=[], is_comparison=False)

def extract_colleges_fuzzy(raw_colleges: List[str]) -> List[str]:
    """Uses RapidFuzz to map raw user input to strict database slugs."""
    if not raw_colleges:
        return []
        
    all_colleges = get_all_colleges()
    # Build search pool
    college_map = {}
    for c in all_colleges:
        name = c['name']
        college_map[c['key']] = name
        
        # Smart acronym generation
        clean_name = re.sub(r'[()]', ' ', name)
        words = [w for w in clean_name.split() if w.lower() not in ['of', 'and', 'for', 'the', 'college', 'institute']]
        acronym = "".join([w[0] for w in words if w]).upper()
        if len(acronym) >= 2:
            college_map[f"{c['key']}_acronym"] = acronym

    matched_keys = []
    
    # Noise words to ignore during alias matching
    noise_pattern = re.compile(r'\b(college|university|institute|of|for|and|the)\b', re.I)

    for raw in raw_colleges:
        raw_norm = str(raw).lower().strip()
        # Cleaned version for alias lookup (Hindustan College -> Hindustan)
        raw_clean = noise_pattern.sub('', raw_norm).strip()
        
        # 1. PRIORITY 1: Explicit high-precision aliases
        # Check both original and cleaned version
        target_alias = None
        if raw_norm in ALIASES: target_alias = ALIASES[raw_norm]
        elif raw_clean in ALIASES: target_alias = ALIASES[raw_clean]
        
        if target_alias:
            if target_alias not in matched_keys:
                matched_keys.append(target_alias)
            continue
            
        # Hard-map check for tokens within larger strings with strict word boundaries
        alias_found = False
        for alias, db_key in ALIASES.items():
            if re.search(rf'\b{re.escape(alias)}\b', raw_norm) or re.search(rf'\b{re.escape(alias)}\b', raw_clean):
                if db_key not in matched_keys:
                    matched_keys.append(db_key)
                alias_found = True
                break
        if alias_found:
            continue

        # 2. PRIORITY 2: Fuzzy matching against short aliases
        alias_keys = list(ALIASES.keys())
        alias_match = process.extractOne(raw_clean, alias_keys, scorer=fuzz.ratio, score_cutoff=85)
        if alias_match:
            best_key = ALIASES[alias_match[0]]
            if best_key not in matched_keys:
                matched_keys.append(best_key)
            continue

        # 3. PRIORITY 3: Fuzzy matching against full names
        match = process.extractOne(raw, college_map, scorer=fuzz.token_set_ratio, score_cutoff=85)
        if match:
            best_key = match[2].split("_")[0]
            if best_key not in matched_keys:
                matched_keys.append(best_key)
                
    return matched_keys

# 🚨 FIX: Added 'loaction' (typo) and 'stand for' (RAG fallback)
def detect_intent(query_lower: str) -> str:
    if re.search(r'\b(location|address|where|loaction|pincode)\b', query_lower):
        return 'location'
    # Area-based queries (colleges in Adyar, North Chennai, etc.)
    if re.search(r'\b(colleges?|institutions?)\s+(in|near|around|at)\s+', query_lower):
        return 'location'
    if re.search(r'\b(vs|compare|between)\b', query_lower):
        return 'comparison'
    if re.search(r'\b(naac|nba|autonomous|a\+\+)\b', query_lower):
        return 'attribute_search'
    # About / general info (established year, history, etc.)
    if re.search(r'\b(established|founded|when\s+was|history\s+of|about)\b', query_lower):
        return 'about'
    # Cheapest / Most expensive must come BEFORE fee and course
    if re.search(r'\b(cheapest|most\s+affordable|lowest\s+fee|least\s+expensive)\b', query_lower):
        return 'cheapest'
    if re.search(r'\b(most\s+expensive|highest\s+fee|priciest|costliest)\b', query_lower):
        return 'most_expensive'
    if re.search(r'\b(placement|package|lpa|salary|recruiters)\b', query_lower):
        return 'placement'
    # Placement percentage queries → ranking
    if re.search(r'\b\d+\s*%\s*placement\b|\bplacement\s+rate\b', query_lower):
        return 'ranking'
    # LPA range queries → ranking handler
    if re.search(r'\b\d+[\-–]\d+\s*lpa\b', query_lower):
        return 'ranking'
    if re.search(r'\b(fee|fees|cost|much|price)\b', query_lower):
        return 'fee'
    if re.search(r'\b(course|courses|program|programs|offering|offerings|study|degree|degrees)\b', query_lower):
        return 'course'
    # Club/sports/wifi/facility queries → facility handler
    if re.search(r'\b(club|clubs|sports|wifi|wi-fi|lab|library|gym|canteen|transport)\b', query_lower):
        return 'facility'
    if re.search(r'\b(history|stand for)\b', query_lower):
        return 'rag_qa'
    return 'general'

def extract_colleges(query: str, aliases: dict) -> list:
    # 🚨 FIX: Strip question marks and symbols, keep dots and pluses, and PAD WITH SPACES
    clean_query = " " + re.sub(r'[^\w\s\.\+]', ' ', query.lower()) + " "
    
    matched_keys = []
    for alias, db_key in aliases.items():
        # Because we added spaces to the query, we look for " alias " 
        # This guarantees "MCC?" or "HITS!" are caught!
        if f" {alias.lower()} " in clean_query:
            if db_key not in matched_keys:
                matched_keys.append(db_key)
                
    return matched_keys
