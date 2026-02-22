from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("authn", "0008_access_token_blacklist"),
    ]

    operations = [
        migrations.DeleteModel(
            name="PasskeyCredential",
        ),
    ]
