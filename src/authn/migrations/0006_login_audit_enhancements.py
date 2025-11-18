import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authn", "0005_rsakeypair_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="loginauditlog",
            name="success",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="loginauditlog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="login_audit_logs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
