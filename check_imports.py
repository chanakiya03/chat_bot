
import os
import sys

# Diagnostic script to check for circular imports or initialization errors
sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("--- Diagnostic Start ---")
try:
    print("Testing loader import...")
    from chatbot.engine import loader
    print("Testing search import...")
    from chatbot.engine import search
    print("Testing utils import...")
    from chatbot.engine import utils
    print("Testing router import...")
    from chatbot.engine import router
    print("Testing handlers import...")
    from chatbot.engine import handlers
    print("Testing responder import...")
    from chatbot.engine import responder
    print("Testing generate_response call...")
    from chatbot.engine.responder import generate_response
    print("Import check passed.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
print("--- Diagnostic End ---")
