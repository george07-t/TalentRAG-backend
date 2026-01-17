from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .parsing import read_file_content, normalize_whitespace, split_sections, extract_skills, chunk_text
from .matching import compute_match
from .rag import store_chunks, answer_question
from .models import Session
from .serializers import SessionSerializer, ChatRequestSerializer, ChatMessageSerializer

class UploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        resume_file = request.FILES.get('resume')
        jd_file = request.FILES.get('job_description')
        if not resume_file or not jd_file:
            return Response({'error': 'Both resume and job description files are required.'}, status=400)
        resume_text = normalize_whitespace(read_file_content(resume_file))
        jd_text = normalize_whitespace(read_file_content(jd_file))

        sections = split_sections(resume_text)
        resume_chunks = chunk_text(sections)
        jd_chunks = chunk_text(split_sections(jd_text))
        skills = extract_skills(resume_text)
        match_data = compute_match(skills, jd_text, resume_text)

        session = Session.objects.create(
            resume_text=resume_text,
            jd_text=jd_text,
            match_score=match_data['match_score'],
            strengths=match_data['strengths'],
            gaps=match_data['gaps'],
            insights=match_data['insights']
        )
        store_chunks(session, resume_chunks, doc_type='resume')
        store_chunks(session, jd_chunks, doc_type='job_description')
        return Response({'session': str(session.id), 'analysis': SessionSerializer(session).data})

class AnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        return Response(SessionSerializer(session).data)

class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        question = serializer.validated_data['question']
        result = answer_question(session, question)
        return Response(result)

    def get(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        messages = session.messages.order_by('created_at')
        return Response(ChatMessageSerializer(messages, many=True).data)
