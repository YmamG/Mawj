from getpass import getpass
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from journal.models import JournalEntry, TaskSuggestion
from tasks.models import Task


class Command(BaseCommand):
    help = "Create fictional sample data once; existing accounts are never modified."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="mawj_demo")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        if get_user_model().objects.filter(username=username).exists():
            self.stdout.write("Account already exists; no data or password changed.")
            return
        password = os.environ.get("MAWJ_DEMO_PASSWORD")
        if not password:
            if not self.stdin_is_terminal():
                raise CommandError("Set MAWJ_DEMO_PASSWORD or run interactively to enter a password.")
            password = getpass("Demo account password (not saved in source): ")
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        user = get_user_model()(username=username)
        try:
            validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        user.set_password(password)
        user.save()
        today = timezone.localdate()
        for index in range(12):
            done = index < 6
            Task.objects.create(
                user=user, title=f"Demo: Study session {index + 1}",
                description="Fictional sample task for the Mawj demonstration.",
                date=today, priority=("low", "medium", "high")[index % 3],
                category=("study", "personal", "work")[index % 3],
                repeat="daily" if index == 11 else "",
                estimated_duration=30, status="done" if done else "todo",
                completed_at=timezone.now() if done else None,
            )
        Task.objects.create(user=user, title="Demo: Previous year", date=today.replace(year=today.year - 1, month=1, day=1), status="todo")
        entry = JournalEntry.objects.create(user=user, raw_text="I want to study and prepare my presentation.", clean_text="I want to study and prepare my presentation.")
        for title, status in [("Study a chapter", "pending"), ("Prepare slides", "pending"), ("An old idea", "dismissed")]:
            TaskSuggestion.objects.create(user=user, entry=entry, title=title, status=status)
        JournalEntry.objects.create(user=user, raw_text="A quiet day without tasks.", clean_text="A quiet day without tasks.")
        self.stdout.write(self.style.SUCCESS("Fictional demo account created: 13 tasks, 2 entries, 3 suggestions. Current period: 6/12 complete (50%)."))

    @staticmethod
    def stdin_is_terminal():
        import sys
        return sys.stdin.isatty()
