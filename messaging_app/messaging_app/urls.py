from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chats.urls')),
    
    # DRF Authentication URLs
    path('api-auth/', include('rest_framework.urls')),
    
    # Redirect root URL to API
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    
    # Handle accounts/profile/ redirect
    path('accounts/profile/', RedirectView.as_view(url='/api/', permanent=False)),
]