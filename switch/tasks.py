from celery import shared_task
from django.utils import timezone
from .models import Switch
import requests
from django.core.mail import send_mail
from datetime import timedelta
import logging
from django.db.models import F

# Correct logger initialization
logger = logging.getLogger(__name__)

@shared_task
def check_switches():
    """Check and trigger switches that have expired"""
    now = timezone.now()
    expired_switches = Switch.objects.filter(
        status='active',
        last_checkin__lt=now - timedelta(days=F('inactivity_duration_days'))
    )
    
    for switch in expired_switches.select_related('action'):
        try:
            trigger_switch(switch)
            switch.status = 'triggered'
            switch.save(update_fields=['status'])
        except Exception as e:
            logger.error(f"Failed to trigger switch {switch.id}: {str(e)}")

def trigger_switch(switch):
    """Execute the associated action for a switch"""
    action = switch.action
    
    try:
        if action.type == 'email':
            send_email_action(action, switch.message)
        elif action.type == 'webhook':
            trigger_webhook(action, switch.message)
    except Exception as e:
        # Handle errors (log them, retry, etc.)
        print(f"Failed to trigger action for switch {switch.id}: {str(e)}")

def send_email_action(action, message):
    send_mail(
        subject='Dead Man Switch Triggered',
        message=message,
        from_email='noreply@yourdomain.com',
        recipient_list=[action.target],
        fail_silently=False,
    )

def trigger_webhook(action, message):
    requests.post(
        url=action.target,
        json={
            'event': 'deadman_switch_triggered',
            'message': message,
            'timestamp': timezone.now().isoformat()
        },
        timeout=10
    )