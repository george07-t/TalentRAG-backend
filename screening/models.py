import uuid
from django.db import models

class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume_text = models.TextField()
    jd_text = models.TextField()
    match_score = models.FloatField(null=True, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    insights = models.TextField(blank=True, default='')  # Changed to TextField for paragraph format
    created_at = models.DateTimeField(auto_now_add=True)

class ResumeChunk(models.Model):
    session = models.ForeignKey(Session, related_name='chunks', on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=20, default='resume')  # resume | job_description
    index = models.IntegerField()
    text = models.TextField()
    embedding = models.JSONField()  # list of floats

class ChatMessage(models.Model):
    session = models.ForeignKey(Session, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # user / assistant
    question = models.TextField(blank=True)
    answer = models.TextField(blank=True)
    retrieved_chunks = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
