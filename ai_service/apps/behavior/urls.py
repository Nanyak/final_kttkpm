from django.urls import path
from .views import TrackBehaviorView, TrackBehaviorBatchView, UserBehaviorHistoryView

urlpatterns = [
    path('track/',         TrackBehaviorView.as_view(),      name='track-behavior'),
    path('track/batch/',   TrackBehaviorBatchView.as_view(), name='track-behavior-batch'),
    path('track/history/', UserBehaviorHistoryView.as_view(), name='user-behavior-history'),
]
