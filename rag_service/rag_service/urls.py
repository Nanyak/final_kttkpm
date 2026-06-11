from django.urls import path, include

urlpatterns = [
    path('api/ai/',  include('apps.chatbot.urls')),   # /api/ai/chatbot/ (same URL as before)
    path('api/rag/', include('apps.scores.urls')),    # /api/rag/scores/ (for ai_service)
]
