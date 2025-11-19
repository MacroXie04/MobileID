from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authn", "0003_alter_userprofile_user_profile_img"),
    ]

    operations = [
        migrations.CreateModel(
            name="FailedLoginAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=150, unique=True)),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("attempt_count", models.PositiveIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("last_attempt", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-last_attempt"],
                "verbose_name": "Failed Login Attempt",
                "verbose_name_plural": "Failed Login Attempts",
            },
        ),
        migrations.CreateModel(
            name="LoginAuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(blank=True, max_length=150)),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("user_agent", models.TextField(blank=True)),
                (
                    "result",
                    models.CharField(
                        choices=[
                            ("success", "Success"),
                            ("failure", "Failure"),
                            ("blocked", "Blocked"),
                        ],
                        max_length=20,
                    ),
                ),
                ("reason", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Login Audit Log",
                "verbose_name_plural": "Login Audit Logs",
            },
        ),
        migrations.AddIndex(
            model_name="loginauditlog",
            index=models.Index(
                fields=["username"], name="authn_logi_usernam_5bd831_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="loginauditlog",
            index=models.Index(
                fields=["created_at"], name="authn_logi_created_1cad83_idx"
            ),
        ),
    ]
