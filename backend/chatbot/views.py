from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import (
    MessageSerializer, CollegeSummarySerializer, CollegeDetailSerializer, UserSerializer
)
from .engine.loader import get_all_colleges, get_college_by_key, reload_knowledge_base, get_knowledge_base
from .engine.responder import generate_response_advanced

User = get_user_model()

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CollegeListView(APIView):
    """GET /api/colleges/ — List all available colleges."""
    def get(self, request):
        colleges = get_all_colleges()
        summary = [{'key': c['key'], 'name': c['details'].get('College Name', c['name'])} for c in colleges]
        return Response({'count': len(summary), 'colleges': summary})


class CollegeDetailView(APIView):
    """GET /api/colleges/<key>/ — Full detail for one college."""
    def get(self, request, key):
        college = get_college_by_key(key)
        if college is None:
            return Response({'error': 'College not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CollegeDetailSerializer(college)
        return Response(serializer.data)


class ChatView(APIView):
    """
    POST /api/chat/ — HTTP fallback for chat (when WebSocket not available).
    Body: { "message": "...", "context": [...], "session_id": "..." }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']
        context = request.data.get('context', [])
        if not isinstance(context, list):
            context = []

        response = generate_response_advanced(user_message, context[-5:])
        return Response({
            'text': response['text'],
            'intent': response.get('intent', 'general'),
            'type': response.get('type', 'search_result'),
            'sources': response.get('sources', []),
        })



class ReloadView(APIView):
    """
    POST /api/reload/ — Hot-reload the knowledge base from disk.
    Call this after adding a new *_output.json file to the data/ folder.
    No server restart needed!
    """
    def post(self, request):
        kb = reload_knowledge_base()
        return Response({
            'status': 'reloaded',
            'colleges_loaded': len(kb['colleges']),
            'documents_indexed': len(kb['documents']),
            'colleges': [c['name'] for c in kb['colleges']],
        })


class HealthView(APIView):
    """GET /api/health/ — Simple health check."""
    def get(self, request):
        kb = get_knowledge_base()
        return Response({
            'status': 'ok',
            'colleges_loaded': len(kb['colleges']),
            'documents_indexed': len(kb['documents']),
            'colleges': [c['name'] for c in kb['colleges']],
        })


class SuggestionsView(APIView):
    """
    GET /api/suggestions/?n=40
    Returns a shuffled sample of real questions from the question.txt dataset.
    The frontend uses these to fill the Quick Access circular shuffle.
    """
    import os as _os
    import random as _random

    _questions_cache: list = []

    @classmethod
    def _load_questions(cls):
        if cls._questions_cache:
            return cls._questions_cache
        import os, random
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        q_file = os.path.join(data_dir, 'question.txt')
        questions = []
        try:
            with open(q_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip blank lines and category headers
                    if not line:
                        continue
                    if line.startswith('Category') or line.startswith('Targeting') or line.startswith('Note:'):
                        continue
                    if len(line) > 10 and line.endswith('?'):
                        questions.append(line)
        except Exception:
            pass
        random.shuffle(questions)
        cls._questions_cache = questions
        return questions

    def get(self, request):
        import random
        n = int(request.query_params.get('n', 40))
        questions = self._load_questions()
        sample = random.sample(questions, min(n, len(questions))) if questions else []
        return Response({'questions': sample, 'total': len(questions)})
