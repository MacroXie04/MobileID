from src.authn.models import UserProfile
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, m2m_changed
from django.dispatch import receiver
from src.index.models import Barcode, UserBarcodeSettings, BarcodeUsage


@receiver(post_migrate)
def bootstrap_groups_and_perms(sender, **kwargs):
    staff_group, _ = Group.objects.get_or_create(name="Staff")
    user_group, _ = Group.objects.get_or_create(name="User")
    school_group, _ = Group.objects.get_or_create(name="School")

    staff_group.permissions.set(Permission.objects.all())

    full_models = [UserProfile, Barcode, UserBarcodeSettings, BarcodeUsage]

    full_perms = []
    for model in full_models:
        ct = ContentType.objects.get_for_model(model)
        full_perms += Permission.objects.filter(content_type=ct)

    view_perms = []

    target_perms = full_perms + view_perms
    user_group.permissions.set(target_perms)
    school_group.permissions.set(target_perms)


@receiver(m2m_changed, sender=User.groups.through)
def keep_is_staff_in_sync(sender, instance: User, action, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        try:
            staff_group = Group.objects.get(name="Staff")
        except Group.DoesNotExist:
            return

        should_be_staff = instance.groups.filter(pk=staff_group.pk).exists()
        if instance.is_staff != should_be_staff:
            instance.is_staff = should_be_staff
            instance.save(update_fields=["is_staff"])
