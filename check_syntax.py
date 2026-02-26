import ast, sys

files = [
    'backend/chatbot/engine/responder.py',
    'backend/chatbot/engine/handlers.py',
    'backend/chatbot/engine/router.py',
    'backend/chatbot/engine/firewall.py',
]

all_ok = True
for f in files:
    try:
        with open(f, encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src)
        print(f"OK: {f}")
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {f} at line {e.lineno}: {e.msg}")
        print(f"  >> {e.text}")
        all_ok = False

sys.exit(0 if all_ok else 1)
