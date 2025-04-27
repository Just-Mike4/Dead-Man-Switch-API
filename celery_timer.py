from django_celery_beat.models import PeriodicTask, IntervalSchedule

# Create schedule every hour
schedule, _ = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.HOURS,
)

# Create the periodic task
PeriodicTask.objects.get_or_create(
    interval=schedule,
    name='Hourly Switch Check',
    task='switch.tasks.check_switches',
)