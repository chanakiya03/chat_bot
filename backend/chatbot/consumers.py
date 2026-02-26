"""
WebSocket Consumer for real-time chat.
Each browser connection gets its own consumer instance with
its own in-memory context/session history (last 5 messages).
"""
import json
import uuid
import logging
import os
import datetime
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chatbot.engine.responder import generate_response_advanced

logger = logging.getLogger(__name__)

def log_user_question(session_id, question):
    """Helper to save user questions into a JSON file for training/analysis."""
    log_file = os.path.join(settings.COLLEGE_DATA_DIR, 'user_questions.json')
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": session_id,
        "question": question
    }
    
    try:
        data = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        
        data.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error logging user question: {e}")

class ChatConsumer(AsyncWebsocketConsumer):
    """Handles a single WebSocket chat connection."""

    async def connect(self):
        self.session_id = str(uuid.uuid4())
        self.context_history = []  # List of {role, content}
        await self.accept()
        logger.info(f"WebSocket connected: {self.session_id}")

        # Send welcome ping
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'session_id': self.session_id,
            'message': 'Connected to CollegeBot server.',
        }))

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: {self.session_id} (code={close_code})")

    async def receive(self, text_data):
        """Handle incoming message from frontend."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON received.',
            }))
            return

        user_message = data.get('message', '').strip()
        if not user_message:
            return

        # Add to context
        self.context_history.append({'role': 'user', 'content': user_message})

        # Save to user_questions.json
        await database_sync_to_async(log_user_question)(self.session_id, user_message)

        # Send typing indicator
        await self.send(text_data=json.dumps({'type': 'typing'}))

        try:
            # Generate response (runs in thread pool to avoid blocking event loop)
            response = await database_sync_to_async(
                generate_response_advanced,
                thread_sensitive=False
            )(user_message, self.context_history[-5:])  # last 5 messages as context
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error in consumer: {e}")
            response = {
                'text': "⚠️ My apologies, something went wrong on my end. Please try again.",
                'intent': 'error',
                'type': 'error'
            }

        # Add bot response to context
        # 🚨 FIX: Safety fallback for missing 'text' key
        bot_text = response.get('text') or response.get('message') or "⚠️ No response generated."
        self.context_history.append({'role': 'bot', 'content': bot_text})

        # Keep context window to 10 messages max
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]

        # Send response to client
        await self.send(text_data=json.dumps({
            'type': 'message',
            'text': bot_text,
            'intent': response.get('intent', 'general'),
            'response_type': response.get('type', 'search_result'),
            'sources': response.get('sources', []),
            'suggestions': response.get('suggestions', []),
            'session_id': self.session_id,
        }))
