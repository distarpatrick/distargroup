from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Import inside the function to avoid circular imports between apps
        from BUS_SYSTEM.models import Profile
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    # Only save if the profile exists
    if hasattr(instance, 'profile'):
        instance.profile.save()