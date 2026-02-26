import ast
import json
import sys

files = [
    ('chatbot/engine/utils.py', 'python'),
    ('chatbot/engine/responder.py', 'python'),
    ('chatbot/engine/handlers.py', 'python'),
]

all_ok = True
for path, ftype in files:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"  OK  {path}")
    except SyntaxError as e:
        print(f" FAIL {path}: {e}")
        all_ok = False

# JSON validation
json_file = 'data/Madras_output.json'
try:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    bca_found = any('bca' in c.get('course','').lower() for c in data.get('courses',[]))
    print(f"  OK  {json_file} (BCA entry: {'FOUND' if bca_found else 'MISSING'})")
except Exception as e:
    print(f" FAIL {json_file}: {e}")
    all_ok = False

if all_ok:
    print("\nAll files valid!")
else:
    print("\nSome files have errors!")
    sys.exit(1)
