from io import BytesIO
import shutil
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import UserPreferences


def photo(format="PNG", size=(600, 400)):
    output = BytesIO()
    Image.new("RGB", size, "blue").save(output, format=format)
    return SimpleUploadedFile("photo.png", output.getvalue(), content_type="image/png")


class AvatarTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp(prefix="mawj-avatar-test-")
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(shutil.rmtree, self.media)
        self.user = get_user_model().objects.create_user("photo-user")
        self.other = get_user_model().objects.create_user("other-photo")
        self.client.force_login(self.user)

    def test_default_upload_resize_and_private_delivery(self):
        self.assertContains(self.client.get(reverse("profile")), "Default profile avatar")
        self.assertEqual(self.client.get(reverse("avatar")).status_code, 404)
        response = self.client.post(reverse("profile_edit"), {"display_name": "Photo", "avatar": photo()})
        self.assertRedirects(response, reverse("profile"))
        preferences = UserPreferences.objects.get(user=self.user)
        with Image.open(preferences.avatar.path) as image:
            self.assertEqual(image.size, (512, 341))
            self.assertEqual(image.format, "PNG")
        response = self.client.get(reverse("avatar"))
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        response.close()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("avatar")).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("avatar")).status_code, 302)

    def test_removal_and_replacement_clean_up_old_files(self):
        self.client.post(reverse("profile_edit"), {"avatar": photo()})
        original = UserPreferences.objects.get(user=self.user).avatar.path
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("profile_edit"), {"avatar": photo(format="JPEG")})
        from pathlib import Path
        self.assertFalse(Path(original).exists())
        current = UserPreferences.objects.get(user=self.user).avatar.path
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("profile_edit"), {"remove_avatar": "on"})
        self.assertFalse(Path(current).exists())
        self.assertFalse(UserPreferences.objects.get(user=self.user).avatar)

    def test_invalid_type_size_and_conflicting_actions(self):
        for upload in [SimpleUploadedFile("script.svg", b"<svg></svg>"), photo(format="GIF"), photo(size=(4097, 1))]:
            response = self.client.post(reverse("profile_edit"), {"avatar": upload})
            self.assertEqual(response.status_code, 200)
            self.assertIn("avatar", response.context["form"].errors)
        large = photo()
        large.size = 3 * 1024 * 1024
        from .forms import ProfileEditForm
        form = ProfileEditForm({}, {"avatar": large}, user=self.user, preferences=UserPreferences.objects.get(user=self.user))
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)
        response = self.client.post(reverse("profile_edit"), {"avatar": photo(), "remove_avatar": "on"})
        self.assertIn("avatar", response.context["form"].errors)
