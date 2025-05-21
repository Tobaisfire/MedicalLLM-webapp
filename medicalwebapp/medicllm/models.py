from django.db import models

# Create your models here.

class ChatSession(models.Model):
    id = models.CharField(primary_key=True, max_length=32)  # Use chat_id from JS
    title = models.CharField(max_length=128, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.id

class Message(models.Model):
    chat = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=32)  # 'user', 'bot', 'user-info', etc.
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} ({self.timestamp}): {self.content[:30]}"
