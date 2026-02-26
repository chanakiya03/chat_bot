"""
Enterprise Anti-Hijack Firewall
Sanitizes LLM-extracted entities to prevent context bleed
and hallucinated college/course injection from chat history.
"""
import re
import logging
from typing import List, Optional, Tuple
from .router import ALIASES, QueryAnalysis
from .utils import extract_course

logger = logging.getLogger(__name__)

# Superlative / Global keywords that signal a cross-database query
GLOBAL_TRIGGERS = [
    'cheapest', 'lowest', 'most expensive', 'highest', 'top', 'best',
    'all', 'list', 'show me', 'which colleges', 'affordable', 'most', 'compare'
]

# Intent keyword maps for precision routing
_FEE_KEYWORDS      = ['cheap', 'expens', 'fee', 'cost', 'afford']
_LOCATION_KEYWORDS  = ['locat', 'where', 'in ', 'area']
_FACILITY_KEYWORDS  = ['club', 'facilit', 'ncc', 'nss', 'wifi', 'hostel']
_DIRECTORY_KEYWORDS = ['list all', 'over all', 'directory', 'details of all']
_PLACEMENT_KEYWORDS = ['package', 'placement', 'highest', 'salary', 'lpa', 'recruit']
_COMPARISON_KEYWORDS = ['compare', 'vs', 'versus', 'better']
_DISCOVERY_KEYWORDS = ['autonomous', 'deemed', 'accreditation', 'women', 'affiliated', 'grade', 'naac', 'nba']


def _verify_colleges_in_text(query_lower: str, raw_colleges: list) -> list:
    """
    Phase 1: Verify that LLM-extracted colleges ACTUALLY appear in query text.
    Prevents history bleed where the LLM injects previous colleges into a new query.
    """
    verified = []
    for rc in raw_colleges:
        rc_clean = rc.lower().strip()
        # Trust if it's a known alias OR if significant words (>3 chars) appear in query
        if rc_clean in ALIASES or any(w in query_lower for w in rc_clean.split() if len(w) > 3):
            verified.append(rc)
    return verified


def _catch_missed_aliases(query_lower: str, colleges_in_text: list, raw_colleges: list):
    """
    Phase 2: Hard-catch aliases the LLM missed via regex word-boundary matching.
    Mutates raw_colleges in-place to add discovered aliases.
    Returns the updated colleges_in_text list.
    """
    found = list(colleges_in_text)  # copy
    for alias, db_key in ALIASES.items():
        if re.search(rf'\b{re.escape(alias)}\b', query_lower):
            if alias not in [c.lower() for c in found]:
                found.append(alias)
                if alias not in raw_colleges:
                    raw_colleges.append(alias)
    return found


def _route_intent_by_colleges(query_lower: str, num_colleges: int, current_intent: str) -> str:
    """
    Phase 3: Precision intent routing based on how many colleges are mentioned.
    
    0 colleges → Global search (ranking/fee/location/facility/directory)
    1 college  → Direct lookup (placement/fee)
    2+ colleges → Comparison or fee comparison
    """
    if num_colleges == 0:
        # E.g., "Top engineering colleges", "Cheapest BCA", "Which colleges have NCC"
        # 🚨 FIX: Check discovery keywords FIRST (NAAC, NBA, autonomous, etc.)
        # so they route to attribute_search instead of being swallowed by 'ranking'.
        if any(w in query_lower for w in _DISCOVERY_KEYWORDS):
            return 'attribute_search'

        # Superlative Priority: 'best', 'top', 'highest', 'ranking'
        if any(w in query_lower for w in ['best', 'top', 'highest', 'ranking']):
            return 'ranking'
            
        if any(w in query_lower for w in _FEE_KEYWORDS):
            # Special Case: "Compare MBA fees" with 0 colleges should go to specialized handler
            if 'compare' in query_lower:
                return 'cheapest'
            return 'fee'
        elif any(w in query_lower for w in _LOCATION_KEYWORDS):
            return 'location'
        elif any(w in query_lower for w in _FACILITY_KEYWORDS):
            return 'facility'
        elif any(w in query_lower for w in _DIRECTORY_KEYWORDS):
            return 'directory'
        else:
            return 'ranking'

    elif num_colleges == 1:
        # E.g., "Highest package at HITS", "Most expensive course at WCC"
        if any(w in query_lower for w in _PLACEMENT_KEYWORDS):
            return 'placement'
        elif any(w in query_lower for w in _FEE_KEYWORDS):
            return 'fee'
        return current_intent  # keep LLM's intent

    else:  # 2+
        # E.g., "Compare fee for SSN and HITS", "Which is better Loyola or WCC"
        if any(w in query_lower for w in _FEE_KEYWORDS):
            return 'fee'
        else:
            return 'comparison'


def sanitize_query(analysis: QueryAnalysis, matched_college_keys: List[str], query: str) -> Tuple[QueryAnalysis, List[str]]:
    """
    Master Entry Point — runs the full Anti-Hijack pipeline.
    
    1. Verify colleges actually exist in query text
    2. Hard-catch aliases the LLM missed
    3. Detect global/superlative queries (Phase 2 Strict Logic)
    4. Wipe hallucinated entities if global + not in text
    5. Override intent with precision routing
    
    Returns: (Sanitized Analysis, Sanitized College Keys)
    """
    q_lower = query.lower()

    # ── Phase 1: Verify colleges in text (LLM check) ──
    # We use analysis.raw_colleges as the "source" from LLM
    verified_raw = _verify_colleges_in_text(q_lower, analysis.raw_colleges)
    
    # ── Phase 2: Catch aliases the LLM missed (Regex check) ──
    # This also populates analysis.raw_colleges and returns verified names
    colleges_in_text = _catch_missed_aliases(q_lower, verified_raw, analysis.raw_colleges)

    # ── Phase 3: Detect actual course in query text ──
    actual_course = extract_course(query)

    # ── Phase 4: Phase 2 Global/Superlative Detection ──
    is_superlative = bool(re.search(
        r"cheapest|most\s*expensive|best|top|highest|lowest|most\s*affordable|premium|costly",
        q_lower, re.I
    ))
    is_global = bool(re.search(r"all|list|which|every|show\s+me", q_lower, re.I))
    is_comparison_discovery = 'compare' in q_lower and not colleges_in_text

    # If it's a cross-db search or comparison discovery and NO verified colleges were found in THIS text
    is_discovery = any(w in q_lower for w in ['which', 'colleges\s+have', 'colleges\s+with', 'list\s+colleges'])
    if (is_superlative or is_global or analysis.metric_range or is_discovery or is_comparison_discovery) and not colleges_in_text:
        logger.debug("[Firewall] Wiping context bleed for global/range/discovery query.")
        analysis.raw_colleges = []
        matched_college_keys = []
        
        # If a NEW course is explicitly mentioned in query text, it MUST override history
        if actual_course:
            logger.debug(f"[Firewall] Overriding history with new course: {actual_course}")
            analysis.raw_courses = [actual_course]
        elif not actual_course and not is_comparison_discovery:
            # Only wipe if it was pure bleed and NOT a comparison request (which might need a course)
            logger.debug("[Firewall] Wiping hallucinated courses from context bleed.")
            analysis.raw_courses = []

    # ── Phase 5: Precision intent routing ──
    # If LLM said 'general' or 'about' but it's clearly a ranking query
    current_intent = analysis.intent
    
    # Strict Cheapest/Most-Expensive Override
    # 🚨 FIX: Only force ranking when NO course is specified.
    # If a course IS specified, keep 'cheapest'/'most_expensive' so the specialized
    # handlers (CheapestHandler/MostExpensiveHandler) run their Scenario C logic.
    if re.search(r"cheapest|most\s*affordable|lowest\s*fees?", q_lower) and not matched_college_keys:
        if actual_course:
            analysis.intent = 'cheapest'  # Preserve cheapest for course-specific search
        else:
            analysis.intent = 'ranking'   # Global cheapest without course → ranking
    elif re.search(r"most\s*expensive|highest\s*fee|priciest|costliest", q_lower) and not matched_college_keys:
        if actual_course:
            analysis.intent = 'most_expensive'
        else:
            analysis.intent = 'ranking'
    else:
        analysis.intent = _route_intent_by_colleges(
            q_lower, len(matched_college_keys), current_intent
        )
    
    # Special Override: If target_metric is present, it's likely a ranking/placement intent
    if analysis.target_metric:
        if analysis.target_metric == 'placement':
            analysis.intent = 'placement'
        elif analysis.target_metric == 'fee':
            # If we have a range but no specific course/college, FeeHandler will now handle cross-college results
            analysis.intent = 'fee'
        elif analysis.target_metric == 'package':
            analysis.intent = 'placement'

    # Intent Override for Location
    if analysis.target_location:
        logger.debug(f"[Firewall] Forcing 'location' intent for target area: {analysis.target_location}")
        analysis.intent = 'location'

    return analysis, matched_college_keys
