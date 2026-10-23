from django.conf import settings
from django.db import models
import uuid


def goal_image_path(instance, filename):
    return f"goal-images/{instance.user_id}/{uuid.uuid4().hex}.jpg"


class Goal(models.Model):
    CATEGORY_CHOICES = [("personal", "Personal"), ("study", "Study"), ("work", "Work")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=200)
    why = models.TextField(blank=True, max_length=2000)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="personal")
    target_date = models.DateField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    marked_complete = models.BooleanField(default=False)
    image = models.ImageField(upload_to=goal_image_path, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title


class GoalStep(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField(max_length=200)
    target_date = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    task = models.OneToOneField("tasks.Task", on_delete=models.SET_NULL, null=True, blank=True, related_name="goal_step")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    @property
    def done(self):
        return self.task.status == "done" if self.task_id else self.is_done
