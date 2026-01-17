from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("screening", "0002_alter_session_insights"),
    ]

    operations = [
        migrations.AddField(
            model_name="resumechunk",
            name="doc_type",
            field=models.CharField(default="resume", max_length=20),
        ),
    ]
