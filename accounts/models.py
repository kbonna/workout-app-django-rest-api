import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models

# from utils.functions import hash_upload_to

# Set user email field to be unique
User._meta.get_field("email")._unique = True
User._meta.get_field("email").blank = False
User._meta.get_field("email").null = False


def user_profile_picture_path(instance, filename):
    """Creates user profile picture path as zero padded user pk correct extension."""
    extension = os.path.splitext(filename)[1]
    return f"profile_pictures/{instance.user_id:07}{extension}"


class UserProfile(models.Model):
    """Additional user-related informations."""

    GENDERS = [("m", "male"), ("f", "female")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    city = models.CharField(blank=True, max_length=100)
    country = models.CharField(blank=True, max_length=100)
    gender = models.CharField(blank=True, max_length=1, choices=GENDERS)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        storage=FileSystemStorage(base_url=settings.MEDIA_URL),
        default="profile_pictures/default.png",
    )

    def __str__(self):
        return f"UserProfile(user={self.user})"

    def delete(self, using=None, keep_parents=False):
        """Delete profile picture file when user is deleted."""
        if os.path.basename(self.profile_picture.name) != "default.png":
            self.profile_picture.storage.delete(self.profile_picture.name)
        super().delete()
