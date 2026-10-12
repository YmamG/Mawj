from django.conf import settings
from django.db import models


class UserPreferences(models.Model):
    THEME_CHOICES = [
        ("tide", "Tide"),
        ("orchid", "Orchid"),
        ("forest", "Forest"),
        ("sunrise", "Sunrise"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default="tide")
    display_name = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"Preferences for {self.user}"
