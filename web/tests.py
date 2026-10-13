from django.contrib.auth import get_user_model
from django.test import TestCase
from tasks.models import Task
from journal.models import JournalEntry

class TemplateEditionTests(TestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user('template-owner',password='test-password')
        self.other=get_user_model().objects.create_user('template-other',password='test-password')

    def test_workspace_renders_owned_records_without_javascript_and_escapes_titles(self):
        Task.objects.create(user=self.owner,title='<script>alert(1)</script>')
        Task.objects.create(user=self.other,title='private-other-task')
        self.client.force_login(self.owner)
        response=self.client.get('/app/tasks/')
        self.assertContains(response,'&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response,'<script>alert(1)</script>')
        self.assertNotContains(response,'private-other-task')
        self.assertIn('no-store',response.headers['Cache-Control'])

    def test_anonymous_workspace_requires_login(self):
        response=self.client.get('/app/tasks/')
        self.assertEqual(response.status_code,302)
        self.assertTrue(response['Location'].startswith('/login/'))

    def test_arabic_public_templates_do_not_need_next_or_react(self):
        self.client.cookies['mawj-language']='ar'
        response=self.client.get('/')
        self.assertContains(response,'dir="rtl"')
        self.assertContains(response,'مساحة لأفكارك.')
        self.assertNotContains(response,'/_next/')
        self.assertContains(response,'static/web/app.js')

    def test_calendar_json_preserves_full_owned_text_without_executable_script_markup(self):
        note='Full note '*80+'</script><script>alert(1)</script>'
        JournalEntry.objects.create(user=self.owner,raw_text=note,clean_text=note)
        JournalEntry.objects.create(user=self.other,raw_text='private-other-journal')
        self.client.force_login(self.owner)
        response=self.client.get('/app/calendar/')
        self.assertContains(response,'Full note '*80)
        self.assertNotContains(response,'</script><script>alert(1)</script>')
        self.assertNotContains(response,'private-other-journal')
