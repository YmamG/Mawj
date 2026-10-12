from django.conf import settings
from django.db import models


class JournalEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journal_entries")
    raw_text = models.TextField()    # exactly what the user wrote
    clean_text = models.TextField(blank=True)    # organized version
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Entry {self.pk} by {self.user}"


class TaskSuggestion(models.Model):
    """A task the AI found in a journal entry. It becomes a real Task
    only after the user accepts it."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("dismissed", "Dismissed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_suggestions")
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="suggestions")
    title = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, default="medium")
    estimated_duration = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return self.title
