from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from .models import User, UserAddress
from .serializers import (
    UserSerializer, UserAddressSerializer, RegisterSerializer,
    LoginSerializer, ChangePasswordSerializer,
)
from .services import (
    register_user, login_user, generate_access_token, generate_refresh_token,
    decode_token, get_user_from_token, hash_password, verify_password,
)


def ok(data, http=status.HTTP_200_OK):
    return Response({'status': 'success', 'data': data}, status=http)


def err(message, http=status.HTTP_400_BAD_REQUEST):
    return Response({'status': 'error', 'data': {'message': message}}, status=http)


def require_auth(request):
    user = get_user_from_token(request)
    if not user:
        return None, err('Unauthorized', status.HTTP_401_UNAUTHORIZED)
    return user, None


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        try:
            user = register_user(serializer.validated_data)
        except IntegrityError:
            return err('Username or email already exists', status.HTTP_409_CONFLICT)
        return ok(UserSerializer(user).data, status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        user = login_user(serializer.validated_data['username'], serializer.validated_data['password'])
        if not user:
            return err('Invalid credentials', status.HTTP_401_UNAUTHORIZED)
        return ok({
            'access': generate_access_token(user),
            'refresh': generate_refresh_token(user),
            'user': UserSerializer(user).data,
        })


class RefreshTokenView(APIView):
    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return err('Refresh token required')
        try:
            payload = decode_token(refresh)
        except ValueError as e:
            return err(str(e), status.HTTP_401_UNAUTHORIZED)
        if payload.get('type') != 'refresh':
            return err('Invalid token type', status.HTTP_401_UNAUTHORIZED)
        try:
            user = User.objects.select_related('role').get(id=payload['user_id'])
        except User.DoesNotExist:
            return err('User not found', status.HTTP_404_NOT_FOUND)
        return ok({'access': generate_access_token(user)})


class LogoutView(APIView):
    def post(self, request):
        # Stateless JWT: client discards tokens. (Could implement blacklist with cache.)
        return ok({'message': 'Logged out'})


class MeView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        return ok(UserSerializer(user).data)

    def patch(self, request):
        user, error = require_auth(request)
        if error:
            return error
        allowed = ['first_name', 'last_name', 'phone_number', 'email']
        for f in allowed:
            if f in request.data:
                setattr(user, f, request.data[f])
        try:
            user.save()
        except IntegrityError:
            return err('Email already in use', status.HTTP_409_CONFLICT)
        return ok(UserSerializer(user).data)


class ChangePasswordView(APIView):
    def post(self, request):
        user, error = require_auth(request)
        if error:
            return error
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        if not verify_password(serializer.validated_data['old_password'], user.password_hash):
            return err('Invalid current password', status.HTTP_401_UNAUTHORIZED)
        user.password_hash = hash_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password_hash'])
        return ok({'message': 'Password changed'})


class MyAddressListView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        addrs = user.addresses.all()
        return ok(UserAddressSerializer(addrs, many=True).data)

    def post(self, request):
        user, error = require_auth(request)
        if error:
            return error
        serializer = UserAddressSerializer(data=request.data)
        if not serializer.is_valid():
            return err(serializer.errors)
        if serializer.validated_data.get('is_default'):
            user.addresses.update(is_default=False)
        addr = serializer.save(user=user)
        return ok(UserAddressSerializer(addr).data, status.HTTP_201_CREATED)


class MyAddressDetailView(APIView):
    def get(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        addr = get_object_or_404(UserAddress, pk=pk, user=user)
        return ok(UserAddressSerializer(addr).data)

    def patch(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        addr = get_object_or_404(UserAddress, pk=pk, user=user)
        serializer = UserAddressSerializer(addr, data=request.data, partial=True)
        if not serializer.is_valid():
            return err(serializer.errors)
        if serializer.validated_data.get('is_default'):
            user.addresses.exclude(pk=pk).update(is_default=False)
        serializer.save()
        return ok(serializer.data)

    def delete(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        addr = get_object_or_404(UserAddress, pk=pk, user=user)
        addr.delete()
        return ok({'deleted': True}, status.HTTP_204_NO_CONTENT)


class AdminUserListView(APIView):
    def get(self, request):
        user, error = require_auth(request)
        if error:
            return error
        if user.role.name != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        users = User.objects.select_related('role').all()
        return ok(UserSerializer(users, many=True).data)


class AdminUserDetailView(APIView):
    def get(self, request, pk):
        user, error = require_auth(request)
        if error:
            return error
        if user.role.name != 'admin':
            return err('Forbidden', status.HTTP_403_FORBIDDEN)
        target = get_object_or_404(User, pk=pk)
        return ok(UserSerializer(target).data)
