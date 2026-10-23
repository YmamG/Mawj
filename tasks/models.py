from django.conf import settings
from django.db import models


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    STATUS_CHOICES = [
        ("todo", "Todo"),
        ("done", "Done"),
    ]

    CATEGORY_CHOICES = [("", "Uncategorized"), ("study", "Study"), ("personal", "Personal"), ("work", "Work"), ("custom", "Custom")]
    REPEAT_CHOICES = [("", "Does not repeat"), ("daily", "Daily"), ("weekly", "Weekly")]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    custom_category = models.CharField(max_length=40, blank=True)
    repeat = models.CharField(max_length=10, choices=REPEAT_CHOICES, blank=True)
    previous_occurrence = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="next_occurrence")
    reminder_at = models.DateTimeField(null=True, blank=True)
    reminder_dismissed = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="todo")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "date", "start_time"]

    def __str__(self):
        return self.title
