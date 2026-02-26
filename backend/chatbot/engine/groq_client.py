"""
Groq API Client
Wraps the Groq SDK for LLM completions.
Updated to support reasoning models and streaming.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_groq_client = None

def _get_client():
    """Lazy-init the Groq client."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    try:
        from groq import Groq
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key:
            logger.warning("GROQ_API_KEY not set.")
            return None
        # timeout=10 ensures slow network won't block user response
        _groq_client = Groq(api_key=api_key, timeout=10.0)
        return _groq_client
    except (ImportError, Exception) as e:
        logger.error(f"Groq Init Error: {e}")
        return None

def ask_groq(system_prompt: str, user_message: str, context_docs: list[str], history: list[dict] = None) -> str | None:
    client = _get_client()
    if client is None: return None

    model = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
    
    context_block = "\n\n".join(f"[Source {i+1}]: {doc}" for i, doc in enumerate(context_docs[:5]))
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history:
            messages.append({"role": "assistant" if msg.get("role") == "assistant" else "user", "content": msg.get("content", "")})
    
    messages.append({
        "role": "user",
        "content": f"Context:\n{context_block}\n\nQuestion: {user_message}"
    })

    import time
    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=768,
                top_p=1,
                stream=True,
            )
            
            full_response = ""
            for chunk in completion:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_response += delta.content
            
            # Strip any reasoning/thinking traces
            import re
            full_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
            
            return full_response or None
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Groq API Rate Limit (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            logger.error(f"Groq API error on attempt {attempt+1}: {e}")
            if attempt == 2: return None
    return None

def ask_groq_json(system_prompt: str, user_message: str) -> str | None:
    """Uses Groq's JSON mode to return a structured response."""
    client = _get_client()
    if client is None: return None

    # Use configured model from settings
    model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')

    messages = [
        {"role": "system", "content": system_prompt + "\nIMPORTANT: Return ONLY valid JSON."},
        {"role": "user", "content": user_message}
    ]

    import time
    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistency
                max_completion_tokens=512,
            )
            return completion.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Groq JSON API Rate Limit (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            logger.error(f"Groq JSON API error on attempt {attempt+1}: {e}")
            if attempt == 2: 
                # CRITICAL: Return a valid JSON string so json.loads() doesn't fail
                return '{"intent": "general", "raw_colleges": [], "raw_courses": [], "is_comparison": false}'
    return '{"intent": "general", "raw_colleges": [], "raw_courses": [], "is_comparison": false}'
