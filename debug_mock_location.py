
import os
import sys
import re

# Mock the loader to bypass DB
class MockLoader:
    def get_all_colleges(self):
        # Manually load some colleges from disk for testing
        data_dir = 'backend/data'
        files = ['Ethiraj_output.json', 'Loyola_output.json', 'Women_Christian_output.json']
        colleges = []
        for f in files:
            path = os.path.join(data_dir, f)
            if os.path.exists(path):
                import json
                with open(path, 'r', encoding='utf-8') as j:
                    data = json.load(j)
                slug = f.replace('_output.json', '').lower()
                colleges.append({
                    'key': slug,
                    'name': data['college_details'].get('College Name', slug),
                    'details': data['college_details']
                })
        return colleges

# Inject mock
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import chatbot.engine.loader as loader
loader.get_all_colleges = lambda: MockLoader().get_all_colleges()

from chatbot.engine.responder import generate_response

query = "Colleges in Egmore"
response = generate_response(query)

print(f"Query: {query}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")
print(f"Verified: {response.get('verified')}")
print(f"Type: {response.get('type')}")
