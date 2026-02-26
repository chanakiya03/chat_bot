import os
import sys
import django

sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.router import spell_check_query, pre_process_query

def test_spell_correction():
    print("\n--- SymSpell Correction Tests ---")
    cases = [
        ("mcc ug cources", "mcc ug courses"),
        ("peri ug cources", "peri ug courses"),
        ("What are coures at ssn?", None),           # "coures" -> "courses"
        ("btech fees at hits", "btech fees at hits"), # acronym preserved
        ("SSN colege", "SSN college"),               # 'colege' corrected
        ("courses under 50k", "courses under 50k"),  # numbers preserved
    ]
    all_pass = True
    for query, expected in cases:
        result = spell_check_query(query)
        final = pre_process_query(result)
        status = "✅" if (expected is None or expected.lower() in final.lower()) else "❌"
        if status == "❌":
            all_pass = False
        print(f"{status} Input:  '{query}'")
        print(f"   Spell: '{result}'")
        print(f"   Final: '{final}'")
        print()

    if all_pass:
        print("✨ All SymSpell tests passed!")
    else:
        print("⚠️ Some tests failed — review above.")

if __name__ == "__main__":
    try:
        test_spell_correction()
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
