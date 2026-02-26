import os
import sys
import json
import logging
import random
import re

# Redirect everything to a file since terminal output is problematic
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mini_test_debug.log")

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    print(msg) # Still print just in case

log("--- SCRIPT STARTING ---")

# Resolve paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')

try:
    import django
    log("Setting up Django...")
    django.setup()
    log("Django setup complete.")
except Exception as e:
    log(f"Django setup FAILED: {e}")
    sys.exit(1)

from chatbot.engine.loader import get_all_colleges
from chatbot.engine.responder import generate_response

def run_mini_test():
    """Trial run with 10 questions."""
    try:
        colleges = get_all_colleges()
        log(f"Loaded {len(colleges)} colleges.")
        
        questions = [
           "What is the fees for MBA at HITS?",
"Can you tell me about Loyola?",
"Does MCC have a hostel?",
"List all colleges in Tambaram.",
"Which college is better for MBA, HITS or Loyola?",
"Top 5 colleges for B.Sc CS",
"Cheapest engineering college",
"Average package for MCA at BIHER",
"Is there a medical center at HITS?",
"Show me all colleges in Velachery.",
"Hey, my budget is around 50k a year. Are there any decent B.Com courses I can get into?",
"How much is the management quota for CSE at SSN?",
"Is the Aided stream at Guru Nanak cheaper? What is the fee for B.Sc Math there?",
"Which is cheaper for MCA, Loyola or Ethiraj?",
"What is the total cost for the 5-year Integrated M.Tech at SSN?",
"What is the fee structure for B.Pharm at BIHER?",
"How much does B.Sc Visual Communication cost at WCC compared to MCC?",
"Does Sri Balaji have any courses under 40,000 rupees?",
"What is the fee for B.Tech AI & ML at HITS?",
"What is the difference in fees between Shift 1 and Shift 2 B.Com at Loyola?",
"Is SSN strictly an engineering college or do they offer arts courses too?",
"Which is better for women, Ethiraj or WCC?",
"What is BIHER known for?",
"Give me a quick summary of Madras Christian College.",
"Are there any deemed universities in this list?",
"Which college has NAAC A++ accreditation?",
"Is PERI College fully self-financed?",
"Which colleges are affiliated with Madras University?",
"What does HITS stand for?",
"Is Guru Nanak College co-educational?",
"What are the nearest arts and science colleges in Tambaram?",
"Is WCC near Nungambakkam?",
"Which engineering colleges are located on OMR?",
"Where exactly is SSN located?",
"Are there good colleges near Velachery?",
"List colleges in Egmore.",
"Show colleges in Chennai 600059.",
"Is HITS located in Padur or Kelambakkam?",
"Is BIHER a good option if I live in Selaiyur?",
"Are Loyola and WCC in the same area?",
"Which is better for B.A Economics, Loyola or MCC?",
"Compare B.Tech placements at HITS and SSN.",
"Which is older, Ethiraj or WCC?",
"Which is better for BBA, PERI or Guru Nanak College?",
"What is the fee difference between SSN Government quota and Management quota?",
"Which has better campus life, MCC or HITS?",
"Is MBA at BIHER cheaper than Ethiraj?",
"Which has more student clubs, SSN or Loyola?",
"Compare NAAC accreditation of autonomous colleges.",
"Is it harder to get into SSN or HITS for CSE?",
"What is the average package at SSN for IT jobs?",
"Do Amazon or Microsoft recruit from these colleges?",
"What is the highest salary package at HITS?",
"Is Ethiraj's placement rate above 85%?",
"Which engineering college has 90%+ placements?",
"Do Zoho and Cognizant recruit from BIHER?",
"What jobs do students get after studying at WCC?",
"Is the MBA average package at Guru Nanak better than B.Com?",
"Does Sri Balaji College have good placements?",
"Which college has the best placements for B.Tech CSE?",
"Does MCC have good hostel facilities?",
"Are there separate hostels for girls at SSN?",
"Does HITS have an active coding or AI club?",
"Which college has the best cultural festivals?",
"Is there NCC or NSS at Guru Nanak College?",
"Does Loyola provide hostel facilities?",
"Which college has an Entrepreneurship Cell?",
"Does WCC have a strong alumni network?",
"Does BIHER have smart classrooms and good Wi-Fi?",
"Which college is known for being strict?",
"How do I get admission into SSN?",
"Does Ethiraj have an entrance exam?",
"Is lateral entry available at SSN?",
"How do PG admissions work at MCC?",
"Can I get direct admission into PERI College?",
"What is the admission mode for B.Arch at HITS?",
"Does BIHER have a management quota?",
"Do I need to write JEE to get into HITS?",
"Is admission at Guru Nanak based on Tamil Nadu government rules?",
"Is it harder to get into Loyola Shift 1 than Shift 2?"

        ]
        
        results = []
        log(f"Running mini test on {len(questions)} questions...")
        for i, q in enumerate(questions):
            log(f"  [{i+1}/10] Testing: {q}")
            resp = generate_response(q)
            res = {
                "question": q,
                "verified": resp.get('verified', False),
                "type": resp.get('type', 'unknown'),
                "text": resp.get('text', '')[:100] + "..."
            }
            results.append(res)
            log(f"    Result: {res['type']} (Verified: {res['verified']})")
        
        log("\n✅ Mini Test Completed!")
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mini_test_results.json"), "w") as f:
            json.dump(results, f, indent=2)
        log("Results saved to mini_test_results.json")
    except Exception as e:
        log(f"Test execution FAILED: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    run_mini_test()
