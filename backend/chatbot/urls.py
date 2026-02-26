from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('auth/signup/', views.SignupView.as_view(), name='signup'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('colleges/', views.CollegeListView.as_view(), name='college-list'),
    path('colleges/<str:key>/', views.CollegeDetailView.as_view(), name='college-detail'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('health/', views.HealthView.as_view(), name='health'),
    path('reload/', views.ReloadView.as_view(), name='reload'),
    path('suggestions/', views.SuggestionsView.as_view(), name='suggestions'),
]
