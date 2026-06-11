from django.urls import path, include

urlpatterns = [
    path('api/ai/', include('apps.recommendations.urls')),
    path('api/ai/', include('apps.behavior.urls')),
    # chatbot has moved to rag_service (/api/ai/chatbot/ routed there via nginx)
]
