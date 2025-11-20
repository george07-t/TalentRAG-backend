from django.urls import path
from .views import UploadView, AnalysisView, ChatView

urlpatterns = [
    path('upload/', UploadView.as_view()),
    path('session/<uuid:session_id>/analysis/', AnalysisView.as_view()),
    path('session/<uuid:session_id>/chat/', ChatView.as_view()),
]
