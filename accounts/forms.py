from django import forms

from .models import UserPreferences


class ThemeSelectionForm(forms.Form):
    theme = forms.ChoiceField(choices=UserPreferences.THEME_CHOICES)


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    display_name = forms.CharField(max_length=80, required=False)

    def __init__(self, *args, user, preferences, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.preferences = preferences
        if not self.is_bound:
            self.initial.update({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "display_name": preferences.display_name,
            })

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        self.preferences.display_name = self.cleaned_data["display_name"]
        self.preferences.save(update_fields=["display_name"])
        return self.user