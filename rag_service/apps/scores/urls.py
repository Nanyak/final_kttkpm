from django.urls import path
from .views import RAGScoresView

urlpatterns = [
    path('scores/', RAGScoresView.as_view(), name='rag-scores'),
]
