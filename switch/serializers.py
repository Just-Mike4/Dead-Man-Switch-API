from rest_framework import serializers
from .models import Switch, Action, CheckIn, ActionType

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ['type', 'target']

class SwitchCreateSerializer(serializers.ModelSerializer):
    action_type = serializers.ChoiceField(
        choices=ActionType.choices,
        write_only=True,
        source='action.type'
    )
    action_target = serializers.CharField(
        write_only=True,
        source='action.target'
    )

    class Meta:
        model = Switch
        fields = [
            'title', 
            'message', 
            'inactivity_duration_days',
            'action_type',
            'action_target'
        ]

class SwitchResponseSerializer(serializers.ModelSerializer):
    next_trigger_date = serializers.DateTimeField(read_only=True,format="%Y-%m-%d %H:%M:%S")
    status = serializers.CharField(read_only=True)
    action_type = serializers.CharField(source='action.type', read_only=True)
    last_checkin = serializers.DateTimeField(read_only=True,format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Switch
        fields = [
            'id',
            'title',
            'status',
            'last_checkin',
            'next_trigger_date',
            'action_type'
        ]

class CheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = []

class ActionTypeSerializer(serializers.Serializer):
    type = serializers.CharField()
    description = serializers.CharField()