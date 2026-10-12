from django import forms

from .models import JournalEntry


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["raw_text"]
        widgets = {"raw_text": forms.Textarea(attrs={"rows": 10})}
        labels = {"raw_text": "How was your day?"}
