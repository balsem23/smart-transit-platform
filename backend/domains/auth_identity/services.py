import logging
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from .models import User

logger = logging.getLogger(__name__)

class AuthService:
    """
    Logique Métier (Service Layer) pour l'Authentification.
    Zero Trust: Toute tentative est journalisée. La logique est isolée de views.py.
    """
    
    @staticmethod
    def register_user(phone_number: str, password: str, role: str = 'PASSENGER', first_name: str = '', last_name: str = '', email: str = '') -> User:
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValueError("Un utilisateur avec ce numéro de téléphone existe déjà.")
        if email and User.objects.filter(email=email).exists():
            raise ValueError("Un utilisateur avec cet email existe déjà.")
        
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        logger.info(f"SUCCESS: New user registered: {phone_number} as {role}")
        return user

    @staticmethod
    def authenticate_user(email: str, password: str, device_id: str, ip_address: str) -> dict:
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            logger.warning(f"SECURITY ALERT: Failed login attempt for {email} from IP {ip_address}")
            raise AuthenticationFailed("Identifiants incorrects ou compte suspendu.")
        
        if not user.check_password(password):
            logger.warning(f"SECURITY ALERT: Failed login attempt for {email} from IP {ip_address}")
            raise AuthenticationFailed("Identifiants incorrects ou compte suspendu.")
        
        if not user.is_active:
            logger.warning(f"SECURITY ALERT: Login attempt on suspended account {user.id}")
            raise AuthenticationFailed("Ce compte a été suspendu pour fraude.")
            
        # Génération des JWT
        refresh = RefreshToken.for_user(user)
        
        # Enregistrement du Device_ID dans le token (Device Fingerprinting)
        refresh['device_id'] = device_id
        
        logger.info(f"SUCCESS: User {user.id} logged in from device {device_id}")
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,
            'user_id': str(user.id),
            'email': user.email,
            'phone_number': user.phone_number,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

    @staticmethod
    def blacklist_token(refresh_token: str) -> None:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            raise ValueError("Token invalide ou déjà expiré.")
