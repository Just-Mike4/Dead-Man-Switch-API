from rest_framework import viewsets
from .serializers import SwitchSerializer, ActionSerializer, CheckInSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Switch, Action, CheckIn


