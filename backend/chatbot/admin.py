from django.contrib import admin
from .models import ChatSession, ChatMessage, CollegeDetail, KnowledgeBaseQA

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'created_at', 'updated_at')
    search_fields = ('session_id',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content_excerpt', 'created_at')
    list_filter = ('role', 'session')
    
    def content_excerpt(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

@admin.register(CollegeDetail)
class CollegeDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'last_synced')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(KnowledgeBaseQA)
class KnowledgeBaseQAAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'category', 'related_college', 'is_verified')
    list_filter = ('category', 'is_verified', 'related_college')
    search_fields = ('question', 'answer')

    def question_short(self, obj):
        return obj.question[:60] + '...' if len(obj.question) > 60 else obj.question
    question_short.short_description = 'Question'
