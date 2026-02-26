"""
Training Data Generator Utility
Converts the college knowledge base into a structured instruction-tuning dataset.
"""
import os
import sys
import json
import logging

# Add the parent directory (backend) to sys.path to resolve 'chatbot' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Moving imports inside to avoid premature Django initialization
def process_question_file(file_path):
    """Parse questions from a file and generate responses using the chatbot engine."""
    from chatbot.engine.responder import generate_response_advanced
    
    if not os.path.exists(file_path):
        print(f"⚠️ Question file not found: {file_path}")
        return []

    print(f"Reading questions from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    questions = []
    seen_questions = set()
    for line in lines:
        line = line.strip()
        # Skip headers, empty lines, and category labels
        if not line or line.startswith(('Category', 'Targeting', '🎓', '💼', '📊', '🎯', '#', '###')):
            continue
        
        # Normalize and filter
        q_norm = line.lower()
        if q_norm in seen_questions:
            continue
            
        # If it ends with ? or looks like a valid question
        if '?' in line or len(line.split()) > 3:
            questions.append(line)
            seen_questions.add(q_norm)

    print(f"Generating answers for {len(questions)} unique questions...")
    qa_pairs = []
    for i, q in enumerate(questions):
        try:
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"  - Answered {i + 1}/{len(questions)} questions")
            
            resp = generate_response_advanced(q)
            qa_pairs.append({
                "instruction": q,
                "response": resp.get('text', '')
            })
        except Exception as e:
            print(f"  ❌ Error answering '{q[:30]}...': {e}")
            
    return qa_pairs

def generate_training_dataset():
    """Iterate through all colleges and generate training pairs."""
    from chatbot.engine.loader import get_all_colleges
    from django.conf import settings
    
    try:
        colleges = get_all_colleges()
        training_data = []

        print(f"1. Generating Template-based data for {len(colleges)} colleges...")
        for college in colleges:
            details = college.get('details', {})
            courses = college.get('courses', [])
            name = college.get('name', 'This college')
            
            # --- Profile & About ---
            about = details.get('About', '')
            ctype = details.get('Type', 'institution')
            location = details.get('Location', 'Chennai')
            if about:
                training_data.append({"instruction": f"Tell me about {name}.", "response": f"{name} is a {ctype}. {about}"})
                training_data.append({"instruction": f"Give me info on {name}.", "response": f"{name} is located in {location}. {about}"})

            # --- Location ---
            if location:
                training_data.append({"instruction": f"Where is {name} located?", "response": f"{name} is located in {location}."})
                training_data.append({"instruction": f"What is the address of {name}?", "response": f"The location for {name} is {location}."})

            # --- Placement ---
            placement = details.get('PLACEMENT DATA', '')
            avg_pkg = details.get('Average Package', 'N/A')
            if placement:
                training_data.append({"instruction": f"What are the placement details for {name}?", "response": f"Placement at {name}: {placement}."})
                training_data.append({"instruction": f"How is the placement at {name}?", "response": f"{name} has a placement record of {placement}. Average package is {avg_pkg}."})
                training_data.append({"instruction": f"What is the average package at {name}?", "response": f"The average package at {name} is {avg_pkg}."})

            # --- Hostel ---
            hostel = details.get('Hostel Available', 'N/A')
            if hostel:
                training_data.append({"instruction": f"Does {name} have a hostel?", "response": f"Yes, hostel is available at {name}: {hostel}"})
                training_data.append({"instruction": f"Is there any accommodation at {name}?", "response": f"{name} provides hostel facilities: {hostel}"})

            # --- Accreditation ---
            acc = details.get('Accreditation', '')
            if acc:
                training_data.append({"instruction": f"What is the accreditation of {name}?", "response": f"{name} is {acc}."})

            # --- Admission / Eligibility ---
            adm = details.get('Admission Mode', '')
            if adm:
                training_data.append({"instruction": f"How to get admission in {name}?", "response": f"Admission at {name}: {adm}"})
                training_data.append({"instruction": f"What is the eligibility for {name}?", "response": f"The eligibility/admission process for {name} is: {adm}"})

            # --- Courses & Fees ---
            for course in courses:
                c_name = course.get('course', 'the course')
                spec = course.get('specialization', 'General')
                dur = course.get('duration_years', '3')
                fees = course.get('annual_fees_inr', 'N/A')
                fees_fmt = f"₹{fees:,.0f}" if isinstance(fees, (int, float)) else str(fees)
                
                # Multiple fee phrasings
                training_data.append({"instruction": f"What are the annual fees for {c_name} at {name}?", "response": f"The annual fee for {c_name} ({spec}) at {name} is {fees_fmt}."})
                training_data.append({"instruction": f"How much does {c_name} cost at {name}?", "response": f"At {name}, the {c_name} ({spec}) costs {fees_fmt} per year."})
                training_data.append({"instruction": f"Duration of {c_name} in {name}?", "response": f"The {c_name} program at {name} is {dur} years long."})

        print(f"2. Generating Question-based data from question.txt...")
        q_file = os.path.join(settings.BASE_DIR, 'data', 'question.txt')
        question_data = process_question_file(q_file)
        training_data.extend(question_data)

        # Save to file
        output_path = os.path.join(settings.BASE_DIR, 'data', 'training_data.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"Saving {len(training_data)} total samples to {output_path}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=4)
        
        print(f"✅ Successfully generated training data.")
        return training_data
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
    django.setup()
    generate_training_dataset()
