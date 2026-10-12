from .models import UserPreferences


def theme_choices(request):
    theme = "tide"
    if request.user.is_authenticated:
        theme = (
            UserPreferences.objects.filter(user=request.user)
            .values_list("theme", flat=True)
            .first()
            or theme
        )
    return {
        "theme_choices": UserPreferences.THEME_CHOICES,
        "current_theme": theme,
    }


def frontend_link(request):
    from django.conf import settings
    return {"frontend_url": settings.FRONTEND_URL}
