from django.contrib.auth import get_user_model
from django.test import TestCase

from journal.models import JournalEntry
from tasks.models import Task


class AccountDirectoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        cls.operator = user.objects.create_user("operator", is_staff=True, is_superuser=True)
        cls.member = user.objects.create_user("member", email="private-email@example.test", first_name="PrivateFirstName", last_name="PrivateLastName")
        cls.member.password = "private-password-hash"
        cls.member.save(update_fields=["password"])
        cls.staff = user.objects.create_user("staff", is_staff=True)
        cls.nonstaff_superuser = user.objects.create_user("nonstaff-superuser", is_superuser=True)
        Task.objects.create(user=cls.member, title="Private task content")
        JournalEntry.objects.create(user=cls.member, raw_text="Private journal content")

    def test_anonymous_and_nonoperators_cannot_list_accounts(self):
        self.assertRedirects(self.client.get("/operator/accounts/"), "/login/?next=/operator/accounts/", fetch_redirect_response=False)
        for user in (self.member, self.staff, self.nonstaff_superuser):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.get("/operator/accounts/").status_code, 403)

    def test_operator_sees_only_directory_fields_and_no_private_content(self):
        self.client.force_login(self.operator)
        response = self.client.get("/operator/accounts/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "member")
        self.assertIn("no-store", response.headers["Cache-Control"])
        rows = list(response.context["registered_accounts"])
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(set(row) == {"username", "date_joined"} for row in rows))
        for secret in (self.member.email, self.member.first_name, self.member.last_name, self.member.password, "Private task content", "Private journal content"):
            self.assertNotContains(response, secret)
        self.assertNotContains(response, 'href="/admin/')
        self.assertNotContains(response, 'type="password"')

    def test_directory_has_no_mutation_or_detail_endpoints(self):
        self.client.force_login(self.operator)
        for method in ("post", "put", "patch", "delete"):
            response = getattr(self.client, method)("/operator/accounts/", data='{}', content_type="application/json")
            self.assertEqual(response.status_code, 405)
        for suffix in (f"{self.member.pk}/", f"{self.member.pk}/change/", f"{self.member.pk}/password/", "export/", "login-as/"):
            self.assertEqual(self.client.get("/operator/accounts/" + suffix).status_code, 404)
        self.member.refresh_from_db()
        self.assertEqual(self.member.password, "private-password-hash")
        self.assertTrue(Task.objects.filter(user=self.member).exists())
        self.assertTrue(JournalEntry.objects.filter(user=self.member).exists())

    def test_pagination_and_arabic_escaping(self):
        user = get_user_model()
        user.objects.bulk_create([user(username=f"extra-{n}") for n in range(51)])
        user.objects.create_user("<script>private</script>")
        self.client.force_login(self.operator)
        self.client.cookies["mawj-language"] = "ar"
        response = self.client.get("/operator/accounts/")
        self.assertContains(response, 'dir="rtl"')
        self.assertContains(response, "الحسابات المسجّلة")
        self.assertContains(response, "&lt;script&gt;private&lt;/script&gt;")
        self.assertNotContains(response, "<script>private</script>")
        self.assertEqual(len(response.context["registered_accounts"]), 50)
        second = self.client.get("/operator/accounts/?page=2")
        self.assertEqual(len(second.context["registered_accounts"]), 6)
        self.assertEqual(self.client.get("/operator/accounts/?page=invalid").status_code, 200)

    def test_profile_link_is_visible_only_to_operator(self):
        self.client.force_login(self.operator)
        self.assertContains(self.client.get("/app/profile/"), 'href="/operator/accounts/"')
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get("/app/profile/"), 'href="/operator/accounts/"')
