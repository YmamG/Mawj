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
        ]
        widgets = {
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
        # Lets the edit form pre-fill the datetime-local input correctly
        self.fields["deadline"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_priority(self):
        return self.cleaned_data.get("priority") or "medium"

    def clean_estimated_duration(self):
        duration = self.cleaned_data.get("estimated_duration")
        if duration is not None and not 1 <= duration <= 1440:
            raise forms.ValidationError("Enter a duration between 1 and 1440 minutes.")
        return duration
