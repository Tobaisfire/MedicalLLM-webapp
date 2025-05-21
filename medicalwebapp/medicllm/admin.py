from django.contrib import admin
from .models import ChatSession, Message

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    search_fields = ('id',)
    ordering = ('-created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'role', 'content', 'timestamp')
    search_fields = ('chat__id', 'role', 'content')
    list_filter = ('role', 'chat')
    ordering = ('-timestamp',)
