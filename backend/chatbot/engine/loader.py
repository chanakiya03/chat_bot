import os
import json
import glob
import logging
import hashlib
from django.conf import settings
from django.utils.text import slugify
from chatbot.models import CollegeDetail

logger = logging.getLogger(__name__)

# Global knowledge base — loaded from DB
_knowledge_base = None

def get_file_hash(filepath):
    """Returns SHA256 hash of a file's content."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

def load_knowledge_base(force_reload=False):
    """
    Robust Loader: Loads from Disk first (fast/reliable) then attempts to enrich from DB.
    Ensures system works even if DB is locked or empty.
    """
    global _knowledge_base
    if _knowledge_base is not None and not force_reload:
        return _knowledge_base

    logger.info("Initializing knowledge base...")
    colleges = []
    documents = []
    college_slugs = {}
    
    # 1. Primary Load: Load everything from Disk JSON files
    data_dir = str(settings.COLLEGE_DATA_DIR)
    json_files = glob.glob(os.path.join(data_dir, '*_output.json'))
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            details = data.get('college_details', {})
            name = details.get('College Name', "")
            if not name:
                basename = os.path.basename(filepath).lower().replace('_output.json', '')
                name = basename.replace('_', ' ').title()
            
            slug = slugify(name)
            if slug in college_slugs:
                logger.warning(f"Duplicate college found on disk: {slug} (from {filepath}). Skipping.")
                continue
            
            college_entry = {
                'key': slug,
                'name': name or slug.title(),
                'details': details,
                'courses': data.get('courses', []),
                'is_verified': True, # Disk files are considered gold standard source
                'db_id': 0
            }
            colleges.append(college_entry)
            college_slugs[slug] = college_entry
            _add_to_corpus(documents, college_entry)
        except Exception as e:
            logger.error(f"Error loading {filepath} from disk: {e}")

    # 2. Enrichment Pass: Try to sync/enrich with Database if available
    try:
        from django.db import connection
        # Check if table exists without triggers/locks if possible
        db_colleges = CollegeDetail.objects.all()
        for db_college in db_colleges:
            if db_college.slug in college_slugs:
                college_slugs[db_college.slug]['db_id'] = db_college.id
                # Optionally sync DB data back to entry if DB is newer, 
                # but for this environment, Disk is safer.
            else:
                # Found something in DB NOT on disk? Add it.
                data = db_college.data
                college_entry = {
                    'key': db_college.slug,
                    'name': db_college.name,
                    'details': data.get('college_details', {}),
                    'courses': data.get('courses', []),
                    'is_verified': True,
                    'db_id': db_college.id
                }
                colleges.append(college_entry)
                college_slugs[db_college.slug] = college_entry
                _add_to_corpus(documents, college_entry)
    except Exception as e:
        logger.warning(f"Database enrichment skipped (possibly locked or empty): {e}")

    _knowledge_base = {
        'colleges': colleges,
        'documents': documents,
        'college_slugs': college_slugs,
    }
    
    logger.info(f"Knowledge base loaded: {len(colleges)} colleges total.")
    return _knowledge_base

def _load_from_disk_fallback():
    """Directly loads from JSON files if DB is empty."""
    colleges = []
    documents = []
    college_slugs = {}
    
    data_dir = str(settings.COLLEGE_DATA_DIR)
    json_files = glob.glob(os.path.join(data_dir, '*_output.json'))
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            slug = os.path.basename(filepath).replace('_output.json', '').replace('_', '-')
            name = data.get('college_details', {}).get('College Name', slug.capitalize())
            
            college_entry = {
                'key': slug,
                'name': name,
                'details': data.get('college_details', {}),
                'courses': data.get('courses', []),
                'is_verified': True,
                'db_id': 0
            }
            colleges.append(college_entry)
            college_slugs[slug] = college_entry
            _add_to_corpus(documents, college_entry)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            
    return colleges, documents, college_slugs

def _add_to_corpus(documents, college_entry):
    name = college_entry['name']
    details = college_entry['details']
    
    overview_text = f"College: {name} | Location: {details.get('Location', '')} | Type: {details.get('Type', '')} | About: {details.get('About', '')}"
    documents.append({
        'text': overview_text,
        'college': college_entry,
        'type': 'overview'
    })

    # Index all individual metadata fields as searchable blocks
    # This allows generic facility/detail searches to work via semantic fallback
    excluded_from_indexing = ['Column Name', 'College Name', 'Courses Offered', 'Popular Courses', 'About']
    for key, val in details.items():
        if key not in excluded_from_indexing and val and len(str(val)) > 1:
            documents.append({
                'text': f"College: {name} | {key.upper()}: {val}",
                'college': college_entry,
                'type': 'metadata',
                'meta_key': key
            })
    
    for course in college_entry['courses']:
        doc_text = f"College: {name} | Course: {course.get('course', '')} | Fee: {course.get('annual_fees_inr', '')}"
        documents.append({
            'text': doc_text,
            'college': college_entry,
            'type': 'course',
            'course': course
        })

def reload_knowledge_base():
    global _knowledge_base
    _knowledge_base = None
    return load_knowledge_base(force_reload=True)

def get_knowledge_base():
    return load_knowledge_base()

def get_all_colleges():
    kb = get_knowledge_base()
    return kb['colleges']

def get_college_by_key(key):
    kb = get_knowledge_base()
    return kb['college_slugs'].get(key.lower())
