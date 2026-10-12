from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    """Form for creating and editing a task.

    Note: 'user', 'status' and 'completed_at' are NOT in the form.
    The user is set in the view (request.user), and status/completed_at
    are changed only by the toggle view.
    """

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "date",
            "start_time",
            "deadline",
            "estimated_duration",
            "priority",
            "category",
            "repeat",
            "reminder_at",
        ]
        widgets = {
            "reminder_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 3}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }
        labels = {
            "estimated_duration": "Estimated duration (minutes)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["priority"].required = False
        self.fields["reminder_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        # Lets the edit form pre-fill the datetime-local input correctly
        self.fields["deadline"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_priority(self):
        return self.cleaned_data.get("priority") or "medium"

    def clean_estimated_duration(self):
        duration = self.cleaned_data.get("estimated_duration")
        if duration is not None and not 1 <= duration <= 1440:
            raise forms.ValidationError("Enter a duration between 1 and 1440 minutes.")
        return duration

    def clean(self):
        data = super().clean()
        if data.get("date") and data.get("start_time"):
            from datetime import datetime
            from django.utils import timezone
            scheduled = timezone.make_aware(datetime.combine(data["date"], data["start_time"]))
            unchanged = self.instance.pk and data["date"] == self.instance.date and data["start_time"] == self.instance.start_time
            if scheduled < timezone.now() and not unchanged:
                self.add_error("start_time", "Choose a start time that has not passed.")
        if data.get("repeat") and not data.get("date"):
            self.add_error("date", "Choose a date for a repeating task.")
        if data.get("reminder_at"):
            from django.utils import timezone
            original = self.instance.reminder_at if self.instance.pk else None
            if original:
                original = original.replace(second=0, microsecond=0)
            # ModelForm has not applied cleaned values to the instance at this point.
            if data["reminder_at"] != original and data["reminder_at"] <= timezone.now():
                self.add_error("reminder_at", "Choose a future reminder time.")
        return data

    def clean_date(self):
        from django.utils import timezone
        value = self.cleaned_data.get("date")
        original = self.instance.date if self.instance.pk else None
        if value and value < timezone.localdate() and value != original:
            raise forms.ValidationError("Choose today or a future date.")
        return value

    def clean_deadline(self):
        from django.utils import timezone
        value = self.cleaned_data.get("deadline")
        original = self.instance.deadline if self.instance.pk else None
        if original:
            original = original.replace(second=0, microsecond=0)
        if value and value < timezone.now() and value != original:
            raise forms.ValidationError("Choose a future deadline.")
        return value
