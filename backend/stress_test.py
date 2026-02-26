import os
import sys
import json
import logging
import random
import re

# Resolve paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
import django
django.setup()

from chatbot.engine.loader import get_all_colleges
from chatbot.engine.responder import generate_response

def run_stress_test():
    """Generates 1000+ natural language questions and tests the engine."""
    colleges = get_all_colleges()
    questions = []
    
    print(f"--- Stress Test Initiation (1000+ Questions) ---")
    print(f"Colleges in Database: {len(colleges)}")
    
    # 1. Load basic questions from file if exists
    q_file = os.path.join('data', 'question.txt')
    if os.path.exists(q_file):
        with open(q_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('Category', 'Targeting', '🎓', '💼', '📊', '🎯')):
                    if '?' in line or len(line.split()) > 3:
                        questions.append(line)
        print(f"Loaded {len(questions)} baseline questions from question.txt")

    # 2. Programmatically generate variations to reach 1000+
    templates = [
        "What is the fees for {course} at {college}?",
        "Can you tell me about {college}?",
        "Does {college} have a hostel?",
        "Where is {college} located?",
        "Placement details for {college}",
        "How is the placement at {college}?",
        "Tell me about {course} in {college}",
        "Is {college} autonomous?",
        "What are the popular courses in {college}?",
        "Eligibility criteria for {college}?",
        "Admission mode of {college}?",
        "Average package at {college}?",
        "Does {college} have {facility} facilities?",
    ]
    
    facilities = ['medical', 'library', 'sports', 'gym', 'wifi', 'lab']
    
    print("Generating 1000+ variations...")
    while len(questions) < 11000:
        c = random.choice(colleges)
        college_name = c['name']
        
        # Pick a course if available
        if c.get('courses'):
            course = random.choice(c['courses'])
            course_name = f"{course.get('course', 'the course')} {course.get('specialization', '')}".strip()
        else:
            course_name = "MBA"
            
        tpl = random.choice(templates)
        q = tpl.format(
            college=college_name,
            course=course_name,
            facility=random.choice(facilities)
        )
        questions.append(q)

    # 3. Batch Test the Engine
    results = []
    verified_count = 0
    total = len(questions)
    
    print(f"Running Engine Validation on {total} questions...")
    for i, q in enumerate(questions):
        try:
            resp = generate_response(q)
            is_verified = resp.get('verified', False)
            if is_verified: verified_count += 1
            
            results.append({
                "question": q,
                "verified": is_verified,
                "response_type": resp.get('type', 'unknown')
            })
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{total}...")
        except Exception as e:
            print(f"  Error on '{q[:50]}': {e}")

    # 4. Report
    report = {
        "summary": {
            "total_questions": total,
            "verified_responses": verified_count,
            "failed_responses": total - verified_count,
            "accuracy_rate": f"{(verified_count/total)*100:.2f}%"
        },
        "details": results[:50] # Show first 50 as sample
    }
    
    output_path = os.path.join('data', 'stress_test_report.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    print(f"\n✅ Stress Test Completed!")
    print(f"📊 Total Questions: {total}")
    print(f"🔒 Verified (Database-Matched): {verified_count}")
    print(f"📈 Accuracy: {(verified_count/total)*100:.2f}%")
    print(f"📄 Report saved to {output_path}")

if __name__ == "__main__":
    run_stress_test()
