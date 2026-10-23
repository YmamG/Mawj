from django.db import transaction
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from tasks.models import Task
from .models import Goal, GoalStep


@receiver(pre_delete, sender=Task)
def preserve_step_completion(sender, instance, **kwargs):
    # Removing a task should not undo a goal step the user already finished.
    GoalStep.objects.filter(task=instance).update(is_done=instance.status == "done")


@receiver(post_delete, sender=Goal)
def delete_goal_image(sender, instance, **kwargs):
    if instance.image and instance.image.name:
        storage, name = instance.image.storage, instance.image.name
        transaction.on_commit(lambda: storage.delete(name))
