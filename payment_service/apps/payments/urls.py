from django.urls import path
from . import views

urlpatterns = [
    path('payments/', views.PaymentListCreateView.as_view()),
    path('payments/webhook/vnpay/', views.VNPayWebhookView.as_view()),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view()),
    path('payments/<int:pk>/receipt/', views.PaymentReceiptView.as_view()),
    path('payments/<int:pk>/refund/', views.PaymentRefundView.as_view()),
]
