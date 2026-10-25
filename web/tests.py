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

    def test_public_navigation_links_work_in_both_languages(self):
        from html.parser import HTMLParser
        from urllib.parse import urlsplit
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.paths = set()
            def handle_starttag(self, tag, attrs):
                href = dict(attrs).get('href', '')
                if tag == 'a' and href.startswith('/'):
                    self.paths.add(urlsplit(href).path)
        for language in ('en', 'ar'):
            self.client.cookies['mawj-language'] = language
            parser = Links()
            parser.feed(self.client.get('/').content.decode())
            self.assertGreaterEqual(len(parser.paths), 4)
            for path in parser.paths:
                with self.subTest(language=language, path=path):
                    self.assertEqual(self.client.get(path, follow=True).status_code, 200)

    def test_slashless_bookmark_redirect_preserves_query_and_unknown_path_stays_404(self):
        response = self.client.get('/login?next=%2Fapp%2Ftasks%2F')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/login/?next=%2Fapp%2Ftasks%2F')
        self.assertEqual(self.client.get('/does-not-exist').status_code, 404)
        self.assertEqual(self.client.post('/api/tasks', data={}).status_code, 404)

    def test_journal_uses_clear_notebook_layout_and_single_primary_action(self):
        JournalEntry.objects.create(user=self.owner, raw_text="A private page", clean_text="A private page")
        self.client.force_login(self.owner)
        response = self.client.get('/app/journal/')
        self.assertContains(response, 'class="page-heading journal-heading"')
        self.assertContains(response, 'class="entry-card journal-page-card"')
        self.assertContains(response, 'Write a new entry')
        self.assertContains(response, 'Writing assistant')
        self.assertNotContains(response, 'class="banner journal-mode"')

    def test_task_and_journal_search_stay_compact_until_opened(self):
        self.client.force_login(self.owner)
        tasks = self.client.get('/app/tasks/')
        self.assertContains(tasks, 'class="search-dock"')
        self.assertContains(tasks, 'aria-expanded="false"')
        filtered_tasks = self.client.get('/app/tasks/?q=private')
        self.assertContains(filtered_tasks, 'class="search-dock is-expanded"')
        journal = self.client.get('/app/journal/')
        self.assertContains(journal, 'class="search-dock journal-search"')
        filtered_journal = self.client.get('/app/journal/?q=page')
        self.assertContains(filtered_journal, 'class="search-dock journal-search is-expanded"')

    def test_today_shows_each_summary_count_once(self):
        Task.objects.create(user=self.owner, title='An undated task')
        self.client.force_login(self.owner)
        response = self.client.get('/app/today/')
        self.assertContains(response, 'class="today-glance"')
        self.assertContains(response, "Today's plan")
        self.assertNotContains(response, 'class="stats-row"')
        self.assertNotContains(response, 'Today &amp; undated <span>')

    def test_privacy_page_leads_with_plain_summary_and_keeps_details_optional(self):
        self.client.cookies['mawj-language'] = 'en'
        response = self.client.get('/privacy/')
        self.assertContains(response, 'Privacy, in plain language.')
        self.assertContains(response, '<details class="privacy-details">')
        self.assertContains(response, 'Other users cannot see your journals, tasks, or goals.')
