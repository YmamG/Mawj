import calendar
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from journal.models import JournalEntry
from tasks.models import Task


@login_required
def calendar_current_month(request):
    today = timezone.localdate()
    return redirect("calendar_month", year=today.year, month=today.month)


@login_required
def calendar_month(request, year, month):
    if year < 1 or year > 9999 or month < 1 or month > 12:
        raise Http404("That month does not exist.")

    entries = JournalEntry.objects.filter(
        user=request.user,
        created_at__year=year,
        created_at__month=month,
    )
    journal_dates = {
        timezone.localtime(entry.created_at).date()
        for entry in entries
    }

    tasks = Task.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month,
    )
    tasks_by_date = {}
    for task in tasks:
        if task.date not in tasks_by_date:
            tasks_by_date[task.date] = {"total": 0, "completed": 0}
        tasks_by_date[task.date]["total"] += 1
        if task.status == "done":
            tasks_by_date[task.date]["completed"] += 1

    weeks = []
    for week in calendar.Calendar().monthdayscalendar(year, month):
        week_days = []
        for day_number in week:
            if day_number == 0:
                week_days.append(None)
                continue

            current_date = date(year, month, day_number)
            task_counts = tasks_by_date.get(current_date, {"total": 0, "completed": 0})
            week_days.append({
                "day": day_number,
                "has_journal": current_date in journal_dates,
                "task_count": task_counts["total"],
                "completed_count": task_counts["completed"],
            })
        weeks.append(week_days)

    first_of_month = date(year, month, 1)
    last_of_month = date(year, month, calendar.monthrange(year, month)[1])
    previous_month = first_of_month - timedelta(days=1)
    next_month = last_of_month + timedelta(days=1)

    return render(request, "dashboard/calendar.html", {
        "month_name": calendar.month_name[month],
        "year": year,
        "month": month,
        "weeks": weeks,
        "previous_month": previous_month,
        "next_month": next_month,
    })


@login_required
def day_detail(request, year, month, day):
    try:
        selected_date = date(year, month, day)
    except ValueError as error:
        raise Http404("That date does not exist.") from error

    entries = JournalEntry.objects.filter(
        user=request.user,
        created_at__date=selected_date,
    )
    tasks = Task.objects.filter(user=request.user, date=selected_date)
    return render(request, "dashboard/day_detail.html", {
        "selected_date": selected_date,
        "entries": entries,
        "tasks": tasks,
    })

@login_required
def achievements(request):
    today = timezone.localdate()
    period = request.GET.get("period", "week")
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
    tasks = Task.objects.filter(user=request.user).filter(
        Q(date__gte=start, date__lt=end)
        | Q(date__isnull=True, created_at__date__gte=start, created_at__date__lt=end)
    )
    total = tasks.count()
    completed = tasks.filter(status="done").count()
    return render(request, "dashboard/achievements.html", {
        "period": period,
        "start": start,
        "last_day": end - timedelta(days=1),
        "total": total,
        "completed": completed,
        "remaining": total - completed,
        "percentage": round(completed * 100 / total) if total else 0,
    })
