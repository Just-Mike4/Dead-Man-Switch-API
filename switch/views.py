from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action,api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from .models import Switch, Action, ActionType,CheckIn
from .serializers import (
    SwitchCreateSerializer,
    SwitchResponseSerializer,
    ActionTypeSerializer
)
from django.db.models import Max
import requests
from rest_framework.views import APIView



class SwitchViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Switch.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return SwitchCreateSerializer
        return SwitchResponseSerializer

    def perform_create(self, serializer):
        # Create associated action first
        action_data = {
            'type': self.request.data.get('action_type'),
            'target': self.request.data.get('action_target')
        }
        action = Action.objects.create(**action_data)
        serializer.save(user=self.request.user, action=action)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        switch = self.get_object()
        switch.last_checkin = timezone.now()
        switch.save()
        CheckIn.objects.create(switch=switch)
        return Response(
            {"message": "Check-in successful. Next trigger reset."},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def webhook_test(request):
    """Test a webhook endpoint"""
    url = request.data.get('url')
    if not url:
        return Response({"error": "URL required"}, status=400)
    
    try:
        response = requests.post(
            url,
            json={'test': True, 'message': 'Webhook test successful'},
            timeout=5
        )
        return Response({
            'status': response.status_code,
            'response': response.text
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    

class ActionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        choices = [
            {'type': choice[0], 'description': choice[1]}
            for choice in ActionType.choices
        ]
        serializer = ActionTypeSerializer(choices, many=True)
        return Response(serializer.data)
    
class UserStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        switches = request.user.switches.all()
        last_checkin = switches.aggregate(
            last=Max('last_checkin')
        )['last']

        if last_checkin is not None:
            last_checkin = last_checkin.strftime("%Y-%m-%d %H:%M:%S")
        
        return Response({
            'active_switches': switches.filter(status='active').count(),
            'triggered_switches': switches.filter(status='triggered').count(),
            'last_checkin': last_checkin
        })
