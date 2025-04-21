from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class ActionType(models.TextChoices):
    EMAIL = 'email', 'Email'
    WEBHOOK = 'webhook', 'Webhook'


class Action(models.Model):
    """An action that gets triggered when a switch activates"""
    type = models.CharField(max_length=20, choices=ActionType.choices)
    target = models.CharField(max_length=255, help_text="Email address or webhook URL")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} → {self.target}"


class Switch(models.Model):
    """Core dead man's switch"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='switches')
    title = models.CharField(max_length=100)
    message = models.TextField()
    inactivity_duration_days = models.PositiveIntegerField()
    last_checkin = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('triggered', 'Triggered')], default='active')

    action = models.OneToOneField(Action, on_delete=models.CASCADE, related_name='switch')

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    @property
    def next_trigger_date(self):
        return self.last_checkin + timedelta(days=self.inactivity_duration_days)

    def should_trigger(self):
        return timezone.now() >= self.next_trigger_date and self.status == 'active'


class CheckIn(models.Model):
    """Tracks user check-ins per switch"""
    switch = models.ForeignKey(Switch, on_delete=models.CASCADE, related_name='checkins')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CheckIn: {self.switch.title} @ {self.timestamp}"
