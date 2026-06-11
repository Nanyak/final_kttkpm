from django.urls import path
from .views import ChatbotView, chatbot_stream

urlpatterns = [
    path('chatbot/',        ChatbotView.as_view(), name='chatbot'),
    path('chatbot/stream/', chatbot_stream,        name='chatbot-stream'),
]
