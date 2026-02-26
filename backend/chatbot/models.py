from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Custom User model with phone and email as unique identifier."""
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name', 'phone']

    def __str__(self):
        return self.email


class ChatSession(models.Model):
    """Stores a unique chat session identifier."""
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id} ({self.created_at:%Y-%m-%d %H:%M})"


class ChatMessage(models.Model):
    """Stores individual chat messages for a session."""
    ROLE_CHOICES = [('user', 'User'), ('bot', 'Bot')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role.upper()}] {self.content[:60]}"


class CollegeDetail(models.Model):
    """Stores full verified college details in JSON format."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    data = models.JSONField()  # Full college JSON structure
    last_synced = models.DateTimeField(auto_now=True)
    file_hash = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.name


class KnowledgeBaseQA(models.Model):
    """Stores verified question-answer pairs from question.txt."""
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    related_college = models.ForeignKey(
        CollegeDetail, on_delete=models.SET_NULL, null=True, blank=True, related_name='qa_pairs'
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_verified = models.BooleanField(default=True)

    def __str__(self):
        return f"Q: {self.question[:50]}..."
