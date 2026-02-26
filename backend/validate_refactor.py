"""Quick syntax + import validation for all engine modules."""
import ast
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

files = [
    'chatbot/engine/firewall.py',
    'chatbot/engine/handlers.py',
    'chatbot/engine/responder.py',
    'chatbot/engine/router.py',
    'chatbot/engine/ranker.py',
    'chatbot/engine/verifier.py',
    'chatbot/engine/utils.py',
    'chatbot/engine/search.py',
    'chatbot/engine/loader.py',
]

print("=== SYNTAX CHECK ===")
all_ok = True
for f in files:
    try:
        with open(f, encoding='utf-8') as fh:
            ast.parse(fh.read())
        print(f"  OK: {f}")
    except SyntaxError as e:
        print(f"  FAIL: {f}: {e}")
        all_ok = False

if all_ok:
    print("\nAll 9 modules: SYNTAX OK")
else:
    print("\nSome modules have syntax errors!")
    sys.exit(1)

# Django import check
print("\n=== IMPORT CHECK ===")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
try:
    import django
    django.setup()
    from chatbot.engine.firewall import sanitize_query
    from chatbot.engine.handlers import (
        AboutHandler, FeeHandler, RankingHandler, DirectoryHandler,
        GreetingHandler, LocationHandler, FacilityHandler, AdmissionHandler,
        ComparisonHandler, PlacementHandler, HostelHandler, CourseHandler
    )
    from chatbot.engine.responder import generate_response_advanced, generate_response_legacy
    from chatbot.engine.router import analyze_query_advanced, extract_colleges_fuzzy, ALIASES
    from chatbot.engine.ranker import rank_colleges
    from chatbot.engine.verifier import verify_response_advanced
    print("  OK: All imports resolved successfully")
    print(f"  OK: 12 handlers registered")
    print(f"  OK: ALIASES: {list(ALIASES.keys())}")
    print("\nFULL VALIDATION PASSED")
except Exception as e:
    print(f"  FAIL: Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
