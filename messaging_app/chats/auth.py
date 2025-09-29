from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def get_tokens_for_user(user):
    """Generate JWT tokens for a user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_user_from_token(token):
    """Get user instance from JWT token"""
    try:
        user_id = token.payload.get('user_id')
        user = User.objects.get(user_id=user_id)
        return user
    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return None

def invalidate_user_tokens(user):
    """Invalidate all refresh tokens for a user"""
    try:
        RefreshToken.for_user(user).blacklist()
        logger.info(f"Tokens invalidated for user {user.email}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating tokens: {str(e)}")
        return False