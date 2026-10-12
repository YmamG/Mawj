import calendar
from datetime import timedelta
from django.db.models import Q, Count
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from tasks.models import Task


def achievement_data(user, period="week"):
    today = timezone.localdate()
    if period not in ("week", "month", "year"):
        period = "week"
    if period == "week":
        start = today - timedelta(days=(today.weekday() + 1) % 7)
        end = start + timedelta(days=7)
    elif period == "month":
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
    else:
        start = today.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
    tasks = Task.objects.filter(user=user).filter(
        Q(date__gte=start, date__lt=end)
        | Q(date__isnull=True, created_at__date__gte=start, created_at__date__lt=end)
    )
    total = tasks.count()
    completed = tasks.filter(status="done").count()
    summaries = tasks.order_by().annotate(
        report_date=Coalesce("date", TruncDate("created_at")),
    ).values("report_date").annotate(
        total=Count("pk"), completed=Count("pk", filter=Q(status="done")),
    )
    if period == "year":
        buckets = {month: {"label": calendar.month_abbr[month], "total": 0, "completed": 0} for month in range(1, 13)}
        for row in summaries:
            bucket = buckets[row["report_date"].month]
            bucket["total"] += row["total"]
            bucket["completed"] += row["completed"]
    else:
        buckets = {}
        day = start
        while day < end:
            buckets[day] = {"label": day.strftime("%d %b"), "total": 0, "completed": 0}
            day += timedelta(days=1)
        for row in summaries:
            buckets[row["report_date"]].update(total=row["total"], completed=row["completed"])
    chart = list(buckets.values())
    largest = max((row["total"] for row in chart), default=0) or 1
    for row in chart:
        row["height"] = round(row["total"] * 160 / largest)
        row["completed_height"] = round(row["completed"] * 160 / largest)
        row["remaining_height"] = row["height"] - row["completed_height"]
        row["remaining"] = row["total"] - row["completed"]
    return {
        "period": period,
        "chart": chart,
        "start": start,
        "last_day": end - timedelta(days=1),
        "total": total,
        "completed": completed,
        "remaining": total - completed,
        "percentage": round(completed * 100 / total) if total else 0,
    }
