from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tasks", "0002_task_category_task_previous_occurrence_and_more")]
    operations = [
        migrations.AddField(
            model_name="task",
            name="custom_category",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AlterField(
            model_name="task",
            name="category",
            field=models.CharField(blank=True, choices=[("", "Uncategorized"), ("study", "Study"), ("personal", "Personal"), ("work", "Work"), ("custom", "Custom")], max_length=20),
        ),
    ]
