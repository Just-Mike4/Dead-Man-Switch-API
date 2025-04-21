from .models import Switch, Action, CheckIn
from rest_framework import serializers

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ['id', 'type', 'target', 'description']
        read_only_fields = ['id']

class SwitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Switch
        fields = ['id', 'user', 'title', 'message', 'inactivity_duration_days', 'last_checkin', 'created_at', 'status', 'action']
        read_only_fields = ['id', 'user', 'last_checkin', 'created_at', 'status']

class CheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = ['id', 'switch', 'timestamp']
        read_only_fields = ['id', 'switch', 'timestamp']