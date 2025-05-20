from rest_framework import serializers
from .forms import UserForm
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class RegisterationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        form = UserForm({
            "username": data.get("username"),
            "email": data.get("email"),
            "password1": data.get("password"),
        })
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)


        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password1'],
        )

        # Generate JWT access token
        access = AccessToken.for_user(user)

        return {
            "username": validated_data['username'],
            "email": validated_data['email'],
            "token": str(access)
        }


class LoginSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        data = {}
        email = attrs.get('email')
        password = attrs.get('password')

        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            access = self.get_token(user).access_token
            data['token'] = str(access)
            
            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, user)

        else:
            raise serializers.ValidationError({
                "error": "Invalid email/password"
            })

        return data

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def save(self):
        request = self.context.get('request')
        user = User.objects.get(email=self.validated_data['email'])
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = str(AccessToken.for_user(user))
        reset_link = request.build_absolute_uri(
            reverse('password-reset-confirm', kwargs={'uid': uid, 'token': token})
        )

        send_mail(
            'Password Reset Request',
            f"""
            Dear {user.username},
        
            We received a request to reset your password for your account associated with this email address. If you did not request this, please ignore this email. No changes have been made to your account.
        
            To reset your password, please click the link below or copy and paste it into your browser:
        
            http://127.0.0.1:8000/password_reset/{uid}/{token}
        
            This link will expire in 1 hour.
        
            If you have any questions, feel free to contact our support team.
        
            Best regards,
            The Dead Man Switch Team
            """,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs): 
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid token or user ID")
        
        token = attrs['token']
        try:
            AccessToken(token)
        except Exception:
            raise serializers.ValidationError("Invalid token")
        
        return attrs

    def save(self):
        uid = force_str(urlsafe_base64_decode(self.validated_data['uid']))
        user = User.objects.get(pk=uid)
        user.set_password(self.validated_data['new_password'])
        user.save()