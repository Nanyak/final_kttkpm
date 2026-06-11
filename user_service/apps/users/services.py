import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone as djtz
from .models import User, Role


def hash_password(raw):
    return make_password(raw)


def verify_password(raw, hashed):
    return check_password(raw, hashed)


def generate_access_token(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role.name if user.role_id else None,
        'type': 'access',
        'exp': datetime.now(tz=timezone.utc) + timedelta(hours=settings.JWT_ACCESS_TOKEN_LIFETIME_HOURS),
        'iat': datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token(user):
    payload = {
        'user_id': user.id,
        'type': 'refresh',
        'exp': datetime.now(tz=timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS),
        'iat': datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError('Token expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def get_user_from_token(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    if payload.get('type') != 'access':
        return None
    try:
        return User.objects.select_related('role').get(id=payload['user_id'])
    except User.DoesNotExist:
        return None


def register_user(data):
    role, _ = Role.objects.get_or_create(name='customer', defaults={'description': 'Default customer role'})
    user = User.objects.create(
        username=data['username'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        phone_number=data.get('phone_number', ''),
        role=role,
        is_active=True,
    )
    return user


def login_user(username, password):
    try:
        user = User.objects.select_related('role').get(username=username)
    except User.DoesNotExist:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login = djtz.now()
    user.save(update_fields=['last_login'])
    return user
