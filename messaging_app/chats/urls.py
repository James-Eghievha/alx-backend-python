from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet,
    MessageViewSet,
    UserViewSet,
    CustomTokenObtainPairView,
    auth_test,
    logout_view,
    health_check
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'users', UserViewSet, basename='user')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth-test/', auth_test, name='auth-test'),
    path('logout/', logout_view, name='logout'),
    path('health/', health_check, name='health-check'),
]