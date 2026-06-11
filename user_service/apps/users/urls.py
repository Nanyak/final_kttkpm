from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('auth/refresh/', views.RefreshTokenView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('users/me/', views.MeView.as_view()),
    path('users/me/change-password/', views.ChangePasswordView.as_view()),
    path('users/me/addresses/', views.MyAddressListView.as_view()),
    path('users/me/addresses/<int:pk>/', views.MyAddressDetailView.as_view()),
    path('users/', views.AdminUserListView.as_view()),
    path('users/<int:pk>/', views.AdminUserDetailView.as_view()),
]
