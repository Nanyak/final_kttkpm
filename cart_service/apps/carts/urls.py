from django.urls import path
from . import views

urlpatterns = [
    path('carts/me/', views.MyCartView.as_view()),
    path('carts/me/items/', views.MyCartItemListView.as_view()),
    path('carts/me/items/<int:pk>/', views.MyCartItemDetailView.as_view()),
    path('carts/<int:pk>/', views.CartDetailInternalView.as_view()),
]
