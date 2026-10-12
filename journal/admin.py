from django.contrib import admin

from .models import JournalEntry, TaskSuggestion

admin.site.register(JournalEntry)
admin.site.register(TaskSuggestion)
