from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.OrderListCreateView.as_view()),
    path('orders/admin/', views.AdminOrderListView.as_view()),
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
    path('orders/<int:pk>/cancel/', views.OrderCancelView.as_view()),
    path('orders/<int:pk>/status/', views.OrderStatusInternalView.as_view()),
]
