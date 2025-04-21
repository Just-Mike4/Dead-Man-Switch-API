from rest_framework import viewsets,status
from .serializers import (RegisterationSerializer,LoginSerializer)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model


CustomUser = get_user_model()


class RegisterationViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterationSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('post')
    
    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result =serializer.save()
        return Response(
        result
        , status=status.HTTP_201_CREATED)
        
class LoginViewSet(viewsets.ModelViewSet):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('post')
    
    def create(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
