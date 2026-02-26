import logging
import re
from typing import List, Optional
from .loader import get_college_by_key, get_all_colleges
from .ranker import rank_colleges
from .router import QueryAnalysis

# Lazy imports to avoid circular dependencies if any
# We'll import these from the original responder until they are moved
from .utils import (
    _format_detailed_report, 
    _format_course_table, 
    _format_comparison, 
    _format_fee_comparison,
    _format_ranking,
    _format_college_directory,
    _map_sources_to_names,
    suggest_refined_query,
    detect_batch_filter,
    extract_course,
    _normalize,
    CHENNAI_AREA_MAP,
    find_college_in_db,        # 🚨 NEW
    normalize_course_string     # 🚨 NEW
)

logger = logging.getLogger(__name__)

# 🚨 UPDATED GLOBAL FOR BULLETPROOF LOOKUP
COLLEGES = get_all_colleges()

class BaseIntentHandler:
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        raise NotImplementedError("Handlers must implement the handle method.")

class AboutHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        if not matched_college_keys:
            return {
                'text': "Sorry, I couldn't find a specific college matching your query. Could you please specify which institution you're asking about?",
                'sources': [], 'intent': analysis.intent, 'type': 'error_not_found', 'verified': True
            }
        
        # 🚨 Use the new bulletproof lookup
        college = find_college_in_db(matched_college_keys[0], COLLEGES)
        if not college:
            return {'text': "Sorry, I couldn't find detailed information for that institution.", 'sources': [], 'intent': analysis.intent, 'type': 'error_not_found', 'verified': True}
            
        return {
            'text': _format_detailed_report(college),
            'sources': _map_sources_to_names([college['key']]),
            'intent': analysis.intent,
            'type': 'institutional_report',
            'verified': True,
            'suggestions': suggest_refined_query(query, analysis.intent)
        }

class FeeHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        # Collect ALL requested courses as a list
        requested_courses: List[str] = list(analysis.raw_courses) if analysis.raw_courses else []
        if not requested_courses:
            single = extract_course(query)
            if single:
                requested_courses = [single]
        else:
            # Enrich bare degree from Groq (e.g., "B.Sc") with specialization from query
            # The improved extract_course captures degree+specialization
            enriched = extract_course(query)
            if enriched and len(enriched) > len(requested_courses[0]):
                requested_courses[0] = enriched
        course = requested_courses[0] if requested_courses else None

        # --- NEW: Shift Logic Detect (Intra-college comparison) ---
        has_shift_comparison = 'shift i' in q_lower and 'shift ii' in q_lower
        
        if has_shift_comparison:
            if not matched_college_keys:
                return {
                    'text': "I see you're looking to compare Shift I and Shift II fees. Could you please specify **which college** you would like to check? (e.g., 'Compare shifts at MCC')",
                    'intent': 'fee', 'sources': [], 'type': 'error_missing_entity', 'verified': True
                }
            
            college = get_college_by_key(matched_college_keys[0])
            if college:
                lines = [f"📊 **Shift Fees Comparison for {college['name']}**\n"]
                
                s1 = [c for c in college['courses'] if 'shift i' in c.get('course', '').lower()]
                s2 = [c for c in college['courses'] if 'shift ii' in c.get('course', '').lower()]
                
                if s1:
                    lines.append("🔹 **Shift I (Aided/General)**:")
                    for c in s1[:5]:
                        lines.append(f"- {c.get('course')} ({c.get('specialization','')}): ₹{c.get('annual_fees_inr',0):,.0f}")
                
                if s2:
                    lines.append("\n🔸 **Shift II (Self-Financed)**:")
                    for c in s2[:5]:
                        lines.append(f"- {c.get('course')} ({c.get('specialization','')}): ₹{c.get('annual_fees_inr',0):,.0f}")
                
                if not s1 and not s2:
                    # --- Dynamic Batch Fallback ---
                    # Collect all meaningful unique batch values this college actually has
                    _GENERIC_BATCHES = {'general', 'regular', '', 'n/a', 'none', 'na', '-'}
                    all_batches = set()
                    for c in college['courses']:
                        b = str(c.get('batch', '')).strip()
                        if b.lower() not in _GENERIC_BATCHES and b:
                            all_batches.add(b)
                    # Also collect quota types from course name/specialization if batch is empty
                    for c in college['courses']:
                        for field in ('course', 'specialization'):
                            val = str(c.get(field, '')).lower()
                            if 'govt quota' in val or 'government quota' in val:
                                all_batches.add('Govt Quota')
                            if 'mgmt quota' in val or 'management quota' in val:
                                all_batches.add('Management Quota')
                            if 'aided' in val:
                                all_batches.add('Aided')
                            if 'self-financed' in val or 'self financed' in val:
                                all_batches.add('Self-Financed')

                    if all_batches:
                        batch_list = ', '.join(sorted(all_batches))
                        lines.append(
                            f"⚠️ **{college['name']}** does not offer Shift I / Shift II batches.\n\n"
                            f"However, they do offer courses under: **{batch_list}**.\n\n"
                            f"Would you like me to compare fees across those instead? "
                            f"_(e.g., \"Compare Aided vs Self-Financed fees at {college['name']}\")_"
                        )
                    else:
                        lines.append(
                            f"⚠️ No Shift I/II or separate batch breakdown found for **{college['name']}**. "
                            "All courses appear to be offered under a single uniform fee structure."
                        )
                else:
                    lines.append("\n_Note: Shift I is generally Aided (lower fees), while Shift II is Self-Financed._")

                return {
                    'text': "\n".join(lines),
                    'sources': _map_sources_to_names([college['key']]),
                    'intent': 'fee', 'type': 'shift_comparison', 'verified': True
                }

        # --- Batch/Shift Filter Detection ---
        batch_filter = None
        if 'shift i' in q_lower or 'aided' in q_lower or 'day college' in q_lower:
            batch_filter = 'shift i'
        elif 'shift ii' in q_lower or 'self-financed' in q_lower or 'evening' in q_lower:
            batch_filter = 'shift ii'

        # Scenario 1: Multi-college comparison
        if len(matched_college_keys) >= 2 or (analysis.is_comparison and len(matched_college_keys) >= 2):
            return {
                'text': _format_fee_comparison(matched_college_keys, course),
                'sources': _map_sources_to_names(matched_college_keys),
                'intent': analysis.intent,
                'type': 'fee_comparison',
                'verified': True,
                'suggestions': suggest_refined_query(query, 'fee')
            }
            
        # Scenario 2: Specific College Fee
        if matched_college_keys:
            college = get_college_by_key(matched_college_keys[0])
            
            if not college:
                return {
                    'text': "❌ I couldn't identify the college. Please specify the full name or abbreviation (e.g., SSN, HITS).", 
                    'intent': 'fee', 'sources': []
                }

            # 🚨 FIX 4: Multi-Condition Fee Filter 🚨
            # Try to find a number in the user's query (e.g., "1,40,000" or "140000")
            price_match = re.search(r'₹?(\d{1,3}(?:,\d{3})*(?:,\d{3})?|\d+)', query)
            target_price = None
            if price_match:
                try:
                    target_price = int(price_match.group(1).replace(',', ''))
                except ValueError:
                    pass

            if not course:
                return {
                    'text': _format_course_table(college, batch_filter or detect_batch_filter(query)),
                    'sources': _map_sources_to_names([college['key']]),
                    'intent': analysis.intent,
                    'type': 'full_fee_table',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, 'fee')
                }
            # --- Scenario 2b: Multi-course loop --------------------------------
            else:
                # If only ONE course was requested, fall through to single-match logic;
                # otherwise iterate over all courses and combine results.
                if len(requested_courses) <= 1:
                    # Single-course path — Refined logic
                    target_norm = normalize_course_string(course)
                    kw_parts = target_norm.split()
                    matches_single = []
                    for ci in college.get('courses', []):
                        db_raw = f"{ci.get('course', '')} {ci.get('specialization', '')} {ci.get('stream', '')}"
                        db_norm = normalize_course_string(db_raw)
                        
                        if all(part in db_norm for part in kw_parts):
                            # Apply price filter if detected
                            if target_price:
                                fee = ci.get('annual_fees_inr')
                                if isinstance(fee, (int, float)) and int(fee) == target_price:
                                    matches_single.append(ci)
                            elif batch_filter:
                                if batch_filter.lower() in db_norm:
                                    matches_single.append(ci)
                            else:
                                matches_single.append(ci)

                    if matches_single:
                        matches_single.sort(key=lambda x: len(x.get('course','')) + len(x.get('specialization','')))
                        lines = [f"💰 **Fee Details for {college['name']}** - {course.upper()}\n"]
                        for c in matches_single[:10]:
                            fee = c.get('annual_fees_inr', 'N/A')
                            fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
                            lines.append(f"- **{c.get('course')}** ({c.get('specialization','—')}): **{fee_fmt}**/yr")
                        if batch_filter:
                            lines.append(f"\n_Note: Showing results only for **{batch_filter.upper()}**._")
                        return {
                            'text': "\n".join(lines),
                            'sources': _map_sources_to_names([college['key']]),
                            'intent': analysis.intent, 'type': 'specific_course_fee', 'verified': True,
                            'suggestions': suggest_refined_query(query, 'fee')
                        }
                    return {
                        'text': f"❌ I found **{college['name']}**, but couldn't find fee data for **{course.upper()}**. They might not offer this specific program.",
                        'sources': _map_sources_to_names([college['key']]),
                        'intent': 'fee', 'type': 'error_missing_course', 'verified': True
                    }

                else:
                    # Multiple courses requested — loop through each
                    lines = [f"💰 **Fee Details for {college['name']}**\n"]
                    found_any = False
                    for req_course in requested_courses:
                        target_norm = normalize_course_string(req_course)
                        kw_parts = target_norm.split()
                        course_matches = []
                        for ci in college.get('courses', []):
                            db_raw = f"{ci.get('course', '')} {ci.get('specialization', '')} {ci.get('stream', '')}"
                            db_norm = normalize_course_string(db_raw)
                            
                            if all(part in db_norm for part in kw_parts):
                                if batch_filter and batch_filter.lower() not in db_norm:
                                    continue
                                course_matches.append(ci)

                        if course_matches:
                            found_any = True
                            course_matches.sort(key=lambda x: len(x.get('course','')))
                            best = course_matches[0]
                            fee = best.get('annual_fees_inr', 'N/A')
                            fee_fmt = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
                            lines.append(f"- **{req_course.upper()}** ({best.get('specialization','General')}): **{fee_fmt}**/yr")
                        else:
                            lines.append(f"- **{req_course.upper()}**: ⚠️ Not found at this college")

                    if batch_filter:
                        lines.append(f"\n_Note: Showing results only for **{batch_filter.upper()}**._")

                    return {
                        'text': "\n".join(lines),
                        'sources': _map_sources_to_names([college['key']]),
                        'intent': 'fee',
                        'type': 'multi_course_fee' if found_any else 'error_missing_course',
                        'verified': True,
                        'suggestions': suggest_refined_query(query, 'fee')
                    }
                
        # Scenario 3: Global/Course Search (Course specified, but no specific college)
        if course:
            # 🚨 FIX 3: Global Course Searcher Fallback 🚨
            # Check for B.Arch or generic course queries without naming a college
            if not matched_college_keys:
                target_norm = normalize_course_string(course)
                kw_parts = target_norm.split()
                found_colleges = []
                for college in get_all_colleges():
                    for cr in college.get("courses", []):
                        db_combined = f"{cr.get('course', '')} {cr.get('specialization', '')} {cr.get('stream', '')}"
                        db_normalized = normalize_course_string(db_combined)
                        if all(token in db_normalized for token in kw_parts):
                            fee = cr.get('annual_fees_inr', 'N/A')
                            fee_str = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
                            found_colleges.append(f"- **{college['name']}** ({cr.get('course')}) — {fee_str}/yr")
                            break
                
                if found_colleges:
                    return {
                        'text': f"✅ The following colleges offer **{course.upper()}**:\n\n" + "\n".join(found_colleges[:15]),
                        'sources': _map_sources_to_names([c.split('**')[1] for c in found_colleges[:3] if '**' in c]), # Rough mapping
                        'intent': analysis.intent, 'type': 'global_course_search', 'verified': True
                    }

            all_colleges = get_all_colleges()
            
            # Area awareness
            target_area = next((k for k in CHENNAI_AREA_MAP.keys() if k in q_lower), None)
            suburbs = CHENNAI_AREA_MAP.get(target_area, []) if target_area else []
            
            target_norm = normalize_course_string(course)
            kw_parts = target_norm.split()
            matches = []
            
            for c in all_colleges:
                # Filter by area if specified
                if target_area:
                    loc = c.get('details', {}).get('Location', '').lower()
                    if target_area not in loc and not any(s in loc for s in suburbs):
                        continue

                for c_info in c.get('courses', []):
                    db_raw = f"{c_info.get('course', '')} {c_info.get('specialization', '')}"
                    db_norm = normalize_course_string(db_raw)
                    
                    # Strict token matching logic
                    if all(token in db_norm for token in kw_parts):
                        # If user asked for B.Sc (BSC), filter out B.Tech/B.E matches
                        if 'bsc' in target_norm and ('btech' in db_norm or 'be' in db_norm):
                            continue
                        # If user asked for B.Tech/B.E, filter out B.Sc matches
                        if ('btech' in target_norm or 'be' in target_norm) and 'bsc' in db_norm:
                            continue
                        
                        matches.append((c, c_info))

            if matches:
                # Identify numeric fees for sorting
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
                    # Default list
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
                    'intent': analysis.intent,
                    'type': 'course_fee_list',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, analysis.intent)
                }

        # Scenario 4: Cross-College Range Search (e.g. "Courses under 50k")
        if analysis.metric_range and analysis.target_metric == 'fee' and not matched_college_keys:
            rmin, rmax = analysis.metric_range
            all_colleges = get_all_colleges()
            hits = []
            for c in all_colleges:
                for cr in c.get('courses', []):
                    fee = cr.get('annual_fees_inr')
                    if isinstance(fee, (int, float)) and rmin <= fee <= rmax:
                        hits.append((c, cr))
            
            if hits:
                hits.sort(key=lambda x: x[1]['annual_fees_inr'])
                lines = [f"💰 **Courses under ₹{rmax:,.0f} across verified colleges**:\n"]
                for c, cr in hits[:15]:
                    fee_fmt = f"₹{cr['annual_fees_inr']:,.0f}"
                    course_name = f"{cr.get('course', 'N/A')} {cr.get('specialization', '')}".strip()
                    lines.append(f"- **{c['name']}**: {course_name} — {fee_fmt}/yr")
                
                return {
                    'text': "\n".join(lines),
                    'sources': _map_sources_to_names([h[0]['key'] for h in hits[:5]]),
                    'intent': analysis.intent,
                    'type': 'cross_college_fee_range',
                    'verified': True,
                    'suggestions': suggest_refined_query(query, 'fee')
                }

        # Scenario 5: Error/Fallback
        return {
            'text': f"❌ I couldn't identify the college or finding verified fee information for **{course or 'that course'}**. Please specify a college name (e.g., 'Hindustan bsc fees').",
            'sources': [], 'intent': analysis.intent, 'type': 'error_missing_entity', 'verified': True
        }

class RankingHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        criteria = {}
        
        is_highest_query = any(w in q_lower for w in ['highest', 'max', 'most', 'top', 'best'])
        is_lowest_query = any(w in q_lower for w in ['cheapest', 'cheepest', 'lowest', 'lowes', 'lowst', 'affordable', 'budget', 'cheap', 'min'])
        
        # --- 1. Define Weights for the base rank_colleges function ---
        if any(w in q_lower for w in ['placement', 'job', 'recruit']):
            criteria = {'placement_weight': 0.8, 'package_weight': 0.15, 'affordability_weight': 0.05}
        elif any(w in q_lower for w in ['fee', 'cost', 'price', 'cheap', 'affordable']) or is_lowest_query:
            criteria = {'affordability_weight': 0.9, 'placement_weight': 0.1}
        elif any(w in q_lower for w in ['package', 'salary', 'lpa']):
            criteria = {'package_weight': 0.8, 'placement_weight': 0.2}
        elif is_highest_query:
            criteria = {'package_weight': 0.5, 'placement_weight': 0.4, 'affordability_weight': 0.1}
        
        course = analysis.raw_courses[0] if analysis.raw_courses else None
        
        # Detect Institution Type (e.g., Autonomous)
        inst_type = None
        if 'autonomous' in q_lower:
            inst_type = 'Autonomous'
            
        ranked = rank_colleges(criteria, course_keyword=course, institution_type=inst_type)
        
        # --- NEW: Strict Range Pre-Filtering ---
        if analysis.metric_range and ranked:
            rmin, rmax = analysis.metric_range
            metric = analysis.target_metric or ('placement' if 'placement' in q_lower else 'fee')
            
            if metric == 'placement':
                ranked = [r for r in ranked if rmin <= r[2]['placement_pct'] <= rmax]
            elif metric == 'fee':
                ranked = [r for r in ranked if rmin <= r[2]['avg_annual_fee'] <= rmax]
            elif metric == 'package':
                ranked = [r for r in ranked if rmin <= r[2]['avg_package_lpa'] <= rmax]
        
        # --- 2. Final Sorting Overrides ---
        if ranked:
            if any(w in q_lower for w in ['cheap', 'affordable', 'budget']):
                ranked.sort(key=lambda x: x[2]['avg_annual_fee'])
            elif any(w in q_lower for w in ['expensive', 'costly', 'pricey']):
                ranked.sort(key=lambda x: x[2]['avg_annual_fee'], reverse=True)
            elif is_highest_query:
                if any(w in q_lower for w in ['placement', 'recruit', 'job']):
                    ranked.sort(key=lambda x: x[2]['placement_pct'], reverse=True)
                elif any(w in q_lower for w in ['package', 'salary', 'lpa']):
                    ranked.sort(key=lambda x: x[2]['avg_package_lpa'], reverse=True)
                else:
                    ranked.sort(key=lambda x: x[0], reverse=True)
            elif is_lowest_query:
                if any(w in q_lower for w in ['placement', 'recruit', 'job']):
                    ranked.sort(key=lambda x: x[2]['placement_pct'])
                elif any(w in q_lower for w in ['package', 'salary', 'lpa']):
                    ranked.sort(key=lambda x: x[2]['avg_package_lpa'])
                else:
                    # Specific course fee sorting if available
                    ranked.sort(key=lambda x: x[2].get('min_fee', x[2]['avg_annual_fee']))

        if ranked:
            header = None
            if analysis.metric_range:
                metric_name = analysis.target_metric.capitalize() if analysis.target_metric else "Value"
                header = f"📊 **Colleges with {metric_name} between {analysis.metric_range[0]} and {analysis.metric_range[1]}**"
            elif is_lowest_query and not course:
                header = "📉 **Verified Most Affordable Colleges (Avg Annual Fee)**"
            elif is_highest_query and not course:
                header = "🏆 **Best Ranked Colleges (Overall Performance)**"
            
            if 'autonomous' in q_lower:
                header = "🏆 **Top Ranked Autonomous Colleges**"

            if ranked and course:
                # STRICT COURSE-LOCK: Filter to colleges that actually offer the course.
                # Use keyword-part matching (same as FeeHandler) to find the exact matched course.
                course_norm = _normalize(course)
                kw_parts = course_norm.split()
                course_locked = []
                for entry in ranked:
                    college_data = entry[1]  # raw college dict
                    matched_ci = None
                    for ci in college_data.get('courses', []):
                        db_full = _normalize(f"{ci.get('course','')} {ci.get('specialization','')} {ci.get('stream','')}")
                        if all(p in db_full for p in kw_parts):
                            matched_ci = ci
                            break
                    if matched_ci:
                        # Overwrite best_course_name in metrics so formatter shows the correct course
                        entry[2]['best_course_name'] = f"{matched_ci.get('course','')} ({matched_ci.get('specialization','')})"
                        entry[2]['best_course_fee'] = matched_ci.get('annual_fees_inr', entry[2]['avg_annual_fee'])
                        course_locked.append(entry)
                ranked = course_locked
                header = f"🏆 **Best Colleges for {course.upper()}**"


            return {
                'text': _format_ranking(ranked, course, custom_header=header),
                'sources': _map_sources_to_names([r[1]['key'] for r in ranked[:5 if not course else 15]]),
                'intent': analysis.intent,
                'type': 'ranking',
                'verified': True,
                'suggestions': suggest_refined_query(query, analysis.intent)
            }
        return {'text': f"I couldn't find any colleges matching those criteria{' for ' + course.upper() if course else ''}.", 'intent': 'general', 'sources': []}
ProxyHandler = BaseIntentHandler # Placeholder for backward compatibility

class DirectoryHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        return {
            'text': _format_college_directory(),
            'sources': _map_sources_to_names([c['key'] for c in get_all_colleges()]),
            'intent': analysis.intent,
            'type': 'college_directory',
            'verified': True
        }

class LocationHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        target_loc = analysis.target_location

        # --- GUARDRAIL: College alias mis-classified as location ---
        # If router.py's Entity Collision Resolver somehow didn't fire, catch it here.
        from .router import ALIASES
        if target_loc and target_loc.lower().strip() in ALIASES:
            alias = target_loc.lower().strip()
            logger.warning(
                f"[LocationHandler] Guardrail triggered: '{alias}' is a college, not a location. "
                f"Redirecting to FeeHandler."
            )
            # Fix analysis in-place so the correct handler gets proper data
            analysis.target_location = None
            if alias not in [r.lower() for r in analysis.raw_colleges]:
                analysis.raw_colleges.append(alias)
            from .router import extract_colleges_fuzzy
            matched_college_keys = extract_colleges_fuzzy(analysis.raw_colleges)
            # Re-route to the most appropriate handler based on query keywords
            if any(w in q_lower for w in ['fee', 'fees', 'cost', 'price', 'cheap', 'afford']):
                return FeeHandler().handle(query, analysis, matched_college_keys)
            return AboutHandler().handle(query, analysis, matched_college_keys)

        # 1. Direct College Location Lookup
        if matched_college_keys and not target_loc:
            col_data = [get_college_by_key(k) for k in matched_college_keys if get_college_by_key(k)]
            if len(col_data) == 1:
                return {
                    'text': f"📍 **{col_data[0]['name']}** is located at:\n\n{col_data[0]['details'].get('Location', 'N/A')}",
                    'sources': _map_sources_to_names([col_data[0]['key']]),
                    'intent': 'location', 'type': 'location_direct', 'verified': True,
                    'suggestions': suggest_refined_query(query, 'location')
                }
            # Multi-college location (Comparison)
            lines = ["📍 **Location Comparison**:\n"]
            for c in col_data:
                lines.append(f"- **{c['name']}**: {c['details'].get('Location', 'N/A')}")
            return {
                'text': "\n".join(lines),
                'sources': _map_sources_to_names(matched_college_keys),
                'intent': 'location', 'type': 'location_comparison', 'verified': True,
                'suggestions': suggest_refined_query(query, 'location')
            }
        
        # 2. Area Mapping & Global Search
        AREA_MAP = {
            'omr': ['padur', 'kelambakkam', 'navalur', 'sholinganallur', 'omr', 'rajiv gandhi salai'],
            'north chennai': ['vyasarpadi', 'tiruvottiyur', 'perambur', 'tondiarpet', 'madhavaram', 'north chennai'],
            'adyar': ['adyar', 'guindy', 'besant nagar'],
            'siruseri': ['siruseri', 'omr', 'sipcot'],
            'tambaram': ['tambaram', 'chromepet', 'selaiyur'],
            'vandalur': ['vandalur', 'rathinamangalam', 'perungalathur'],
            'egmore': ['egmore', 'kilpauk', 'nungambakkam'],
            'nungambakkam': ['nungambakkam', 'kodambakkam', 'chetpet', 't nagar', 't. nagar'],
            'anna nagar': ['anna nagar', 'mogappair', 'ambattur'],
            'mylapore': ['mylapore', 'triplicane', 'royapettah'],
            'velachery': ['velachery', 'madipakkam', 'pallikaranai'],
        }

        # 🚨 FIX: Fallback — extract area from raw query if Groq missed target_location
        if not target_loc:
            for area_name in AREA_MAP.keys():
                if area_name in q_lower:
                    target_loc = area_name
                    break
            # Also try common area patterns
            if not target_loc:
                area_match = re.search(r'(?:in|near|around|at)\s+([a-z\s]+?)(?:\s*\?|$)', q_lower)
                if area_match:
                    candidate = area_match.group(1).strip()
                    # Check if candidate matches any known area
                    for area_name in AREA_MAP.keys():
                        if area_name in candidate or candidate in area_name:
                            target_loc = area_name
                            break

        search_terms = [target_loc.lower()] if target_loc else []
        if target_loc and target_loc.lower() in AREA_MAP:
            search_terms.extend(AREA_MAP[target_loc.lower()])
            
        if search_terms:
            colleges = get_all_colleges()
            hits = []
            for c in colleges:
                loc_val = c['details'].get('Location', '').lower()
                if any(term in loc_val for term in search_terms):
                    hits.append(c)
            
            if hits:
                lines = [f"📍 **Colleges located in/near {target_loc.title() if target_loc else 'requested area'}**:\n"]
                for c in hits:
                    lines.append(f"- **{c['name']}** ({c['details'].get('Location', 'N/A')})")
                return {
                    'text': "\n".join(lines),
                    'sources': _map_sources_to_names([c['key'] for c in hits[:5]]),
                    'intent': 'location', 'type': 'area_search_success', 'verified': True
                }

        return {
            'text': f"I don't have explicit information about colleges in **{target_loc.title() if target_loc else 'that specific area'}**. Please try another location or college name.",
            'sources': [], 'intent': 'location', 'type': 'not_found', 'verified': False
        }

class FacilityHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        
        # Expanded keywords including student club/association terminology
        facility_keywords = [
            'medical', 'center', 'lab', 'wifi', 'library', 'sports', 'gym', 'clinic',
            'red cross', 'yrc', 'ncc', 'nss', 'club', 'society', 'activity', 'activities',
            'canteen', 'cafeteria', 'transport', 'bus', 'hostel',
            'association', 'cell', 'forum', 'committee'
        ]
        
        # Primary keyword extraction
        key_fac = next((f for f in facility_keywords if f in q_lower), None)
        
        if matched_college_keys:
            college = get_college_by_key(matched_college_keys[0])
            if college:
                details = college['details']
                # Search in dict values
                found_field = next((k for k, v in details.items() if key_fac and key_fac in str(v).lower()), None)
                # Search in dict keys
                if not found_field:
                    found_field = next((k for k in details.keys() if key_fac and key_fac in k.lower()), None)
                
                if found_field:
                    return {
                        'text': f"✅ Yes, **{college['name']}** has information about **{key_fac.title() if key_fac else found_field}**:\n\n{details.get(found_field)}",
                        'sources': _map_sources_to_names([college['key']]),
                        'intent': 'facility', 'type': 'facility_verified', 'verified': True,
                        'suggestions': suggest_refined_query(query, 'facility')
                    }
                
        # ── Global Keyword Search ──
        if key_fac:
            all_colleges = get_all_colleges()
            hits = []
            for c in all_colleges:
                details = c.get('details', {})
                content = (f"{details.get('STUDENT CLUBS', '')} {details.get('Facilities', '')} {details.get('About', '')}").lower()
                if key_fac in content:
                    hits.append(c)
            
            if hits:
                lines = [f"🔍 **Colleges mentioning '{key_fac.title()}'**:\n"]
                for h in hits[:10]:
                    lines.append(f"- **{h['name']}**")
                return {
                    'text': "\n".join(lines),
                    'sources': _map_sources_to_names([h['key'] for h in hits[:5]]),
                    'intent': 'facility', 'type': 'global_facility_search', 'verified': True
                }

        return {
            'text': f"I don't have explicit information about **{key_fac or 'those student activities'}** in my records. Please try specifying a college.",
            'sources': [], 'intent': 'facility', 'type': 'not_found', 'verified': False
        }

class AdmissionHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        if matched_college_keys:
            college = get_college_by_key(matched_college_keys[0])
            if not college:
                return {'text': "Please specify a college to see admission details.", 'intent': 'admission', 'sources': []}
            adm = college['details'].get('Admission Mode', 'N/A')
            return {
                'text': f"📝 **Admission Information for {college['name']}**:\n\n{adm}",
                'sources': _map_sources_to_names([college['key']]),
                'intent': 'admission', 'type': 'admission_info', 'verified': True,
                'suggestions': suggest_refined_query(query, 'admission')
            }
class AttributeSearchHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        # Define the keywords we are looking for
        keywords = ['nba', 'naac', 'autonomous', 'a++', 'accreditation']
        clean_query = query.lower()
        found_keyword = next((kw for kw in keywords if kw in clean_query), None)
        
        if not found_keyword:
            return {"text": "I couldn't identify the specific accreditation (NBA, NAAC, etc.) you are asking about.", "intent": "attribute_search", "sources": []}
        
        matched_colleges = []
        all_colleges = get_all_colleges()
        for college in all_colleges:
            # Safely grab the accreditation and type strings from the JSON
            accreditation = str(college.get('details', {}).get('Accreditation', '')).lower()
            college_type = str(college.get('details', {}).get('Type', '')).lower()
            
            if found_keyword in accreditation or found_keyword in college_type:
                matched_colleges.append(f"- **{college.get('details', {}).get('College Name', college['name'])}**")
        
        if matched_colleges:
            return {
                "text": f"✅ Colleges with **{found_keyword.upper()}** status:\n\n" + "\n".join(matched_colleges),
                "intent": "attribute_search",
                "type": "attribute_list",
                "sources": _map_sources_to_names([c['key'] for c in all_colleges if any(m in c['name'] for m in matched_colleges[:5])]),
                "verified": True
            }
        else:
            return {"text": f"I couldn't find any colleges matching **{found_keyword.upper()}**.", "intent": "attribute_search", "sources": [], "verified": True}

class ComparisonHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        if len(matched_college_keys) < 2:
            # ── NEW: Auto-Selection for Comparison queries without explicit colleges ──
            # If user asks "Compare BCA fees" or "Compare MBA colleges", we pick the top 2
            if analysis.raw_courses:
                course = analysis.raw_courses[0]
                # Rank colleges for this course using rank_colleges helper
                # We use default criteria (weighted towards placement/fee balance)
                ranked = rank_colleges(course_keyword=course)
                if len(ranked) >= 2:
                    matched_college_keys = [r[1]['key'] for r in ranked[:2]]
                    logger.debug(f"[Comparison] Auto-selected {matched_college_keys} for course '{course}'")
                else:
                    return {"type": "error", "text": f"I don't have enough verified data for multiple colleges offering **{course.upper()}** to provide a comparison.", "intent": "comparison", "sources": []}
            else:
                return {"type": "error", "text": "Please specify at least two valid colleges to compare (e.g., 'Compare HITS and SSN').", "intent": "comparison", "sources": []}
        
        # 🚨 Use the new bulletproof lookup for all compared colleges
        compared_colleges = [find_college_in_db(key, COLLEGES) for key in matched_college_keys]
        # Filter out any Nones if a college truly wasn't found
        compared_colleges = [c for c in compared_colleges if c] 
        
        if len(compared_colleges) < 2:
             return {"type": "error", "text": "I couldn't find enough verified data in the database for those specific colleges.", "intent": "comparison", "sources": []}

        # Build Headers safely
        headers = "| Feature | " + " | ".join([c.get('college_details', {}).get('College Name', 'Unknown') for c in compared_colleges]) + " |"
        separator = "|---|" + "|".join(["---" for _ in compared_colleges]) + "|"
        
        rows = []
        
        # 🚨 IF THEY ASKED FOR A SPECIFIC COURSE (e.g., "WCC vs MCC B.Com fees")
        if analysis.raw_courses:
            target_course = normalize_course_string(analysis.raw_courses[0])
            course_row = f"| Fee for {analysis.raw_courses[0].upper()} | "
            
            for c in compared_colleges:
                found_fee = "N/A"
                for crs in c.get('courses', []):
                    db_course = normalize_course_string(f"{crs.get('course', '')} {crs.get('specialization', '')}")
                    # Token match
                    if all(token in db_course for token in target_course.split()):
                        found_fee = f"₹{crs.get('annual_fees_inr', 'N/A')}/yr"
                        break # Found it, stop looking
                course_row += found_fee + " | "
            
            rows.append(course_row)
            
        else:
            # 🚨 GENERAL COMPARISON (No specific course named)
            from .utils import get_standard_attribute
            rows.append("| Type | " + " | ".join([get_standard_attribute(c, 'Type') for c in compared_colleges]) + " |")
            rows.append("| Fees | " + " | ".join([get_standard_attribute(c, 'fee') for c in compared_colleges]) + " |")
            rows.append("| Placement | " + " | ".join([get_standard_attribute(c, 'placement') for c in compared_colleges]) + " |")
            rows.append("| Hostel | " + " | ".join([get_standard_attribute(c, 'hostel') for c in compared_colleges]) + " |")

        table_string = "\n".join([headers, separator] + rows)
        
        return {"type": "comparison_table", "text": f"📊 Here is your comparison:\n\n{table_string}", "intent": "comparison", "sources": _map_sources_to_names(matched_college_keys), "verified": True}

class GreetingHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        all_colleges = get_all_colleges()
        college_names = sorted([c['name'] for c in all_colleges])
        bulleted_list = "\n".join([f"- {name}" for name in college_names])
        
        greeting_text = (
            "👋 Hello! I'm CollegeBot, your AI college enquiry assistant!\n\n"
            "I can help you with fees, placements, courses, and admissions for the following institutions:\n\n"
            f"{bulleted_list}\n\n"
            "What would you like to know?"
        )
        
        return {
            'text': greeting_text,
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

class PlacementHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        if matched_college_keys:
            # 🚨 Use the new bulletproof lookup
            col = find_college_in_db(matched_college_keys[0], COLLEGES)
            if not col:
                return {'text': "I couldn't retrieve the placement information for that specific college. Please try again or ask about another institution.", 'intent': 'placement', 'sources': []}
            
            val = col.get('details', {}).get('PLACEMENT DATA', 'No placement data found.')
            pkg = col.get('details', {}).get('Average Package', 'N/A')
            text = f"💼 **Placement Statistics for {col['name']}**:\n\n{val}\n\n**Average Package/Statistics:** {pkg}"
            return {
                'text': text, 'sources': _map_sources_to_names([col['key']]),
                'intent': 'placement', 'type': 'general', 'verified': True,
                'suggestions': suggest_refined_query(query, 'placement')
            }
        
        # Range Filtering for Placement
        from .ranker import rank_colleges
        ranked = rank_colleges({'package_weight': 0.8, 'placement_weight': 0.2})
        
        if analysis.metric_range and len(analysis.metric_range) == 2:
            rmin, rmax = analysis.metric_range
            metric = analysis.target_metric or 'placement'
            if metric == 'placement':
                ranked = [r for r in ranked if rmin <= r[2]['placement_pct'] <= rmax]
            elif metric == 'package':
                ranked = [r for r in ranked if rmin <= r[2]['avg_package_lpa'] <= rmax]
        
        if ranked:
            header = None
            if analysis.metric_range and len(analysis.metric_range) == 2:
                metric_name = analysis.target_metric.capitalize() if analysis.target_metric else "Placement"
                header = f"📊 **Colleges with {metric_name} between {analysis.metric_range[0]} and {analysis.metric_range[1]}**"
                
            return {
                'text': _format_ranking(ranked, custom_header=header), 
                'sources': _map_sources_to_names([r[1]['key'] for r in ranked[:5]]),
                'intent': 'ranking', 'type': 'ranking', 'verified': True,
                'suggestions': suggest_refined_query(query, 'ranking')
            }
        
        return {'text': "No colleges found matching that placement range.", 'intent': 'placement', 'sources': []}

class CheapestHandler(BaseIntentHandler):
    """Find most affordable colleges/courses."""
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        course = analysis.raw_courses[0] if analysis.raw_courses else extract_course(query)
        all_colleges = get_all_colleges()

        # SCENARIO A: Group Cheapest (2+ colleges named)
        if len(matched_college_keys) >= 2:
            winner = None
            lowest_fee = float('inf')
            for key in matched_college_keys:
                college = get_college_by_key(key)
                if not college: continue
                target_courses = college['courses']
                if course:
                    norm_c = _normalize(course)
                    kw = norm_c.split()
                    target_courses = [c for c in target_courses if all(p in _normalize(f"{c.get('course','')} {c.get('specialization','')}") for p in kw)]
                for cr in target_courses:
                    fee = cr.get('annual_fees_inr')
                    if isinstance(fee, (int, float)) and 0 < fee < lowest_fee:
                        lowest_fee = fee
                        winner = {
                            'college_name': college['details'].get('College Name', college['name']),
                            'course_name': f"{cr.get('course')} {cr.get('specialization','')}".strip(),
                            'fee': fee, 'key': college['key']
                        }
            if winner:
                return {
                    'type': 'general', 
                    'text': f"🏆 The cheapest option between those colleges is **{winner['course_name']}** at **{winner['college_name']}** for **₹{winner['fee']:,.0f}/yr**.",
                    'sources': _map_sources_to_names([winner['key']]),
                    'intent': 'cheapest', 'verified': True
                }
            return {'text': "I couldn't find enough verified fee data to compare those institutions.", 'intent': 'cheapest', 'sources': []}

        # SCENARIO B: Single College Cheapest (1 college named)
        if len(matched_college_keys) == 1:
            college = get_college_by_key(matched_college_keys[0])
            if college:
                valid_courses = [c for c in college['courses'] if isinstance(c.get('annual_fees_inr'), (int, float)) and c.get('annual_fees_inr') > 0]
                if course:
                    norm_c = _normalize(course)
                    kw_parts = norm_c.split()
                    valid_courses = [c for c in valid_courses if all(p in _normalize(f"{c.get('course','')} {c.get('specialization','')}") for p in kw_parts)]
                if valid_courses:
                    valid_courses.sort(key=lambda x: x['annual_fees_inr'])
                    top = valid_courses[:3]
                    lines = [f"📉 **Most Affordable {'(' + course.upper() + ') ' if course else ''}Courses at {college['name']}**\n"]
                    for i, c in enumerate(top, 1):
                        lines.append(f"{i}. **{c['course']}** ({c.get('specialization','General')}): **₹{c['annual_fees_inr']:,.0f}/yr**")
                    return {
                        'text': "\n".join(lines), 'sources': _map_sources_to_names([college['key']]),
                        'intent': 'cheapest', 'type': 'general', 'verified': True
                    }
                return {'text': f"❌ No verified courses found matching **{course.upper() if course else ''}** at **{college['name']}**.", 'intent': 'cheapest', 'sources': []}

        # SCENARIO C: Global Course Cheapest (Course provided, no college)
        if course and not matched_college_keys:
            target_norm = normalize_course_string(course)
            kw_parts = target_norm.split()
            matches = []
            for college in all_colleges:
                for cr in college.get('courses', []):
                    db_raw = f"{cr.get('course', '')} {cr.get('specialization', '')} {cr.get('stream', '')}"
                    db_norm = normalize_course_string(db_raw)
                    if all(part in db_norm for part in kw_parts):
                        fee = cr.get('annual_fees_inr')
                        if isinstance(fee, (int, float)) and fee > 0:
                            matches.append({
                                'college': college['name'], 'course': f"{cr.get('course')} {cr.get('specialization','')}".strip(),
                                'fee': fee, 'key': college['key']
                            })
            if matches:
                matches.sort(key=lambda x: x['fee'])
                top_3 = matches[:5]
                table = "| College | Exact Course | Fee (₹) |\n|---|---|---|\n"
                for m in top_3: table += f"| {m['college']} | {m['course']} | {m['fee']:,.0f} |\n"
                return {
                    'text': f"🏆 Here are the cheapest verified options for **{course.upper()}**:\n\n{table}",
                    'intent': 'cheapest', 'type': 'general', 'sources': _map_sources_to_names([m['key'] for m in top_3[:3]]), 'verified': True
                }
            return {'text': f"❌ I couldn't find any colleges offering verified fees for **{course.upper()}**.", 'intent': 'cheapest', 'sources': []}

        # SCENARIO D: Absolute Global Cheapest (No college, no course)
        lowest_fee = float('inf')
        winner_c = None
        winner_col = None
        for college in all_colleges:
            for cr in college.get('courses', []):
                fee = cr.get('annual_fees_inr')
                if isinstance(fee, (int, float)) and 0 < fee < lowest_fee:
                    lowest_fee = fee
                    winner_c = cr
                    winner_col = college
        if winner_col:
            return {
                'text': f"🏆 The absolute cheapest course across all verified colleges is **{winner_c['course']}** ({winner_c.get('specialization','General')}) at **{winner_col['name']}** for **₹{lowest_fee:,.0f}/yr**.",
                'sources': _map_sources_to_names([winner_col['key']]), 'intent': 'cheapest', 'type': 'general', 'verified': True
            }

        return {"text": "I couldn't find any verified course fees to determine the cheapest option.", "intent": "cheapest", "sources": []}

class MostExpensiveHandler(BaseIntentHandler):
    """Find most premium colleges/courses."""
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        q_lower = query.lower()
        course = analysis.raw_courses[0] if analysis.raw_courses else extract_course(query)

        # --- Scoped to a specific college ---
        if matched_college_keys:
            college = get_college_by_key(matched_college_keys[0])
            if college:
                valid_courses = [c for c in college['courses'] if isinstance(c.get('annual_fees_inr'), (int, float))]
                if course:
                    norm_c = _normalize(course)
                    kw_parts = norm_c.split()
                    valid_courses = [c for c in valid_courses
                                     if all(p in _normalize(f"{c.get('course','')} {c.get('specialization','')}") for p in kw_parts)]

                if valid_courses:
                    valid_courses.sort(key=lambda x: x['annual_fees_inr'], reverse=True)
                    top = valid_courses[:3]  # Show top 3
                    lines = [f"📈 **Most Expensive {'(' + course.upper() + ') ' if course else ''}Courses at {college['name']}**\n"]
                    for i, c in enumerate(top, 1):
                        fee_fmt = f"₹{c['annual_fees_inr']:,.0f}"
                        lines.append(f"{i}. **{c['course']}** ({c.get('specialization','General')}): **{fee_fmt}/yr**")
                    return {
                        'text': "\n".join(lines),
                        'sources': _map_sources_to_names([college['key']]),
                        'intent': 'most_expensive', 'type': 'general', 'verified': True
                    }
                return {
                    'text': f"❌ No courses found{' matching ' + course.upper() if course else ''} at **{college['name']}**.",
                    'sources': _map_sources_to_names([college['key']]),
                    'intent': 'most_expensive', 'type': 'error_missing_course', 'verified': True
                }

        # --- Global most expensive ranking ---
        ranked = rank_colleges({'affordability_weight': 1.0}, course_keyword=course)
        ranked.sort(key=lambda x: x[2]['avg_annual_fee'], reverse=True)

        if ranked:
            header = f"📈 **Most Premium (Highest Fee) Colleges{' for ' + course.upper() if course else ''}**"
            return {
                'text': _format_ranking(ranked, course, custom_header=header),
                'sources': _map_sources_to_names([r[1]['key'] for r in ranked[:5]]),
                'intent': 'ranking', 'type': 'expensive', 'verified': True
            }
        return {'text': "No courses found to list premium rankings.", 'intent': 'ranking', 'sources': []}

class HostelHandler(BaseIntentHandler):
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        if matched_college_keys:
            col = get_college_by_key(matched_college_keys[0])
            if not col:
                return {'text': "Please specify a college to check hostel availability.", 'intent': 'hostel', 'sources': []}
            val = col['details'].get('Hostel Available', 'No hostel data found.')
            return {
                'text': f"🏡 **Hostel Information for {col['name']}**:\n\n{val}",
                'sources': _map_sources_to_names([col['key']]),
                'intent': 'hostel', 'type': 'hostel_info', 'verified': True,
                'suggestions': suggest_refined_query(query, 'hostel')
            }
        return {'text': "Please specify a college to check hostel availability.", 'intent': 'hostel', 'sources': []}

class CourseHandler(BaseIntentHandler):
    """Handles course-related queries: listings, availability, and course details."""
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        course_kw = extract_course(query)
        level = analysis.degree_level

        # Single college: show its course table
        if matched_college_keys:
            col = get_college_by_key(matched_college_keys[0])
            if col:
                original_courses = col['courses']

                def _is_ug(course_name: str) -> bool:
                    n = course_name.strip().upper()
                    return n.startswith('B.') or any(n == x for x in ['BCA', 'BBA', 'BCOM', 'BSW']) or 'UG' in n

                def _is_pg(course_name: str) -> bool:
                    n = course_name.strip().upper()
                    return n.startswith('M.') or any(n == x for x in ['MCA', 'MBA', 'MCOM', 'MSW']) or 'PG' in n

                if level == 'UG':
                    filtered = [c for c in original_courses if _is_ug(c.get('course', ''))]
                elif level == 'PG':
                    filtered = [c for c in original_courses if _is_pg(c.get('course', ''))]
                else:
                    filtered = original_courses

                # If filter produced empty results, give a graceful fallback
                if level and not filtered:
                    opposite_level = 'PG' if level == 'UG' else 'UG'
                    opposite_filter = _is_pg if level == 'UG' else _is_ug
                    opposite_courses = [c for c in original_courses if opposite_filter(c.get('course', ''))]

                    msg = f"⚠️ I couldn't find any **{level}** courses for **{col['name']}**."
                    if opposite_courses:
                        examples = ", ".join(set(c.get('course','') for c in opposite_courses[:5]))
                        msg += f" However, they do offer **{opposite_level}** programs such as: {examples}."
                    else:
                        msg += " Please check directly with the college for their current offerings."

                    return {
                        'text': msg,
                        'sources': _map_sources_to_names([col['key']]),
                        'intent': 'course', 'type': 'no_degree_match', 'verified': True,
                        'suggestions': suggest_refined_query(query, 'course')
                    }

                col['courses'] = filtered
                level_label = f"**{level} Courses** at" if level else "Courses at"
                res = {
                    'text': f"🎓 {level_label} **{col['name']}**:\n\n" + _format_course_table(col, course_filter=course_kw),
                    'sources': _map_sources_to_names([col['key']]),
                    'intent': 'course', 'type': 'course_table', 'verified': True,
                    'suggestions': suggest_refined_query(query, 'course')
                }
                col['courses'] = original_courses
                return res

        # No specific college but has a course keyword or level → list colleges offering it
        if course_kw or level:
            all_colleges = get_all_colleges()
            matches = []
            search_label = course_kw.upper() if course_kw else (f"{level} Programs" if level else "Courses")
            
            kw_parts = normalize_course_string(course_kw).split() if course_kw else []
            
            for c in all_colleges:
                temp_courses = c.get('courses', [])
                if level == 'UG':
                    temp_courses = [cr for cr in temp_courses if cr.get('batch', '').strip().upper() == 'UG' or cr.get('course', '').strip().upper().startswith('B.')]
                elif level == 'PG':
                    temp_courses = [cr for cr in temp_courses if cr.get('batch', '').strip().upper() == 'PG' or cr.get('course', '').strip().upper().startswith('M.')]
                
                for cr in temp_courses:
                    db_raw = f"{cr.get('course','')} {cr.get('stream','')} {cr.get('specialization','')}"
                    db_norm = normalize_course_string(db_raw)
                    
                    if not kw_parts or all(part in db_norm for part in kw_parts):
                        fee = cr.get('annual_fees_inr', 'N/A')
                        fee_str = f"₹{fee:,.0f}" if isinstance(fee, (int, float)) else str(fee)
                        matches.append(f"- **{c['name']}** — {cr.get('course','N/A')} ({cr.get('specialization','General')}) — {fee_str}/yr")
                        break  # one per college

            if matches:
                header = f"🎓 **Colleges offering {search_label}:**\n\n"
                # Use find_college_in_db to get friendly names correctly
                sources = []
                for m in matches[:5]:
                    col_name = m.split('**')[1]
                    matched_col = next((col for col in all_colleges if col['name'] == col_name), None)
                    if matched_col:
                        sources.append(matched_col['key'])

                return {
                    'text': header + "\n".join(matches[:15]),
                    'sources': _map_sources_to_names(sources),
                    'intent': 'course', 'type': 'course_search', 'verified': True
                }

        # Fallback: general course directory
        return {
            'text': "Please specify a college or course name for me to look up. Example: \"BCA courses\" or \"Courses at WCC\".",
            'sources': [], 'intent': 'course', 'type': 'course_prompt', 'verified': True,
            'suggestions': ["BCA courses", "MBA colleges", "Courses at SSN"]
        }

class RAGQAHandler(BaseIntentHandler):
    """
    The Ultimate RAG Fallback.
    Reads the entire college JSON and sends it to the LLM to answer
    general or unknown questions.
    """
    def handle(self, query: str, analysis: QueryAnalysis, matched_college_keys: List[str]) -> dict:
        if not matched_college_keys:
            return {
                "text": "Could you please specify which college you are asking about? (e.g., 'Does HITS have a club?')",
                "intent": "general", "sources": [], "type": "error_missing_entity", "verified": True
            }
        
        # Get the first matched college
        # 🚨 Use the new bulletproof lookup
        target_college_key = matched_college_keys[0]
        college_data = find_college_in_db(target_college_key, COLLEGES)
        
        if not college_data:
            return {
                "text": "I couldn't find the data for that specific institution.",
                "intent": "general", "sources": [], "type": "error_not_found", "verified": True
            }

        # Convert the entire JSON to a string context
        context_string = str(college_data)
        
        # Build the strict prompt for the AI
        system_prompt = """
        You are CollegeBot, a helpful assistant.
        Answer the user's question based ONLY on the following JSON data. 
        If the answer is NOT in the data, reply exactly with: "Sorry, I don't have that specific information in my current records."
        Do not make up facts. Be concise.
        """
        
        # Import ask_groq locally to stay decoupled
        from .groq_client import ask_groq
        
        answer = ask_groq(
            system_prompt=system_prompt,
            user_message=query,
            context_docs=[context_string]
        )
        
        if not answer or "Sorry, I don't have that specific information" in answer:
            return {
                "text": "Sorry, I don't have that specific information in my current records for this college.",
                "sources": _map_sources_to_names([target_college_key]),
                "intent": "general", "type": "no_info", "verified": True
            }

        return {
            "text": answer,
            "sources": _map_sources_to_names([target_college_key]),
            "intent": "general",
            "type": "rag_fallback",
            "verified": True
        }



