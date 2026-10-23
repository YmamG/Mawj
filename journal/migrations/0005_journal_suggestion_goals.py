from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("goals", "0001_initial"),
        ("journal", "0004_journalvault_key_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasksuggestion",
            name="kind",
            field=models.CharField(default="task", max_length=8),
        ),
        migrations.AddField(
            model_name="tasksuggestion",
            name="category",
            field=models.CharField(default="personal", max_length=20),
        ),
        migrations.AddField(
            model_name="vaulttaskacceptance",
            name="goal",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="goals.goal"),
        ),
    ]
