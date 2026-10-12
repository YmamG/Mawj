from django.utils import timezone
from .models import Task


def reminders(request):
    if not request.user.is_authenticated:
        return {}
    return {"due_reminder_count": Task.objects.filter(
        user=request.user, status="todo", reminder_at__lte=timezone.now(),
        reminder_dismissed=False,
    ).count()}
