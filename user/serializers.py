from rest_framework import serializers
from .forms import UserForm
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model


User = get_user_model()

class RegisterationSerializer(serializers.Serializer):
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


    def validate(self, data):

        form = UserForm({
            "username": data.get("username"),
            "email": data.get("email"),
            "password": data.get("password"),
        })

        if not form.is_valid():
            
            error_messages = []
            for field, errors in form.errors.items():
                if field == 'email':
                    error_messages.append("Email is already in use.")
                elif field == 'password':
                    error_messages.append("Password is too weak. It must contain at least 8 characters, including a number.")
                else:    
                    error_messages.append(errors[0])
            combined_error_message = ' and '.join(error_messages)

            raise serializers.ValidationError({
                "error": combined_error_message
            })
        
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=f"{validated_data['firstname']}-{validated_data['lastname']}",
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=self.role
        )

        from rest_framework_simplejwt.tokens import AccessToken
        access = AccessToken.for_user(user)

        return {
            "message": "Registration successful.",
            "access": str(access)
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
            data['access'] = str(access)
            data['message'] ="Login successful."
            
            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, user)

        else:
            raise serializers.ValidationError({
                "error": "Invalid email/password"
            })

        return data