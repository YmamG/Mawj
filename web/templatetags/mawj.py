import json
import re
from functools import lru_cache
from pathlib import Path
from django import template
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.safestring import mark_safe
register = template.Library()
MESSAGES = json.loads((Path(__file__).resolve().parents[1] / 'translations.json').read_text())
@register.simple_tag(takes_context=True)
def tr(context, text):
    if context.get('lang') != 'ar':
        return text
    dated = re.fullmatch(r'(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', str(text))
    if dated:
        return f'{dated[1]} {MESSAGES[dated[2]]}'
    return MESSAGES.get(text, text)
@register.simple_tag
def icon(name):
    return mark_safe(_svg(name))
@lru_cache(maxsize=64)
def _svg(name):
    if name not in ('Sun','CheckCircle','Notebook','ChartBar','CalendarBlank','UserCircle','Plus','SignOut','Check','X','MagnifyingGlass','Sparkle','Plant','PencilSimple','Trash','ArrowUpRight','Bell','CaretLeft','CaretRight'):
        return ''
    return (settings.BASE_DIR / 'templates' / 'web' / f'icon-{name}.html').read_text()
@register.filter
def display_date(value):
    if not value:
        return ''
    if isinstance(value, str):
        value = parse_datetime(value) or parse_date(value)
    if not value:
        return ''
    if hasattr(value, 'hour') and timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime('%d/%m/%Y')
@register.filter
def decrement(value):
    return int(value)-1
@register.filter
def increment(value):
    return int(value)+1
