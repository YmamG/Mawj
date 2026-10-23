from datetime import timedelta
from django.utils import timezone
from .models import Task


def create_next_occurrence(task):
    """Create at most one successor; skip missed dates rather than flooding the list."""
    if not task.repeat or not task.date:
        return None
    step = timedelta(days=1 if task.repeat == "daily" else 7)
    next_date = task.date + step
    while next_date <= timezone.localdate():
        next_date += step
    shift = next_date - task.date
    successor, _ = Task.objects.get_or_create(previous_occurrence=task, defaults={
        "user": task.user, "title": task.title, "description": task.description,
        "date": next_date, "start_time": task.start_time,
        "deadline": task.deadline + shift if task.deadline else None,
        "estimated_duration": task.estimated_duration, "priority": task.priority,
        "category": task.category, "custom_category": task.custom_category, "repeat": task.repeat,
        "reminder_at": task.reminder_at + shift if task.reminder_at else None,
    })
    return successor
