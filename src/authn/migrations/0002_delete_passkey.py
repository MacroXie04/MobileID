# Generated manually to remove Passkey model

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('authn', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Passkey',
        ),
    ]
