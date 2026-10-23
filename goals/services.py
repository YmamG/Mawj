from django.db.models import Count, F, Q
from django.utils import timezone
from .models import Goal


def owned_goals(user):
    return Goal.objects.filter(user=user).annotate(
        total_steps=Count("steps", distinct=True),
        done_steps=Count("steps", filter=Q(steps__task__status="done") | Q(steps__task__isnull=True, steps__is_done=True), distinct=True),
    )


def achieved_query():
    return Q(total_steps__gt=0, done_steps=F("total_steps")) | Q(total_steps=0, marked_complete=True)


def goal_data(goal):
    achieved = goal.done_steps == goal.total_steps if goal.total_steps else goal.marked_complete
    percent = round(100 * goal.done_steps / goal.total_steps) if goal.total_steps else (100 if achieved else 0)
    return {"object": goal, "id": goal.pk, "title": goal.title, "why": goal.why, "category": goal.category,
            "has_image": bool(goal.image),
            "target_date": goal.target_date, "total_steps": goal.total_steps, "done_steps": goal.done_steps,
            "progress": percent, "ring_offset": round(276.46 * (1 - percent / 100), 2),
            "state": "achieved" if achieved else "paused" if goal.paused else "active",
            "overdue": bool(goal.target_date and goal.target_date < timezone.localdate() and not achieved)}
