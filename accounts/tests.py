from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from journal.models import JournalEntry
from tasks.models import Task

from .models import UserPreferences


class ProfileViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(
            "alice",
            password="Strong-pass!9",
            first_name="Alice",
            last_name="Example",
            email="alice@example.com",
        )
        self.bob = user_model.objects.create_user("bob", password="Strong-pass!9")
        self.client.force_login(self.alice)

    def test_profile_shows_user_details_and_private_statistics(self):
        JournalEntry.objects.create(user=self.alice, raw_text="Alice's entry")
        JournalEntry.objects.create(user=self.bob, raw_text="Bob's entry")
        Task.objects.create(user=self.alice, title="Completed", status="done")
        Task.objects.create(user=self.alice, title="Pending")
        Task.objects.create(user=self.bob, title="Bob's task")

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice")
        self.assertContains(response, "Alice")
        self.assertContains(response, "Example")
        self.assertContains(response, "alice@example.com")
        self.assertContains(response, "Journal entries: 1")
        self.assertContains(response, "Total tasks: 2")
        self.assertContains(response, "Completed tasks: 1")
        self.assertContains(response, "Pending tasks: 1")
        self.assertNotContains(response, "Bob's entry")
        self.assertNotContains(response, "Bob's task")

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_edit_only_updates_allowed_fields(self):
        response = self.client.get(reverse("profile_edit"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="username"')

        self.client.post(reverse("profile_edit"), {
            "username": "changed",
            "first_name": "Alicia",
            "last_name": "Example",
            "email": "alicia@example.com",
            "display_name": "Ali",
        })

        self.alice.refresh_from_db()
        preferences = UserPreferences.objects.get(user=self.alice)
        self.assertEqual(self.alice.username, "alice")
        self.assertEqual(self.alice.first_name, "Alicia")
        self.assertEqual(self.alice.last_name, "Example")
        self.assertEqual(self.alice.email, "alicia@example.com")
        self.assertEqual(preferences.display_name, "Ali")

    def test_theme_selection_is_saved_to_logged_in_user(self):
        response = self.client.post(reverse("theme_update"), {
            "theme": "orchid",
            "next": reverse("profile"),
        })

        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(UserPreferences.objects.get(user=self.alice).theme, "orchid")
        self.assertEqual(
            self.client.get(reverse("profile")).context["current_theme"],
            "orchid",
        )

    def test_invalid_theme_is_rejected(self):
        response = self.client.post(reverse("theme_update"), {"theme": "unknown"})
        self.assertEqual(response.status_code, 400)
