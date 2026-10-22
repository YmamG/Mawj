from django import forms
from django.utils import timezone
from .models import Goal, GoalStep


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["title", "why", "category", "target_date"]
        widgets = {"why": forms.Textarea(attrs={"rows": 3}), "target_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        original = self.instance.target_date if self.instance.pk else None
        self.fields["target_date"].widget.attrs["min"] = min(timezone.localdate(), original or timezone.localdate()).isoformat()

    def clean_category(self):
        return self.cleaned_data.get("category") or "personal"

    def clean_target_date(self):
        value = self.cleaned_data.get("target_date")
        if value and value < timezone.localdate() and value != self.instance.target_date:
            raise forms.ValidationError("Choose today or a future date.")
        if value and self.instance.pk and self.instance.steps.filter(target_date__gt=value).exists():
            raise forms.ValidationError("Choose a goal date on or after your planned steps.")
        return value


class StepForm(forms.ModelForm):
    class Meta:
        model = GoalStep
        fields = ["title", "target_date"]
        widgets = {"target_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, goal, **kwargs):
        super().__init__(*args, **kwargs)
        self.goal = goal
        self.fields["title"].widget.attrs.update(placeholder="One small next step…", autocomplete="off")
        self.fields["target_date"].widget.attrs["min"] = timezone.localdate().isoformat()
        if goal.target_date:
            self.fields["target_date"].widget.attrs["max"] = goal.target_date.isoformat()

    def clean_target_date(self):
        value = self.cleaned_data.get("target_date")
        if value and value < timezone.localdate():
            raise forms.ValidationError("Choose today or a future date.")
        if value and self.goal.target_date and value > self.goal.target_date:
            raise forms.ValidationError("Choose a step date on or before your goal date.")
        return value
