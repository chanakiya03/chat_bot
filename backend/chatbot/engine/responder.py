"""
Response Generator — Brain of the chatbot.
Now strictly database-driven with double-verification and high-level ranker/comparison integration.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from .search import semantic_search
from .ranker import rank_colleges
from .loader import get_all_colleges, get_college_by_key
from .groq_client import ask_groq
from .router import analyze_query_advanced, extract_colleges_fuzzy, detect_intent as router_detect_intent
from .firewall import sanitize_query
from .utils import (
    _normalize, _format_ranking, _format_comparison, _format_detailed_report,
    _format_fee_comparison, _format_college_directory, _map_sources_to_names,
    _format_course_table, extract_course, detect_batch_filter, suggest_refined_query,
    CHENNAI_AREA_MAP, find_strict_qa_match
)
from chatbot.models import KnowledgeBaseQA, CollegeDetail

# Delayed import of handlers to avoid circularity until refactor is complete
_INTENT_ROUTER = None
def get_intent_router():
    global _INTENT_ROUTER
    if _INTENT_ROUTER is None:
        from .handlers import (
            AboutHandler, FeeHandler, RankingHandler, 
            DirectoryHandler, GreetingHandler, LocationHandler,
            FacilityHandler, AdmissionHandler, ComparisonHandler,
            PlacementHandler, HostelHandler, CourseHandler,
            AttributeSearchHandler, RAGQAHandler
        )
        _INTENT_ROUTER = {
            'about': AboutHandler(),
            'fee': FeeHandler(),
            'ranking': RankingHandler(),
            'directory': DirectoryHandler(),
            'greeting': GreetingHandler(),
            'location': LocationHandler(),
            'facility': FacilityHandler(),
            'admission': AdmissionHandler(),
            'comparison': ComparisonHandler(),
            'placement': PlacementHandler(),
            'hostel': HostelHandler(),
            'course': CourseHandler(),
            'attribute_search': AttributeSearchHandler(),
            'general': RAGQAHandler(),
        }
    return _INTENT_ROUTER

logger = logging.getLogger(__name__)

# ─── Intent Detection ────────────────────────────────────────────────────────

INTENT_PATTERNS = [
    ('comparison', [r'\bcompar\w*\b', r'\bbetter\b', r'\bvs\b', r'\bversus\b', r'\bor\b.*college', r'\bwhich is better\b', r'\bmore\s+expensive\b', r'\bcheaper\b', r'\bcostl\w+\b', r'\bpricey\b']),
    ('ranking',    [r'\bbest\b', r'\btop\b', r'\brank\w*\b', r'\brecommend\w*\b', r'\bhighest\b', r'\blowest\b', r'\bmax\w*\b', r'\bmin\w*\b', r'\bcheap\w*\b', r'\boldest\b', r'\blegacy\b']),
    ('fee',        [r'\bfee\w*\b', r'\bcost\b', r'\bprice\b', r'\bafford\w*\b', r'\bexpens\w*\b', r'\blow\w*\s*fee\b',
                    r'\bhow\s+much\b', r'\btuition\b', r'\bquota\b', r'\bgov\w*\s*quota\b', r'\bmgmt\s*quota\b']),
    ('placement',  [r'\bplace\w*\b', r'\bjob\b', r'\brecruit\w*\b', r'\bpackage\b', r'\blpa\b', r'\bsalar\w*\b', r'\bcampus\b']),
    ('hostel',     [r'\bhostel\b', r'\baccomod\w*\b', r'\bstay\b', r'\broom\b']),
    ('admission',  [r'\badmiss\w*\b', r'\bapply\b', r'\benroll\w*\b', r'\beligib\w*\b', r'\bcutoff\b', r'\bcounsel\w*\b', r'\btnea\b', r'\bneet\b', r'\bentrance\b']),
    ('course',     [r'\bcourse\w*\b', r'\bprogram\w*\b', r'\bdegree\b', r'\bstream\b', r'\bspecial\w*\b', r'\bsubject\b',
                    r'\bmba\b', r'\bmca\b', r'\bbca\b', r'\bb\.?tech\b', r'\bm\.?tech\b', r'\bb\.?sc\b', r'\bm\.?sc\b',
                    r'\bpharm\w*\b', r'\blaw\b', r'\bengineering\b', r'\bnursing\b', r'\bmbbs\b', r'\bb\.?arch\b', r'\barchitecture\b',
                    r'\bavail\w*\b', r'\boffer\w*\b', r'\blist\b', r'\bduration\b', r'\blong\b', r'\byear\b']),
    ('directory',  [r'\bover\s*all\b', r'\ball\s*college', r'\blist\s*of\s*college', r'\bsummary\b', r'\bdirectory\b', r'\bcolleges\s*available\b']),
    ('about',      [r'\babout\b', r'\bdetai\w*\b', r'\bdeat\w*\b', r'\binfo\w*\b', r'\bestablish\w*\b', r'\bfound\w*\b', r'\bhistory\b', r'\breput\w*\b', r'\brank\w*\b']),
    ('location',   [r'\blocat\w*\b', r'\bin\b\s*\w+', r'\bwhere\b', r'\barea\b', r'\bcity\b', r'\baddress\b', r'\bnear\b', r'(?<!\w)\w+\s+colleges?\b']),
    ('facility',   [r'\bfacilit\w*\b', r'\bamenit\w*\b', r'\bservice\w*\b', r'\bcenter\b', r'\blab\b', r'\bwifi\b', r'\blibrary\b', r'\bmedical\b', r'\bclinic\b', r'\bsport\w*\b', r'\bgym\b', r'\bclub\b', r'\bsociet\w*\b', r'\bactivity\b', r'\bactivities\b', r'\bncc\b', r'\bnss\b', r'\bred\s*cross\b', r'\byrc\b']),
    ('greeting',   [r'\b(hi|hello|hey|good\s*(morning|afternoon|evening))\b']),
]

def detect_intent(query: str) -> str:
    q = query.lower()
    for intent, patterns in INTENT_PATTERNS:
        for p in patterns:
            if re.search(p, q):
                return intent
    return 'general'

def extract_college_names(query: str) -> list:
    """Return list of college keys mentioned in query. Uses a scoring system for strict matching."""
    all_colleges = get_all_colleges()
    q_lower = query.lower()
    # Normalize: strip possessives and punctuation
    q_norm = q_lower.replace("’", "").replace("'", "")
    q_clean = re.sub(r'[,;/]+', ' ', q_norm)
    q_clean = re.sub(r'[^\w\s]', ' ', q_clean)
    tokens = q_clean.split()
    
    COLLEGE_STOPWORDS = {
        'college', 'university', 'institute', 'arts', 'science', 'technology',
        'higher', 'education', 'for', 'and', 'the', 'with', 'about', 'from', 
        'near', 'in', 'of', 'co-educational', 'coeducational'
    }
    # DESCRIPTORS to keep for acronyms but not for general significance checks
    ACRONYM_DESCRIPTORS = {'women', 'womens', 'men', 'mens', 'management', 'engineering', 'research'}

    scores = {} # college_key -> score

    for college in all_colleges:
        key = college['key']
        name = college['name'].lower().replace("’", "").replace("'", "")
        name_clean = re.sub(r'[()]', ' ', name)
        name_parts = [n.strip() for n in name_clean.split() if n.strip()]
        sig_parts = [p for p in name_parts if p not in COLLEGE_STOPWORDS]

        score = 0
        
        # 1. Exact Slug Match (Highest Priority)
        if re.search(rf'\b{re.escape(key.lower())}\b', q_clean):
            score = 100
        
        # 2. Acronym Match (Be more inclusive: keep 'W' for Women, 'M' for Management)
        acronym_parts = [p for p in name_parts if p not in COLLEGE_STOPWORDS]
        acronym = ''.join(w[0] for w in acronym_parts if len(w) > 0)
        if len(acronym) >= 2 and f" {acronym} " in f" {q_clean} ":
            score = max(score, 90)
        
        # Specific high-confidence checks for mapped keys
        if 'wcc' in q_clean and key == 'womens-christian-college':
            score = max(score, 98)
        if 'ethiraj' in q_clean and key == 'ethiraj-college-for-women':
            score = max(score, 98)
        if 'mcc' in q_clean and key == 'madras-christian-college':
            score = max(score, 98)
        if 'ssn' in q_clean and key == 'ssn-college-of-engineering':
            score = max(score, 98)

        # 3. Full Significant Name Match
        matched_sig_parts = 0
        for part in sig_parts:
            if re.search(rf'\b{re.escape(part)}\b', q_clean):
                matched_sig_parts += 1
        
        if sig_parts and matched_sig_parts == len(sig_parts):
            score = max(score, 95)
        elif matched_sig_parts > 0:
            # Partial match score based on percentage of sig parts matched
            score = max(score, int((matched_sig_parts / len(sig_parts)) * 80))

        if score > 0:
            scores[key] = score

    if not scores:
        return []

    # Filter: If there's a 90+ score match, isolate it unless it's a potential comparison
    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    if not sorted_keys: return []
    max_score = scores[sorted_keys[0]]
    
    # NEW: If query contains comparison markers like "or", "vs", "versus", don't isolate top match here
    if any(w in q_lower for w in [' or ', ' vs ', ' versus ', ' against ']):
        return [k for k in sorted_keys if scores[k] >= 40] # Broaden for comparisons
        
    if max_score >= 90:
        return [k for k in sorted_keys if scores[k] >= 90]
        
    return sorted_keys


# NOTE: extract_course is imported from .utils (canonical version)
# The duplicate that used to live here has been removed.

# Formatting and Utility helpers have been moved to .utils

# ─── Formatting Helpers ───────────────────────────────────────────────────────

# Formatting and Utility helpers have been moved to .utils

# ─── Strict QA Matching & Verification ────────────────────────────────────────

# Fast pre-built suggestions per intent — avoids Groq API call on every response
import random as _random

def verify_response(answer: str, related_data: list):
    """Legacy verification shim - calls advanced verifier if possible or does basic check."""
    from .verifier import verify_response as verify_core, verify_response_advanced
    return verify_response_advanced(answer, related_data)


# ─── Main Generator ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are CollegeBot, a strictly data-driven expert for college admissions.
You ONLY answer based on the provided context. 
If the information is not in the context, say: "I'm sorry, I don't have verified information to answer that."
Use markdown. Be professional and concise.
"""

def _get_intent_router() -> Dict[str, 'BaseIntentHandler']: # Added 'BaseIntentHandler' as forward reference
    """Registry of specialized strategy handlers."""
    from .handlers import ( # Moved import here as per original structure
        AboutHandler, FeeHandler, RankingHandler, 
        DirectoryHandler, GreetingHandler, LocationHandler,
        FacilityHandler, AdmissionHandler, ComparisonHandler,
        PlacementHandler, HostelHandler, CourseHandler,
        CheapestHandler, MostExpensiveHandler,
        AttributeSearchHandler, RAGQAHandler
    )
    return {
        'greeting': GreetingHandler(),
        'about': AboutHandler(),
        'fee': FeeHandler(),
        'placement': PlacementHandler(),
        'ranking': RankingHandler(),
        'cheapest': CheapestHandler(),
        'most_expensive': MostExpensiveHandler(),
        'hostel': HostelHandler(),
        'admission': AdmissionHandler(),
        'course': CourseHandler(),
        'directory': DirectoryHandler(),
        'location': LocationHandler(),
        'facility': FacilityHandler(),
        'comparison': ComparisonHandler(),
        'attribute_search': AttributeSearchHandler(),
        'discovery': AttributeSearchHandler(),
        'rag_qa': RAGQAHandler(),
        'general': RAGQAHandler(),
    }

def generate_response_advanced(query: str, history: list) -> dict:
    """
    Main Orchestrator — Sequential Processing Pipeline (Phases 1-4)
    Flow: User Query → Router → Firewall → Handler → Verifier → Final JSON
    """
    try:
        # ── Phase 0a: INIT_CHAT Command Bypass ──────────────────────────────────
        # Sent automatically by the frontend on page load to trigger welcome message.
        # Never reaches the LLM/DB.
        if query.strip() == 'INIT_CHAT':
            logger.debug("[Bypass] INIT_CHAT command received. Triggering GreetingHandler.")
            from .handlers import GreetingHandler
            from .router import QueryAnalysis
            return GreetingHandler().handle('INIT_CHAT', QueryAnalysis(intent='greeting'), [])

        # ── Phase 0b: Persona Questions ─────────────────────────────────────────
        # Hardcoded instant response — never sent to LLM or verifier.
        _persona_q = re.search(
            r'^(what\s+is\s+your\s+name|who\s+are\s+you|what\s+are\s+you|'
            r'introduce\s+yourself|tell\s+me\s+about\s+yourself|are\s+you\s+a\s+bot|'
            r'are\s+you\s+an?\s+ai|are\s+you\s+human)',
            query.lower().strip()
        )
        if _persona_q:
            return {
                'text': (
                    "🤖 I'm **CollegeBot**, your AI-powered college enquiry assistant!\n\n"
                    "I can help you with:\n"
                    "- 💰 **Fees** — course-wise fee details\n"
                    "- 🎓 **Courses** — UG/PG programs offered\n"
                    "- 📈 **Placements** — average packages, top recruiters\n"
                    "- 📍 **Location** — area, campus info\n"
                    "- 🏆 **Rankings** — best colleges by criteria\n\n"
                    "Just type your question and I'll get right on it!"
                ),
                'sources': [], 'intent': 'greeting', 'type': 'persona', 'verified': True,
                'suggestions': ["Fees at HITS", "Top BCA colleges", "Compare SSN and HITS"]
            }

        # ── Phase 0c: Absolute Greeting Bypass (Regex) ──────────────────────────
        # Prevents LLM context bleed for simple greetings
        greeting_pattern = r'^(hi|hello|hey|good\s*(morning|afternoon|evening)|namaste|vanakkam)[!?\s]*$'
        if re.search(greeting_pattern, query.lower().strip()):
            logger.debug(f"[Bypass] Greeting detected: '{query}'. Jumping to GreetingHandler.")
            from .handlers import GreetingHandler
            from .router import QueryAnalysis # Dummy analysis for handler
            return GreetingHandler().handle(query, QueryAnalysis(intent='greeting'), [])

        # Phase 0.5: Spell Correction
        from .utils import autocorrect_query
        corrected_text = autocorrect_query(query)
        logger.debug(f"[Responder] Correction: '{query}' -> '{corrected_text}'")
        
        # Use corrected text for all subsequent extraction
        _q_proc = corrected_text
        _q_lower = corrected_text.lower()

        # Phase 1: Semantic Router (Intent & Entity Extraction)
        from .router import extract_colleges, detect_intent, ALIASES, QueryAnalysis
        
        # Use the "The Ultimate Extractor" logic as requested
        intent = detect_intent(_q_lower)
        matched_college_keys = extract_colleges(_q_proc, ALIASES)
        
        # Initialize analysis for downstream handlers
        analysis = QueryAnalysis(intent=intent, raw_colleges=matched_college_keys)
        
        # Always try to extract a course for handlers that need it (fees, comparison)
        course = extract_course(_q_proc)
        if course:
            analysis.raw_courses = [course]
        
        # Extract metric range (e.g., "₹3-6 LPA", "under 50k")
        from .router import match_range_regex
        range_result = match_range_regex(_q_proc)
        if range_result and isinstance(range_result, dict):
            analysis.metric_range = range_result.get('metric_range')
            analysis.target_metric = range_result.get('target_metric')

        # Phase 2: Anti-Hijack Firewall (Mutates analysis if needed)
        # (Wipes context bleed for global/superlative queries without explicit entities)
        from .firewall import sanitize_query
        analysis, matched_college_keys = sanitize_query(analysis, matched_college_keys, query)
        
        # 🚨 INTERCEPTOR: If 2+ colleges matched, FORCE comparison — UNLESS the user is
        # asking a superlative question (cheapest, most expensive) which needs its own handler.
        _PROTECTED_INTENTS = {'cheapest', 'most_expensive'}
        if len(matched_college_keys) >= 2 and analysis.intent not in _PROTECTED_INTENTS:
            analysis.intent = 'comparison'
            intent = 'comparison'
        
        # Access AboutHandler for default fallback
        from .handlers import AboutHandler, ComparisonHandler, RAGQAHandler
        
        # If intent is general/unknown but we have a college, RAG is the best fallback
        if analysis.intent in ('general', 'unknown', 'college_info') and matched_college_keys:
            handler = RAGQAHandler()
        else:
            handler = _get_intent_router().get(analysis.intent, AboutHandler())

        # --- MULTI-COLLEGE RE-ROUTING ---
        # If 2+ colleges matched AND the query has VS/compare/and intent,
        # reroute to ComparisonHandler regardless of the detected single-college intent.
        _single_college_intents = {'placement', 'fee', 'hostel', 'course', 'about', 'admission', 'facility'}
        _q_lower_reroute = query.lower()
        if (analysis.intent in _single_college_intents
                and len(matched_college_keys) > 1
                and re.search(r'\bvs\b|\bversus\b|\bcompare\b', _q_lower_reroute)):
            logger.debug(
                f"[Responder] Multi-college re-route: intent='{analysis.intent}' "
                f"with {len(matched_college_keys)} colleges → ComparisonHandler"
            )
            # Preserve original metric as target so ComparisonHandler knows what to focus on
            analysis.target_metric = analysis.intent
            handler = ComparisonHandler()

        response = handler.handle(_q_proc, analysis, matched_college_keys)
        
        # 🚨 FIX: Safety Check
        if response is None:
            logger.error(f"[Responder] Handler {handler.__class__.__name__} returned None. Falling back.")
            return generate_response_legacy(query)

        # Phase 4: Zero-Hallucination Verifier
        from .verifier import verify_response
        response = verify_response(response)
        
        # 🚨 FINAL FIX: Guard against verifier return None
        if not isinstance(response, dict):
            return generate_response_legacy(query)

        # 🚨 NORMALIZATION: Ensure 'text' key exists (Standardize message vs text)
        if 'text' not in response and 'message' in response:
            response['text'] = response['message']
        elif 'text' not in response:
            response['text'] = "I'm sorry, I couldn't generate a proper response text."

        # Meta-information for transparency
        response['_meta'] = {
            'intent': getattr(analysis, 'intent', 'unknown'),
            'colleges_matched': _map_sources_to_names(matched_college_keys),
            'extraction': analysis.dict() if hasattr(analysis, 'dict') else {},
            'verified': response.get('verified', True)
        }
        
        return response

    except Exception as e:
        logger.error(f"Advanced pipeline failed: {e}", exc_info=True)
        return generate_response_legacy(query) # Safe fallback to regex orchestrator

def generate_response_legacy(query: str, context_history: list = None) -> dict:
    if context_history is None: context_history = []
    
    # ── Context Resolver: Expand short/ambiguous follow-up queries ─────────────
    # When the user says "shift 1", "fees?", "compare that?" after a prior query,
    # we reconstruct the query using context from the last turn.
    _ambiguous_triggers = {
        'shift i', 'shift 1', 'shift ii', 'shift 2',
        'first', 'second', 'that', 'it', 'there', 'this',
        'fees?', 'fee?', 'cost?', 'yes', 'no', 'ok', 'okay',
    }
    q_stripped = query.strip().lower().rstrip('?!.')

    def _is_short_followup(q: str) -> bool:
        words = q.strip().split()
        # If the query contains "list", "all", "which", or "show", it's likely a complete 
        # request for a filtered list, not a short follow-up to a specific college.
        if any(w in q.lower() for w in ['list', 'all', 'which', 'show', 'available']):
            return False
            
        return len(words) <= 4 and (
            q.lower() in _ambiguous_triggers or
            not extract_college_names(q) or
            detect_intent(q) in ('general', None)
        )

    if context_history and _is_short_followup(query):
        # Find last user message in history
        last_user_msg = None
        for msg in reversed(context_history[:-1]):  # skip the current message
            if msg.get('role') == 'user':
                last_user_msg = msg.get('content', '')
                break

        if last_user_msg:
            # Build a reconstructed query: current qualifier + previous context
            reconstructed = f"{query} {last_user_msg}"
            logger.debug(f"[Context] Reconstructed: '{query}' + '{last_user_msg}' → '{reconstructed}'")
            query = reconstructed
    # ── End Context Resolver ──────────────────────────────────────────────────

    q_lower = query.lower()
    
    try:
        # 1. Intent Detection
        intent = detect_intent(query)
        college_keys = extract_college_names(query)

        # Context-aware college extraction for pronouns like "these", "those", "they", "them"
        # Refinement: Only trigger on explicit pronouns, NOT generic "the college" or "colleges"
        # to avoid hijacking global filters like "Autonomous colleges list"
        if not college_keys and any(f" {w} " in f" {q_lower} " for w in ['these', 'those', 'they', 'them']):
            for msg in reversed(context_history):
                if msg.get('role') == 'assistant':
                    extracted = extract_college_names(msg.get('content', ''))
                    if extracted:
                        college_keys = extracted
                        break

        # --- Superlative Intent Guardian ---
        # If the router already set intent='cheapest'/'most_expensive', preserve it.
        # If the raw text has a superlative AND a college, still force cheapest/most_expensive.
        # This prevents FeeHandler from dumping a full fee table for queries like 'lowest fees in peri'.
        _superlative_cheapest = any(w in q_lower for w in [
            'cheapest', 'lowest', 'most affordable', 'minimum fees', 'min fee', 'affordable'
        ])
        _superlative_expensive = any(w in q_lower for w in [
            'most expensive', 'highest fee', 'costliest', 'highest cost', 'priciest'
        ])
        if _superlative_cheapest and intent not in ('cheapest', 'most_expensive', 'comparison'):
            intent = 'cheapest'
        elif _superlative_expensive and intent not in ('cheapest', 'most_expensive', 'comparison'):
            intent = 'most_expensive'
        elif (_superlative_cheapest or _superlative_expensive or
              any(w in q_lower for w in ['top', 'best', 'highest', 'most'])) and not college_keys:
            # Fallback: global superlative queries (no college named) → ranking
            if extract_course(query) and any(w in q_lower for w in ['fee', 'cost', 'expensive', 'cheap', 'afford']):
                intent = 'fee'  # e.g., "Cheapest BCA fees"
            else:
                intent = 'ranking'  # e.g., "Most affordable college"
        # -----------------------------------------------------------------------


        # 2. DIRECTORY Handle (Priority for broad queries)
        if intent == 'directory' and not college_keys:
            return {
                'text': _format_college_directory(),
                'sources': _map_sources_to_names([c['key'] for c in get_all_colleges()]),
                'intent': intent,
                'type': 'college_directory',
                'verified': True,
                'suggestions': suggest_refined_query(query, intent)
            }

        # ─── GREETING Handler (Legacy Fallback) ───
        if intent == 'greeting':
            return {
                'text': "Hello! 👋 I am CollegeBot. I can help you find verified information about colleges, including fees, placements, courses, and admission details. What are you looking for today?",
                'sources': [],
                'intent': 'greeting',
                'type': 'greeting',
                'verified': True,
                'suggestions': [
                    "Top engineering colleges", 
                    "Cheapest BCA courses", 
                    "Compare SSN and HITS"
                ]
            }
        
        # 2.3. STRICT COLLISION / MULTI-RESULT CHECK (As per Rules)
        # If intent is informational and we have multiple results but no 'comparison' intent,
        # we strictly isolate the top match to follow the "ONLY that college's details" rule.
        if college_keys and len(college_keys) > 1 and intent != 'comparison' and not any(w in q_lower for w in ['vs', 'versus', 'or']):
            logger.debug(f"[Strict] Multiple found {college_keys}, isolating top match '{college_keys[0]}'")
            college_keys = [college_keys[0]]

        # 2.4. MISSING COLLEGE ERROR (As per Rule 6)
        # If the user asks for details/info of a specific college but none was found
        if not college_keys and (intent in ['about', 'fee', 'admission', 'hostel', 'placement']):
            # Distinguish from global searches (like "Engineering colleges" or "Colleges in OMR")
            is_global = any(w in q_lower for w in ['list', 'all', 'any', 'ranking', 'best', 'top', 'in ', 'near', 'cheapest', 'lowest', 'affordable', 'most', 'highest'])
            is_generic = extract_course(query) is not None and not any(w in q_lower for w in ['details', 'info', 'about'])
            
            if not is_global and not is_generic:
                return {
                    'text': "Sorry, the requested college was not found in our dataset.",
                    'sources': [],
                    'intent': intent,
                    'type': 'error_not_found',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, intent)
                }

        # 2.5. ACCREDITATION / NAAC / TYPE Handler — intercepts before ranking
        # Catches: "NAAC A++ colleges", "NBA accredited", "autonomous", "deemed universities", "UGC approved"
        _acc_triggers = {
            'naac a++': 'NAAC A++',
            'naac a+':  'NAAC A+',
            'naac a':   'NAAC A',
            'naac b+':  'NAAC B+',
            'naac b':   'NAAC B',
            'nba':      'NBA',
            'ugc':      'UGC',
        }
        _type_triggers = {
            'autonomous':  'Autonomous',
            'deemed':      'Deemed',
            'affiliated':  'Affiliated',
        }

        matched_acc  = next((label for kw, label in _acc_triggers.items() if kw in q_lower), None)
        matched_type = next((label for kw, label in _type_triggers.items() if kw in q_lower), None)

        # Detect negative constraints (e.g. "non-autonomous", "not NBA", "non NAAC")
        # We look for "non", "not", or "no" before the matched keywords
        is_negative = False
        if matched_acc or matched_type:
            # BUG FIX: Escape trigger keys to avoid "multiple repeat" error with "++"
            all_triggers = list(_acc_triggers.keys()) + list(_type_triggers.keys())
            escaped_triggers = '|'.join(re.escape(k) for k in all_triggers)
            neg_pattern = r'\b(non|not|no)[-\s]+(?:' + escaped_triggers + r')\b'
            if re.search(neg_pattern, q_lower):
                is_negative = True

        if matched_acc or matched_type:
            label_parts = []
            if matched_acc:  label_parts.append(matched_acc)
            if matched_type: label_parts.append(matched_type)
            
            raw_label = " / ".join(label_parts) if label_parts else "matching"
            acc_label = f"non-{raw_label}" if is_negative else raw_label

            # ── Single-college direct answer: "Is MCC autonomous?", "Is SSN NAAC A++?" ──
            if college_keys:
                col = get_college_by_key(college_keys[0])
                if col:
                    details = col.get('details', {})
                    acc_val  = str(details.get('Accreditation', '')).upper()
                    type_val = str(details.get('Type', '')).lower()
                    
                    # Logic: if positive, must match. if negative, must NOT match.
                    acc_ok   = (not matched_acc)  or ((matched_acc.upper()  in acc_val) != is_negative)
                    type_ok  = (not matched_type) or ((matched_type.lower() in type_val) != is_negative)
                    
                    if acc_ok and type_ok:
                        answer = (
                            f"✅ **Yes**, **{col['name']}** is **{acc_label}**.\n\n"
                            f"- **Accreditation**: {details.get('Accreditation', 'N/A')}\n"
                            f"- **Institution Type**: {details.get('Type', 'N/A')}"
                        )
                    else:
                        answer = (
                            f"❌ **No**, **{col['name']}** is **not** classified as **{acc_label}**.\n\n"
                            f"- **Accreditation**: {details.get('Accreditation', 'N/A')}\n"
                            f"- **Institution Type**: {details.get('Type', 'N/A')}"
                        )
                    return {
                        'text': answer,
                        'sources': _map_sources_to_names([col['key']]),
                        'intent': 'about',
                        'type': 'accreditation_direct',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, 'about')
                    }

            # ── No specific college → list all matching colleges ──
            all_colleges = get_all_colleges()
            hits = []
            for c in all_colleges:
                details = c.get('details', {})
                acc_val  = str(details.get('Accreditation', '')).upper()
                type_val = str(details.get('Type', '')).lower()
                
                acc_ok  = (not matched_acc)  or ((matched_acc.upper()  in acc_val) != is_negative)
                type_ok = (not matched_type) or ((matched_type.lower() in type_val) != is_negative)
                
                if acc_ok and type_ok:
                    hits.append(c)

            if hits:
                lines = [f"🏅 **Colleges with {acc_label} accreditation/status:**\n"]
                for c in hits:
                    details = c.get('details', {})
                    acc_str  = details.get('Accreditation', 'N/A')
                    type_str = details.get('Type', 'N/A')
                    lines.append(f"- **{c['name']}** — {acc_str} | {type_str}")
                return {
                    'text': "\n".join(lines),
                    'sources': _map_sources_to_names([c['key'] for c in hits]),
                    'intent': 'ranking',
                    'type': 'accreditation_filter',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, 'ranking')
                }

        # 3. RANKING Handle
        if intent == 'ranking':
            criteria = {}
            is_highest_query = any(w in q_lower for w in ['highest', 'max', 'most', 'top', 'best'])
            is_lowest_query = any(w in q_lower for w in ['cheapest', 'lowest', 'affordable', 'budget', 'cheap'])
            
            if any(w in q_lower for w in ['placement', 'job', 'recruit']):
                criteria = {'placement_weight': 0.8, 'package_weight': 0.15}
            elif any(w in q_lower for w in ['fee', 'cost', 'price']):
                criteria = {'affordability_weight': 0.95}
            elif any(w in q_lower for w in ['package', 'salary', 'lpa']):
                criteria = {'package_weight': 0.8, 'placement_weight': 0.15}
            
            course = extract_course(query)
            ranked = rank_colleges(criteria, course_keyword=course)
            
            # --- 2. Final Strict Sorting Overrides ---
            if ranked:
                # 1. Explicit Affordability Override (Catches "most affordable", "cheapest")
                if any(w in q_lower for w in ['cheap', 'affordable', 'budget']):
                    ranked.sort(key=lambda x: x[2]['avg_annual_fee'])
                    
                # 2. Explicit Expensive Override (Catches "most expensive")
                elif any(w in q_lower for w in ['expensive', 'costly', 'pricey']):
                    ranked.sort(key=lambda x: x[2]['avg_annual_fee'], reverse=True)
                    
                # 3. Highest/Best X
                elif is_highest_query:
                    if any(w in q_lower for w in ['placement', 'recruit', 'job']):
                        ranked.sort(key=lambda x: x[2]['placement_pct'], reverse=True)
                    elif any(w in q_lower for w in ['package', 'salary', 'lpa']):
                        ranked.sort(key=lambda x: x[2]['avg_package_lpa'], reverse=True)
                    elif any(w in q_lower for w in ['old', 'age', 'establish', 'legacy', 'history', 'oldest']):
                        ranked.sort(key=lambda x: x[2].get('established_year', 9999))
                    else:
                        # NEW: Default "Best" Sort
                        # Trust the mathematically balanced Composite Score!
                        ranked.sort(key=lambda x: x[0], reverse=True)
                        
                # 4. Lowest X
                elif is_lowest_query:
                    if any(w in q_lower for w in ['placement', 'recruit', 'job']):
                        ranked.sort(key=lambda x: x[2]['placement_pct'])
                    elif any(w in q_lower for w in ['package', 'salary', 'lpa']):
                        ranked.sort(key=lambda x: x[2]['avg_package_lpa'])
                    else:
                        ranked.sort(key=lambda x: x[2]['avg_annual_fee'])

            if ranked:
                return {
                    'text': _format_ranking(ranked, course), 
                    'sources': _map_sources_to_names([r[1]['key'] for r in ranked]), 
                    'intent': intent, 
                    'type': 'ranking', 
                    'verified': True, 
                    'suggestions': suggest_refined_query(query, intent)
                }

        # 4. COMPARISON Handle
        if intent == 'comparison':
            if len(college_keys) >= 2:
                course = extract_course(query)
                # Detect fee-focused queries: 'fees', 'cost', 'price', 'cheap', 'fee'
                is_fee_query = any(w in q_lower for w in ['fee', 'fees', 'cost', 'price', 'cheap', 'afford'])
                if is_fee_query:
                    return {'text': _format_fee_comparison(college_keys, course), 'sources': _map_sources_to_names(college_keys), 'intent': intent, 'type': 'fee_comparison', 'verified': True, 'suggestions': suggest_refined_query(query, 'fee')}
                return {'text': _format_comparison(college_keys, course), 'sources': _map_sources_to_names(college_keys), 'intent': intent, 'type': 'comparison', 'verified': True, 'suggestions': suggest_refined_query(query, intent)}
 
        # 5. LOCATION Handler
        # Refinement: Allow reputation/history queries to pass through to specialized handlers
        # even if they match broad location patterns (e.g. "SSN reputation")
        if intent == 'location' and not any(w in q_lower for w in ['reput', 'rank', 'about', 'history', 'establish', 'found']):
            # Pattern A: Multi-college Location Comparison or Lookup
            if college_keys:
                col_data = []
                for k in college_keys:
                    col = get_college_by_key(k)
                    if col:
                        col_data.append(col)
                
                if len(col_data) == 1:
                    col = col_data[0]
                    loc = col.get('details', {}).get('Location', 'Not found')
                    return {
                        'text': f"📍 **{col['name']}** is located at:\n\n{loc}",
                        'sources': _map_sources_to_names([col['key']]),
                        'intent': intent,
                        'type': 'location_direct',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }
                elif len(col_data) > 1:
                    # Comparative location matching
                    lines = []
                    locs = [c.get('details', {}).get('Location', '').lower() for c in col_data]
                    
                    # Detect shared locality (simple heuristic: common substrings like 'nungambakkam', 'tambaram')
                    common_areas = ['nungambakkam', 'tambaram', 'adyar', 'guindy', 'mylapore', 't. nagar', 'anna nagar', 'velachery', 'omr', 'ecr']
                    shared = [area for area in common_areas if all(area in loc for loc in locs)]
                    
                    if shared:
                        suburb = shared[0].title()
                        lines.append(f"📍 **Yes**, both **{col_data[0]['name']}** and **{col_data[1]['name']}** are located in the **{suburb}** area.\n")
                    else:
                        lines.append(f"📍 **Location Details**:\n")
                    
                    for c in col_data:
                        lines.append(f"- **{c['name']}**: {c.get('details', {}).get('Location')}")
                    
                    return {
                        'text': "\n".join(lines),
                        'sources': _map_sources_to_names([c['key'] for c in col_data]),
                        'intent': intent,
                        'type': 'location_comparison',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }

            # Pattern B: "Colleges in [city]" — find all colleges in that area
            colleges = get_all_colleges()
            found_colleges = []
            
            # Extract target location from query (e.g. "in Tambaram area" or "Nungambakkam colleges")
            target_loc = None
            location_match = re.search(r'\bin\s+([a-zA-Z\s]+)\b', query, re.IGNORECASE)
            if location_match:
                target_loc = location_match.group(1).strip().lower()
            else:
                # Direct area name check (if intent is location, look for known suburbs)
                all_suburbs = set()
                for subs in CHENNAI_AREA_MAP.values():
                    all_suburbs.update(subs)
                all_suburbs.update(CHENNAI_AREA_MAP.keys())
                all_suburbs.update(['nungambakkam', 'egmore', 'adyar', 'guindy', 'mylapore', 't. nagar', 'anna nagar', 'velachery'])
                
                for s in all_suburbs:
                    if re.search(rf'\b{re.escape(s)}\b', q_lower):
                        target_loc = s
                        break
            
            if target_loc:
                # Noise stripping: remove common filler words
                noise_words = ['the', 'area', 'city', 'district', 'near', 'around', 'region', 'locality', 'part of', 'colleges', 'college']
                for word in noise_words:
                    target_loc = re.sub(rf'\b{word}\b', '', target_loc).strip()
                
                # Check area map for corridors like OMR/ECR
                target_suburbs = CHENNAI_AREA_MAP.get(target_loc, [target_loc])
                
                if target_loc:
                    for c in colleges:
                        loc_str = c.get('details', {}).get('Location', '').lower()
                        # Match if target matches or any mapped suburb matches
                        if target_loc in loc_str or any(sub in loc_str for sub in target_suburbs):
                            found_colleges.append(c)

            if found_colleges:
                loc_title = target_loc.title() if target_loc else "the specified area"
                lines = [f"📍 **Colleges found in/near {loc_title}**:\n"]
                for c in found_colleges:
                    lines.append(f"- **{c['name']}** ({c.get('details', {}).get('Location', '')})")
                return {
                    'text': "\n".join(lines),
                    'sources': _map_sources_to_names([c['key'] for c in found_colleges]),
                    'intent': intent,
                    'type': 'location_search',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, intent)
                }

        # 6. FACILITY Handler
        if intent == 'facility':
            facility_keywords = [
                'medical', 'center', 'lab', 'wifi', 'library', 'sports', 'gym', 'clinic',
                'red cross', 'yrc', 'ncc', 'nss', 'club', 'society', 'activity', 'activities',
                'canteen', 'cafeteria', 'transport', 'bus'
            ]
            target_facility = next((f for f in facility_keywords if f in query.lower()), None)
            
            # --- Pattern A: Specific college facility ---
            if college_keys and target_facility:
                college = get_college_by_key(college_keys[0])
                if college:
                    details = college.get('details', {})
                    search_text = " ".join([str(v) for v in details.values()]).lower()
                    
                    if target_facility in search_text:
                        found_in_key = next((k for k, v in details.items() if target_facility in str(v).lower()), "Details")
                        return {
                            'text': f"✅ Yes, **{college['name']}** has **{target_facility.title()}** facilities/activities.\n\n**Information**: {details.get(found_in_key)}",
                            'sources': _map_sources_to_names([college['key']]),
                            'intent': intent,
                            'type': 'facility_verified',
                            'verified': True,
                            'suggestions': suggest_refined_query(query, intent)
                        }

            # --- Pattern B: Global facility search (Which college has X?) ---
            if target_facility and not college_keys:
                all_colls = get_all_colleges()
                found_hits = []
                for c in all_colls:
                    details = c.get('details', {})
                    # Look specifically in fields likely to contain clubs/facilities
                    search_fields = ['Facilities', 'Activities', 'Clubs', 'About', 'Extra-Curricular']
                    # Also fallback to full detail search if no matches in specific fields
                    found = False
                    for field in search_fields:
                        if target_facility in str(details.get(field, '')).lower():
                            found_hits.append((c, details.get(field)))
                            found = True
                            break
                    if not found:
                        # Full scan
                        for k, v in details.items():
                            if k not in search_fields and target_facility in str(v).lower():
                                found_hits.append((c, v))
                                break
                
                if found_hits:
                    lines = [f"✅ **Colleges with {target_facility.title()}**:\n"]
                    for c, info in found_hits[:6]:
                        # Truncate info if too long
                        display_info = (info[:100] + "...") if len(str(info)) > 100 else info
                        lines.append(f"- **{c['name']}**: {display_info}")
                    
                    return {
                        'text': "\n".join(lines),
                        'sources': _map_sources_to_names([h[0]['key'] for h in found_hits]),
                        'intent': intent,
                        'type': 'global_facility_search',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }

        # 7. Specialized Metadata Handlers (Direct DB access)
        if intent in ['hostel', 'about', 'admission', 'placement', 'fee', 'course']:
            course = extract_course(query)
            
            # --- New: Colleges offering a specific course ---
            if intent == 'course' and not college_keys and course:
                # User is asking "MBA colleges" or "colleges with engineering"
                all_colleges = get_all_colleges()
                
                # Check for area filter (e.g. "Engineering in OMR")
                target_area = next((k for k in CHENNAI_AREA_MAP.keys() if k in q_lower), None)
                suburbs = CHENNAI_AREA_MAP.get(target_area, []) if target_area else []
                
                offering = []
                target_norm = _normalize(course)
                for c in all_colleges:
                    # Filter by location if area specified
                    if target_area:
                        loc = c.get('details', {}).get('Location', '').lower()
                        if target_area not in loc and not any(s in loc for s in suburbs):
                            continue

                    # Check if any course in this college matches the requested course
                    for c_info in c['courses']:
                        c_name_norm = _normalize(c_info.get('course', ''))
                        c_spec_norm = _normalize(c_info.get('specialization', ''))
                        
                        if target_norm in c_name_norm or target_norm in c_spec_norm:
                            offering.append(c)
                            break
                
                if offering:
                    lines = [f"✅ **Colleges offering {course.upper()}**:\n"]
                    for c in offering[:8]:
                        # Find the first matching course to get duration
                        duration = "N/A"
                        fee_str = "Contact for Fee"
                        for c_info in c['courses']:
                            if course.lower() in c_info.get('course', '').lower() or \
                               course.lower() in c_info.get('specialization', '').lower():
                                duration = f"{c_info.get('duration_years', 'N/A')} yrs"
                                fee = c_info.get('annual_fees_inr')
                                if fee:
                                    fee_str = f"₹{fee:,.0f}/yr" if isinstance(fee, (int, float)) else str(fee)
                                break
                        
                        if intent == 'fee':
                            lines.append(f"- **{c['name']}**: {fee_str} ({duration})")
                        else:
                            lines.append(f"- **{c['name']}** (Duration: {duration})")
                    
                    return {
                        'text': "\n".join(lines) + f"\n\n_Found {len(offering)} verified institutions._",
                        'sources': _map_sources_to_names([c['key'] for c in offering[:5]]),
                        'intent': intent,
                        'type': 'course_availability_list',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }

            # --- New: Colleges offering a specific course fees (multi-match) ---
            if intent == 'fee' and not college_keys and course:
                all_colleges = get_all_colleges()
                
                target_area = next((k for k in CHENNAI_AREA_MAP.keys() if k in q_lower), None)
                suburbs = CHENNAI_AREA_MAP.get(target_area, []) if target_area else []
                
                target_norm = _normalize(course)
                matches = []
                for c in all_colleges:
                    if target_area:
                        loc = c.get('details', {}).get('Location', '').lower()
                        if target_area not in loc and not any(s in loc for s in suburbs):
                            continue

                    for c_info in c.get('courses', []):
                        c_name_norm = _normalize(c_info.get('course', ''))
                        c_spec_norm = _normalize(c_info.get('specialization', ''))
                        
                        if target_norm in c_name_norm or target_norm in c_spec_norm:
                            # Strict Degree filtering (e.g., prevent B.Tech showing up for B.Sc)
                            if 'bsc' in q_lower.replace('.', '') and ('btech' in c_name_norm or 'be' in c_name_norm):
                                continue
                            if ('btech' in q_lower.replace('.', '') or re.search(r'\bbe\b', q_lower)) and 'bsc' in c_name_norm:
                                continue
                            matches.append((c, c_info))
                
                if matches:
                    valid_matches = [m for m in matches if isinstance(m[1].get('annual_fees_inr'), (int, float))]
                    
                    # Superlative detection
                    is_expensive = any(w in q_lower for w in ['expensive', 'highest', 'max', 'most', 'costliest'])
                    is_cheap = any(w in q_lower for w in ['cheap', 'lowest', 'min', 'affordable'])

                    if is_expensive and valid_matches:
                        valid_matches.sort(key=lambda x: x[1]['annual_fees_inr'], reverse=True)
                        matches = [valid_matches[0]]
                        prefix = f"📈 **Most Expensive {course.upper()} Course**:\n"
                    elif is_cheap and valid_matches:
                        valid_matches.sort(key=lambda x: x[1]['annual_fees_inr'])
                        matches = [valid_matches[0]]
                        prefix = f"📉 **Cheapest {course.upper()} Course**:\n"
                    else:
                        valid_matches.sort(key=lambda x: x[1]['annual_fees_inr'])
                        matches = valid_matches[:10]
                        prefix = f"💰 **Fee Comparison for {course.upper()}**:\n"
                    
                    lines = [prefix]
                    for c, c_info in matches:
                        fee = c_info.get('annual_fees_inr')
                        fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else "Contact College"
                        exact_course = f"{c_info.get('course', '')} {c_info.get('specialization', '')}".strip()
                        lines.append(f"- **{c['name']}** ({exact_course}): {fee_fmt}/yr")
                    
                    return {
                        'text': "\n".join(lines),
                        'sources': _map_sources_to_names([m[0]['key'] for m in matches[:5]]),
                        'intent': intent,
                        'type': 'course_fee_list',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }

            if college_keys:
                # If a specific college is mentioned, provide its verified data directly
                target_key = college_keys[0]
                college = get_college_by_key(target_key)
                
                if college:
                    # 7a. Course Table (Always single college)
                    if intent == 'course':
                        batch_filter = detect_batch_filter(query)
                        return {
                            'text': _format_course_table(college, batch_filter),
                            'sources': _map_sources_to_names([target_key]),
                            'intent': intent,
                            'type': 'course_details',
                            'verified': True,
                            'suggestions': suggest_refined_query(query, intent)
                        }

                    # 7b. Fee intent — no specific course → show full fee table
                    if intent == 'fee' and not course:
                        batch_filter = detect_batch_filter(query)
                        return {
                            'text': _format_course_table(college, batch_filter),
                            'sources': _map_sources_to_names([target_key]),
                            'intent': intent,
                            'type': 'full_fee_table',
                            'verified': True,
                            'suggestions': suggest_refined_query(query, intent)
                        }

                    # 7c. Specific Course Fee (Single college)
                    if intent == 'fee' and course:
                        target_norm = _normalize(course)
                        matches = []
                        for ci in college.get('courses', []):
                            c_name_norm = _normalize(ci.get('course', ''))
                            c_spec_norm = _normalize(ci.get('specialization', ''))
                            
                            if target_norm in c_name_norm or target_norm in c_spec_norm:
                                matches.append(ci)

                        if matches:
                            # ── Shift I/II detection ──
                            shift_match = re.search(r'shift\s*(ii|2|i|1)', q_lower)
                            shift_label = None
                            if shift_match:
                                raw = shift_match.group(1).lower()
                                shift_label = 'II' if raw in ('ii', '2') else 'I'

                            # ── Govt/Mgmt Quota detection ──
                            quota_label = None
                            if re.search(r'govt\s*quota|government\s*quota', q_lower):
                                quota_label = 'Govt Quota'
                            elif re.search(r'mgmt\s*quota|management\s*quota', q_lower):
                                quota_label = 'Mgmt Quota'

                            # ── Sort by fee (cheapest first) for consistent Shift I = cheapest logic ──
                            if len(matches) > 1:
                                matches.sort(key=lambda x: x.get('annual_fees_inr', 0) if isinstance(x.get('annual_fees_inr'), (int, float)) else 0)

                            # ── Apply quota filter first (highest priority) ──
                            if quota_label:
                                quota_filtered = [ci for ci in matches
                                                  if quota_label.lower() in ci.get('course', '').lower()]
                                if quota_filtered:
                                    filtered = quota_filtered
                                else:
                                    filtered = matches  # fall back if no match in course name
                            # ── Then apply shift filter ──
                            elif shift_label and len(matches) >= 2:
                                filtered = [matches[0]] if shift_label == 'I' else [matches[-1]]
                            elif shift_label and len(matches) == 1:
                                filtered = matches
                            else:
                                filtered = matches

                            qualifier = f" ({quota_label})" if quota_label else (f" (Shift {shift_label})" if shift_label else "")
                            lines = [f"💰 **{course.upper()} Fee at {college['name']}{qualifier}**:\n"]
                            for ci in filtered:
                                fee = ci.get('annual_fees_inr')
                                fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
                                lines.append(f"- **{ci.get('course', 'N/A')} ({ci.get('specialization', 'N/A')})**: {fee_fmt} per year")

                            if not quota_label and not shift_label and len(matches) > 1:
                                lines.append("\n_ℹ️ Multiple batches/quotas available. Specify **Govt Quota** or **Mgmt Quota** for exact fee._")

                            return {
                                'text': "\n".join(lines),
                                'sources': _map_sources_to_names([target_key]),
                                'intent': intent,
                                'type': 'specific_course_fee',
                                'verified': True,
                                'suggestions': suggest_refined_query(query, intent)
                            }
        
        # 8. HIGH-INTEGRITY DIRECT ANSWERS (Accreditation, Affiliation, Admission)
        # Shifted to separate block for clarity and improved routing
        if any(w in q_lower for w in ['accredit', 'naac', 'nba', 'autonomous', 'deemed', 'affiliated', 'university of']):
            # Option A: Global affiliation search (e.g. "which colleges are affiliated with University of Madras")
            if any(w in q_lower for w in ['affiliated', 'university of']):
                uni_match = re.search(r'(?:affiliated\s+with|university\s+of)\s+([a-zA-Z\s]+)', query, re.IGNORECASE)
                uni_name = uni_match.group(1).strip().lower() if uni_match else None
                if not uni_name and 'madras' in q_lower: uni_name = 'madras'
                
                if uni_name:
                    all_c = get_all_colleges()
                    matches = [c for c in all_c if uni_name in str(c['details'].get('Type', '')).lower()]
                    if matches:
                        lines = [f"🎓 **Colleges Affiliated with/associated with {uni_name.upper()}**:\n"]
                        for m in matches: lines.append(f"- **{m['name']}**")
                        return {
                            'text': "\n".join(lines),
                            'sources': _map_sources_to_names([m['key'] for m in matches]),
                            'intent': 'about',
                            'type': 'affiliation_search',
                            'verified': True,
                            'suggestions': suggest_refined_query(query, 'about')
                        }

            # Option B: Specific college accreditation lookup
            if college_keys:
                col = get_college_by_key(college_keys[0])
                if col:
                    acc = col['details'].get('Accreditation', 'N/A')
                    if acc == 'NA': acc = "No formal NAAC/NBA accreditation listed in records."
                    typ = col['details'].get('Type', 'N/A')
                    return {
                        'text': f"🏛️ **{col['name']}** Information:\n\n- **Type**: {typ}\n- **Accreditation**: {acc}",
                        'sources': _map_sources_to_names([col['key']]),
                        'intent': 'about',
                        'type': 'accreditation_direct',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, 'about')
                    }

        # 9. ADMISSION MODE Direct Answer (e.g. "Does SSN have TNEA?")
        admission_keywords = ['tnea', 'counselling', 'neet', 'entrance', 'merit', 'management quota']
        target_mode = next((kw for kw in admission_keywords if kw in q_lower), None)
        
        if intent == 'admission' and college_keys and target_mode:
            col = get_college_by_key(college_keys[0])
            if col:
                details = col.get('details', {})
                adm_info = str(details.get('Admission Mode', '')).lower()
                
                if target_mode in adm_info:
                    return {
                        'text': f"✅ **Yes**, **{col['name']}** accepts/offers **{target_mode.upper()}**.\n\n**Details**: {details.get('Admission Mode')}",
                        'sources': _map_sources_to_names([col['key']]),
                        'intent': intent,
                        'type': 'admission_direct',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }
                else:
                    return {
                        'text': f"❌ **No**, I don't see **{target_mode.upper()}** listed as an admission mode for **{col['name']}**.\n\n**Current Admission Info**: {details.get('Admission Mode', 'N/A')}",
                        'sources': _map_sources_to_names([col['key']]),
                        'intent': intent,
                        'type': 'admission_direct_negative',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }

        # 10. General Metadata (Supports multiple colleges)
        if intent in ['hostel', 'about', 'admission', 'placement', 'fee']:
            mapping = {
                'hostel': ('Hostel Available', "🏡 **Hostel Information for {name}**:\n{val}"),
                'about': ('About', "ℹ️ **About {name}**:\n{val}"),
                'admission': ('Admission Mode', "📝 **Admission Details & Eligibility for {name}**:\n{val}"),
                'placement': ('PLACEMENT DATA', "💼 **Placement Statistics for {name}**:\n{val}"),
                'fee': ('Popular Courses', "💰 **Fee structure for {name}** typically varies by course (e.g., {val}). Please ask for a specific course fee.")
            }
            
            field_key, template = mapping.get(intent, (None, None))
            if field_key:
                # 🚨 FIX: Prevent generic metadata lookup if a specific course is detected!
                if intent == 'fee' and extract_course(query):
                    logger.debug("[Legacy] Specific course detected in fee query. Bypassing generic metadata.")
                else:
                    # ── NEW: Detailed Institutional Report (Rule 5) ──
                    # Triggered by "details", "info", "overall", "everything", "full" etc.
                    report_trig = ['detail', 'deat', 'info', 'overall', 'everything', 'full', 'summary']
                    if college_keys and intent in ('about', 'directory') and any(w in q_lower for w in report_trig):
                        college = get_college_by_key(college_keys[0])
                        if college:
                            return {
                                'text': _format_detailed_report(college),
                                'sources': _map_sources_to_names([college['key']]),
                                'intent': intent,
                                'type': 'institutional_report',
                                'verified': True,
                                'suggestions': suggest_refined_query(query, intent)
                            }

                    results_text = []
                    found_keys = []
                    
                    for key in college_keys:
                        c_data = get_college_by_key(key)
                        if not c_data: continue
                        
                        val = c_data.get('details', {}).get(field_key)
                        if val:
                            results_text.append(template.format(name=c_data['name'], val=val))
                            found_keys.append(key)
                    
                    if results_text:
                        return {
                            'text': "\n\n---\n\n".join(results_text),
                            'sources': _map_sources_to_names(found_keys),
                            'intent': intent,
                            'type': 'direct_database_response_multi',
                            'verified': True,
                            'suggestions': suggest_refined_query(query, intent)
                        }

        # 7.5. COLLEGE DETAIL FULL-TEXT SCANNER
        # Only runs for non-comparison intents where a specific college is mentioned
        if college_keys and intent not in ('comparison', 'ranking', 'directory'):
            col_data = get_college_by_key(college_keys[0])
            if col_data:
                details = col_data.get('details', {})
                # Extract meaningful words from query (4+ chars, skip common words)
                _stopwords = {'does', 'have', 'what', 'tell', 'about', 'the', 'this', 'that',
                              'with', 'from', 'list', 'show', 'give', 'college', 'campus'}
                query_keywords = [
                    w.lower().strip('?!.,') for w in query.split()
                    if len(w) >= 4 and w.lower().strip('?!.,') not in _stopwords
                ]
                
                matched_field = None
                matched_val = None
                for field_name, field_val in details.items():
                    val_str = str(field_val).lower()
                    # Check if any query keyword appears in this field
                    if any(kw in val_str for kw in query_keywords if len(kw) > 3):
                        matched_field = field_name
                        matched_val = str(field_val)
                        break
                
                if matched_field and matched_val:
                    # Format Yes/No for boolean-style questions
                    q_lower_clean = q_lower.strip('?')
                    kw_found = [kw for kw in query_keywords if kw in matched_val.lower()]
                    if any(q_lower.startswith(w) for w in ['does', 'do', 'is ', 'has ', 'can ', 'are ']):
                        answer_prefix = f"✅ **Yes**, {col_data['name']} has information about **{', '.join(kw_found)}**.\n\n"
                    else:
                        answer_prefix = f"🔍 **{matched_field}** at **{col_data['name']}**:\n\n"
                    
                    return {
                        'text': answer_prefix + matched_val,
                        'sources': _map_sources_to_names([college_keys[0]]),
                        'intent': intent,
                        'type': 'detail_scan',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }
                
                # If nothing matched but a college was mentioned, produce a clear negative
                if query_keywords and not matched_field:
                    return {
                        'text': f"❌ I don't have specific information about **{'** or **'.join(query_keywords)}** at **{col_data['name']}** in my dataset. You may want to check the college's official website.",
                        'sources': _map_sources_to_names([college_keys[0]]),
                        'intent': intent,
                        'type': 'not_found_for_college',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, intent)
                    }

        # 8. Attempt STRICT Database Match as Fallback
        # This matches specific questions like "What is the motto of MCC?"
        qa_match, confidence = find_strict_qa_match(query)
        if qa_match:
            verified = True
            if qa_match.related_college:
                # Double-verify against the actual college data
                verified = verify_response(qa_match.answer, [str(qa_match.related_college.data)])
            if verified:
                return {
                    'text': qa_match.answer,
                    'sources': _map_sources_to_names([qa_match.related_college.slug]) if qa_match.related_college else [],
                    'intent': 'strict_qa',
                    'type': 'database_match',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, intent)
                }

        # 6. Semantic Fallback with Strict Verification
        results = semantic_search(query, top_k=5)
        if not results:
            return {'text': "I'm sorry, I couldn't find verified information to answer that accurately.", 'sources': [], 'intent': intent, 'type': 'no_result'}

        context_docs = [doc['text'] for _, doc in results]
        source_keys = list(set(doc['college']['key'] for _, doc in results))
        
        verification_data = context_docs.copy()
        for _, doc in results[:2]:
            college = get_college_by_key(doc['college']['key'])
            if college: verification_data.append(college) # Pass raw dict, not string!

        groq_answer = ask_groq(_SYSTEM_PROMPT, query, context_docs, context_history)
        if groq_answer and verify_response(groq_answer, verification_data):
            # Include suggestions in the final output
            suggestions = suggest_refined_query(query, intent, context_docs)
            return {
                'text': groq_answer, 
                'sources': _map_sources_to_names(source_keys), 
                'intent': intent, 
                'type': 'verified_generation', 
                'verified': True,
                'suggestions': suggestions
            }

        # If Groq gives an answer, show it with AI-assisted tag regardless of verification
        if groq_answer:
            return {
                'text': groq_answer,
                'sources': _map_sources_to_names(source_keys),
                'intent': intent,
                'type': 'ai_assisted',
                'verified': False,
                'suggestions': suggest_refined_query(query, intent)
            }
        
        return {
            'text': "❌ I couldn't find verified information for that query. Try asking about a specific college (e.g., 'Does MCC have a hostel?') or browse the college directory.",
            'sources': [], 'intent': intent, 'type': 'no_result', 'verified': False
        }

    except Exception as e:
        logger.exception(f"Responder Error: {e}")
        return {'text': "⚠️ I encountered an error while retrieving verified data. Please try again later.", 'intent': 'error', 'type': 'error', 'sources': []}
