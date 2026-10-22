from django.db.models.signals import pre_delete
from django.dispatch import receiver
from tasks.models import Task
from .models import GoalStep


@receiver(pre_delete, sender=Task)
def preserve_step_completion(sender, instance, **kwargs):
    # Removing a task should not undo a goal step the user already finished.
    GoalStep.objects.filter(task=instance).update(is_done=instance.status == "done")
