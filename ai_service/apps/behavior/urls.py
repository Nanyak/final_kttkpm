from django.urls import path
from .views import TrackBehaviorView

urlpatterns = [
    path('track/', TrackBehaviorView.as_view(), name='track-behavior'),
]
