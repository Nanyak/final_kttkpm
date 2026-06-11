from django.urls import path
from . import views

urlpatterns = [
    path('shipping/', views.ShipmentListCreateView.as_view()),
    path('shipping/admin/', views.AdminShipmentListView.as_view()),
    path('shipping/calculate-fee/', views.CalculateFeeView.as_view()),
    path('shipping/track/<str:tracking_number>/', views.ShipmentTrackPublicView.as_view()),
    path('shipping/<int:pk>/', views.ShipmentDetailView.as_view()),
    path('shipping/<int:pk>/status/', views.ShipmentStatusUpdateView.as_view()),
]
