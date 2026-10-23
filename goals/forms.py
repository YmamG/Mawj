from django import forms
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
import warnings
from .models import Goal, GoalStep


class GoalForm(forms.ModelForm):
    remove_image = forms.BooleanField(required=False)

    class Meta:
        model = Goal
        fields = ["title", "why", "category", "target_date", "image"]
        widgets = {"why": forms.Textarea(attrs={"rows": 3}), "target_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_image_name = self.instance.image.name if self.instance.pk and self.instance.image else ""
        self.fields["category"].required = False
        self.fields["image"].required = False
        original = self.instance.target_date if self.instance.pk else None
        self.fields["target_date"].widget.attrs["min"] = min(timezone.localdate(), original or timezone.localdate()).isoformat()

    def clean_category(self):
        return self.cleaned_data.get("category") or "personal"

    def clean_image(self):
        upload = self.cleaned_data.get("image")
        if not upload or getattr(upload, "name", "") == self.original_image_name:
            return upload
        if upload.size > 3 * 1024 * 1024:
            raise forms.ValidationError("Choose an image smaller than 3 MB.")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                upload.seek(0)
                with Image.open(upload) as image:
                    if image.format not in ("PNG", "JPEG", "WEBP"):
                        raise forms.ValidationError("Choose a PNG, JPEG or WebP image.")
                    if image.width > 6000 or image.height > 6000:
                        raise forms.ValidationError("Choose an image up to 6000 pixels wide and tall.")
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    image.thumbnail((1600, 1200))
                    output = BytesIO()
                    image.save(output, format="JPEG", quality=88, optimize=True)
            return ContentFile(output.getvalue(), name="goal.jpg")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise forms.ValidationError("This image could not be read. Choose another image.")

    def clean(self):
        data = super().clean()
        if data.get("image") and data.get("remove_image") and getattr(data["image"], "name", "") != self.original_image_name:
            self.add_error("image", "Choose either a new image or removal, not both.")
        return data

    @transaction.atomic
    def save(self, commit=True):
        goal = super().save(commit=False)
        if self.cleaned_data.get("remove_image"):
            goal.image = ""
        if not commit:
            return goal
        goal.save()
        self.save_m2m()
        current_name = goal.image.name if goal.image else ""
        if self.original_image_name and self.original_image_name != current_name:
            storage = goal.image.storage
            transaction.on_commit(lambda: storage.delete(self.original_image_name))
        return goal

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
