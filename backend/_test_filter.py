import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.utils import _format_course_table, get_college_by_key

def test_filter():
    hits = get_college_by_key('hindustan-institute-of-technology-and-science-hits-chennai')
    if not hits:
        print("HITS data not found.")
        return

    # Scenario: "hits btech ai and ml"
    # CourseHandler extracts "btech ai and ml" as course_kw
    course_kw = "btech ai and ml"
    table = _format_course_table(hits, course_filter=course_kw)
    
    print(f"Query keyword: {course_kw}")
    print("Filtered Table Output:")
    print(table)
    
    # Check if unfiltered rows are present (they shouldn't be)
    if "Aeronautical" in table:
        print("\n❌ FAIL: Table contains unfiltered rows (e.g. Aeronautical)")
    else:
        print("\n✅ SUCCESS: Table appears correctly filtered.")

if __name__ == "__main__":
    test_filter()
