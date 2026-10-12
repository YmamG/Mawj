from django import forms
from django.core.files.base import ContentFile
from django.db import transaction
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import warnings

from .models import UserPreferences


class ThemeSelectionForm(forms.Form):
    theme = forms.ChoiceField(choices=UserPreferences.THEME_CHOICES)


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    display_name = forms.CharField(max_length=80, required=False)
    avatar = forms.ImageField(required=False, help_text="PNG or JPEG, up to 2 MB. Images are resized to 512 pixels.")
    remove_avatar = forms.BooleanField(required=False, label="Remove photo and use the default avatar")

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

    def clean_avatar(self):
        upload = self.cleaned_data.get("avatar")
        if not upload:
            return None
        if upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Choose an image smaller than 2 MB.")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                upload.seek(0)
                with Image.open(upload) as image:
                    if image.format not in ("PNG", "JPEG"):
                        raise forms.ValidationError("Choose a PNG or JPEG image.")
                    if image.width > 4096 or image.height > 4096:
                        raise forms.ValidationError("Choose an image up to 4096 pixels wide and tall.")
                    from PIL import ImageOps
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    image.thumbnail((512, 512))
                    output = BytesIO()
                    image.save(output, format="PNG")
            return ContentFile(output.getvalue(), name="avatar.png")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise forms.ValidationError("This image could not be read. Choose another PNG or JPEG.")

    def clean(self):
        data = super().clean()
        if data.get("avatar") and data.get("remove_avatar"):
            self.add_error("avatar", "Choose either a new photo or removal, not both.")
        return data

    @transaction.atomic
    def save(self):
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        self.preferences.display_name = self.cleaned_data["display_name"]
        old_avatar = self.preferences.avatar.name
        upload = self.cleaned_data.get("avatar")
        removing = self.cleaned_data.get("remove_avatar")
        if removing:
            self.preferences.avatar = ""
        elif upload:
            self.preferences.avatar = upload
        self.preferences.save(update_fields=["display_name", "avatar"])
        if old_avatar and (upload or removing):
            storage = self.preferences.avatar.storage
            transaction.on_commit(lambda: storage.delete(old_avatar))
        return self.user