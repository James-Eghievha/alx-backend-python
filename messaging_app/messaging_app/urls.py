# messaging_app/messaging_app/urls.py
# COMPLETE UPDATED VERSION WITH JWT ENDPOINTS

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('chats.urls')),
    
    # JWT token refresh/verify endpoints
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # DRF browsable API authentication
    path('api-auth/', include('rest_framework.urls')),
    
    # Redirect root URL to API
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    
    # Handle the accounts/profile/ redirect after login
    path('accounts/profile/', RedirectView.as_view(url='/api/', permanent=False)),
]