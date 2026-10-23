# نشر mawj على PythonAnywhere

هذا الدليل لنسخة **Django templates** فقط؛ لا يحتاج Node.js. اختُبرت إعدادات الإنتاج محليًا، ولم يُنشر الموقع ضمن هذه المراجعة. لا توجد استضافة مضمونة 100%؛ التحقق من الموقع الفعلي خطوة مستقلة.

## قبل البدء

اعتمد فرع `django-templates` من مستودع `YmamG/Mawj`، مع الاحتفاظ بقاعدة بياناتك و`.env` والصور محليًا. لا ترفع هذه الملفات إلى GitHub. أنشئ حسابًا على [PythonAnywhere](https://www.pythonanywhere.com/)؛ اسم حساب الاستضافة يحدد الرابط الافتراضي، وليس اسم GitHub.

الخطة المجانية محدودة وتتطلب تجديد صلاحية الموقع دوريًا، وقد تمنع الاتصال بمزوّد AI خارج قائمة السماح. ابدأ ببيانات وهمية و`AI_PROVIDER=demo`؛ هذا وضع قواعد محلية وليس نموذج ذكاء اصطناعي مباشرًا.

## تنزيل الكود على الاستضافة

افتح Bash console في PythonAnywhere:

```bash
git clone --branch django-templates --single-branch https://github.com/YmamG/Mawj.git mawj
cd ~/mawj
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

تأكد من توفر Python 3.12، واختر الإصدار نفسه لاحقًا في Web. إن لم يتوفر، اختر إصدارًا مدعومًا ومطابقًا في الخطوتين. المستودع الخاص يحتاج وسيلة وصول آمنة تدعمها الاستضافة؛ لا ترسل رمز وصول في المحادثة ولا تضعه في عنوان clone.

## الملف الخاص على الاستضافة

أنشئ `~/mawj/.env` **على الاستضافة فقط**. استخدم `.env.production.example` مرجعًا؛ لا يُقرأ تلقائيًا، والمفتاح الفارغ يرفض تشغيل الإنتاج. لا تستبدل ملف جهازك. اكتب:

```dotenv
DJANGO_ALLOWED_HOSTS=PA_USERNAME.pythonanywhere.com
AI_PROVIDER=demo
```

استبدل `PA_USERNAME` باسم حساب PythonAnywhere الفعلي. ولّد مفتاحًا خاصًا مرة واحدة في Bash console؛ الأمر يكتبه دون طباعته:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import secrets
from dotenv import dotenv_values, set_key
path = Path('.env')
if dotenv_values(path).get('DJANGO_SECRET_KEY'):
    raise SystemExit('A key already exists; keep it unchanged.')
set_key(str(path), 'DJANGO_SECRET_KEY', secrets.token_urlsafe(64))
path.chmod(0o600)
print('Production key saved privately.')
PY
```

لا تشارك المفتاح ولا تغيّره مع كل تحديث. عند تفعيل اليوميات المشفّرة يستخدم التطبيق هذا المفتاح لاشتقاق مفاتيح اليوميات ما لم تضبط `MAWJ_JOURNAL_KEY` مستقلًا؛ فقد المفتاح المستخدم أو تغييره يجعل التدوينات المشفّرة غير قابلة للقراءة. إعداد الإنتاج يحدد `DEBUG=False`، ويطلب مضيفًا صريحًا ومفتاحًا قويًا، ويفرض HTTPS وملفات ارتباط آمنة. إعداد التشغيل المحلي منفصل.

```bash
.venv/bin/python manage.py migrate --settings=config.settings_production
.venv/bin/python manage.py collectstatic --noinput --settings=config.settings_production
.venv/bin/python manage.py check --deploy --settings=config.settings_production
```

المتوقع حاليًا تحذير `security.W004` لأن HSTS مؤجل إلى ما بعد التحقق من HTTPS الفعلي. أي خطأ آخر يحتاج مراجعة. لا تستخدم `runserver` للنشر.

## إعداد Web

1. أضف تطبيقًا عبر **Manual configuration** بإصدار Python نفسه.
2. عيّن Source code وWorking directory إلى `/home/PA_USERNAME/mawj`، وVirtualenv إلى `/home/PA_USERNAME/mawj/.venv`.
3. افتح ملف WSGI المرتبط من Web واستبدل المثال الافتراضي بهذا المحتوى بعد تعديل اسم المستخدم:

```python
import sys

project = '/home/PA_USERNAME/mawj'
if project not in sys.path:
    sys.path.insert(0, project)

from config.wsgi_production import application
```

4. أضف Static files mapping: العنوان `/static/` والمسار `/home/PA_USERNAME/mawj/staticfiles`.
5. **لا تضف mapping لـ`/media/`**؛ صور الملف الشخصي خاصة وتُقدّم عبر Django من `/api/profile/avatar/`.
6. اضغط **Reload**، وافتح `https://PA_USERNAME.pythonanywhere.com/`. المنصة توفر شهادة النطاق الافتراضي. راجع Error log إن ظهر خطأ، دون مشاركة أسرار.
7. بعد التأكد من HTTPS فعّل **Force HTTPS** من Web. تحقق من انتقال HTTP إلى HTTPS دون حلقة إعادة توجيه. لا تضف ثقة في ترويسات الوكيل دون التحقق من إعداد الاستضافة.

## التحقق قبل مشاركة الرابط

- اختبر من الجوال حسابًا وهميًا، الخروج والدخول، المهام واليوميات واقتراحاتها، والتقويم والإحصاءات، والعربية والطابع والصور.
- أعد تحميل التطبيق من Web ثم تحقق من بقاء الحساب والمهام. قاعدة الاستضافة مستقلة عن جهازك؛ لن تظهر حسابات Windows تلقائيًا.
- تحقق من تحميل CSS والخطوط، وخصوصية بيانات كل حساب وصورته، ومن HTTPS وعدم وجود أخطاء في السجل.
- بعد التحقق من HTTPS يمكن ضبط مدة HSTS قصيرة ومراجعتها؛ لا تفعّل تغطية النطاقات الفرعية أو preload تلقائيًا. هذا البند ما زال معلقًا قبل نشر الموقع الفعلي.
- التنبيهات الحالية داخل الموقع فقط. اختيار SMTP في إعداد الإنتاج لا يضيف إرسال بريد؛ إعداد خدمة بريد واختبارها مطلوبان إذا أُضيفت الميزة لاحقًا.
- مسار `/admin/` معطّل في إعداد الإنتاج، بما فيه إدارة المستخدمين وتغيير كلمات مرورهم. لا تحتاج إلى إنشاء superuser لتشغيل الموقع. حساب موجود بهذه الصلاحية لا يتجاوز ملكية السجلات في واجهة موج. تبقى صلاحيات مشغّل الخادم وقاعدة البيانات قائمة؛ هذا ليس تشفيرًا من طرف إلى طرف ولا يمنع الوصول المباشر أو إعادة تفعيل لوحة الإدارة بواسطة من يملك الكود.
- للاطلاع على الحسابات المسجّلة فقط، سجّل الدخول بحساب مدير نشط يحمل صلاحيتَي staff وsuperuser، وافتح `/operator/accounts/` أو الرابط في صفحة «مساحتي». تعرض القائمة أسماء المستخدمين وتواريخ التسجيل فقط، ولا تتيح فتح محتوى حساب آخر أو تغيير بياناته أو كلمة مروره. إنشاء هذا الحساب اختياري عبر `.venv/bin/python manage.py createsuperuser --settings=config.settings_production` على الاستضافة، ولا يعيد تشغيل لوحة Django المعطّلة. احتفظ بكلمة مروره لنفسك.

ابدأ ببيانات وهمية. SQLite مناسبة لعرض صغير وتحتاج نسخًا احتياطية: احتفظ بنسخة متسقة من `db.sqlite3` والصور و`.env` قبل التحديث أو النقل، مع إيقاف الكتابة أثناء نسخ SQLite. لا تضع النسخ في المستودع أو static. لا يُضمن تحمل مستخدمين كثيرين بهذه الخطة.

## التحديث لاحقًا

بعد دفع تحديثات جهازك إلى مستودعك، نفّذ على الاستضافة:

```bash
cd ~/mawj
git pull --ff-only
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate --settings=config.settings_production
.venv/bin/python manage.py collectstatic --noinput --settings=config.settings_production
.venv/bin/python manage.py check --deploy --settings=config.settings_production
```

اضغط Reload في Web واختبر الدخول. إن منع Git التحديث بسبب تغييرات محلية، افحصها بدل استخدام reset أو حذف البيانات.

## المراجع الرسمية

- [نشر Django](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)
- [الملفات الثابتة](https://help.pythonanywhere.com/pages/DjangoStaticFiles/)
- [HTTPS](https://help.pythonanywhere.com/pages/HTTPSSetup/) و[فرض HTTPS](https://help.pythonanywhere.com/pages/ForcingHTTPS/)
- [حدود الحساب المجاني](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)
- [قائمة Django للتحقق قبل النشر](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
