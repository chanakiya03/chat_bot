
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.generator import process_question_file

def test_generation():
    # Create a small temp file
    temp_file = 'data/temp_test_questions.txt'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("What is the annual fee for B.Tech CSE at HITS?\n")
        f.write("Which colleges offer a BCA program?\n")
        f.write("Compare the B.Tech CSE fees of HITS and BIHER.\n")

    print("Running small-scale generation test...")
    results = process_question_file(temp_file)
    
    print(f"\nResults generated: {len(results)}")
    for item in results:
        print(f"\nQ: {item['instruction']}")
        print(f"A: {item['response'][:100]}...")

    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)

if __name__ == "__main__":
    test_generation()
