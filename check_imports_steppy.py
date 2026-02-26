
import os
import sys

# Step-by-step diagnostic to find the hang
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def log(msg):
    print(f"[DIAG] {msg}")
    sys.stdout.flush()

log("Starting diagnostic...")

try:
    log("Importing loader...")
    import chatbot.engine.loader as loader
    log("Loader imported.")

    log("Importing utils...")
    import chatbot.engine.utils as utils
    log("Utils imported.")

    log("Importing router...")
    import chatbot.engine.router as router
    log("Router imported.")

    log("Importing handlers (Potential circularity point)...")
    import chatbot.engine.handlers as handlers
    log("Handlers imported.")

    log("Importing responder (Potential circularity point)...")
    import chatbot.engine.responder as responder
    log("Responder imported.")

    log("Success: All modules imported.")
except ImportError as e:
    log(f"ImportError: {e}")
except Exception as e:
    log(f"Other Error: {e}")
    import traceback
    traceback.print_exc()

log("Diagnostic finished.")
