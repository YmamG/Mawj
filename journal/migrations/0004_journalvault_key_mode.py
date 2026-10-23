from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("journal", "0003_vaulttaskacceptance")]
    operations = [
        migrations.AddField(
            model_name="journalvault",
            name="key_mode",
            field=models.CharField(default="legacy", max_length=12),
        ),
    ]
