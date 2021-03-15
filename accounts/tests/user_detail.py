import os
import tempfile
import datetime
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

from accounts.models import UserProfile
from .utils import (
    create_image_file,
    USER_DETAIL_URLPATTERN_NAME,
    PASSWORD_RESET_URLPATTERN_NAME,
    EMAIL_RESET_URLPATTERN_NAME,
    PROFILE_PICTURE_URLPATTERN_NAME,
)

# Override MEDIA_ROOT directory just for tests
# This way real /media/ folder would not be littered by test files
TEMP_MEDIA_ROOT = tempfile.TemporaryDirectory(prefix="MEDIA_test")
settings.MEDIA_ROOT = TEMP_MEDIA_ROOT.name
os.mkdir(os.path.join(settings.MEDIA_ROOT, "profile_pictures"))


class UserDetailTest(APITestCase):
    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def setUp(self):
        # First user
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@mail.com",
            password="test",
            first_name="Test",
            last_name="Smith",
        )
        self.owner.profile.gender = "m"
        self.owner.profile.date_of_birth = datetime.date(1990, 1, 20)
        self.owner.profile.save()
        # Second user
        self.other_user = User.objects.create_user(
            username="other_user", email="other_user@mail.com", password="test"
        )

    def test_get_your_own_profile_data(self):
        """User is able to get own profile data including email."""
        self.authorize(self.owner)
        url = reverse(USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        profile = data["profile"]

        self.assertEqual(data["username"], "owner")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "Smith")
        self.assertEqual(data["email"], "owner@mail.com")
        self.assertNotIn("password", data)
        self.assertEqual(
            profile["profile_picture"], settings.MEDIA_URL + "profile_pictures/default.png"
        )
        self.assertEqual(profile["gender"], "m")
        self.assertEqual(profile["gender_display"], "male")
        self.assertEqual(profile["date_of_birth"], "20.01.1990")

    def test_get_other_user_profile_data(self):
        """Any authenticated user is able to get data of other user but without email field."""
        self.authorize(self.owner)
        url = reverse(USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        profile = data["profile"]

        # These fields should not be in the response
        self.assertNotIn("password", data)
        self.assertNotIn("email", data)

        self.assertEqual(data["username"], "other_user")
        self.assertEqual(data["first_name"], "")
        self.assertEqual(data["last_name"], "")
        self.assertEqual(
            profile["profile_picture"], settings.MEDIA_URL + "profile_pictures/default.png"
        )
        self.assertEqual(profile["gender"], "")
        self.assertEqual(profile["gender_display"], "")
        self.assertEqual(profile["date_of_birth"], None)

    def test_delete_account(self):
        """User can delete their own account. Associated profile should be removed after user is
        removed. Profile picture should be removed from the filesystem."""
        self.authorize(self.owner)

        # Set profile picture and manually move to MEDIA_ROOT directory
        img_file = create_image_file()
        img_path = os.path.join(
            settings.MEDIA_ROOT, "profile_pictures", os.path.basename(img_file.name)
        )
        shutil.copy(img_file.name, img_path)
        self.owner.profile.profile_picture = img_path
        self.owner.profile.save()

        profile_picture_path = self.owner.profile.profile_picture.path
        self.assertTrue(os.path.exists(profile_picture_path))

        user_pk = self.owner.pk
        url = reverse(USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": user_pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that User object is gone
        with self.assertRaises(User.DoesNotExist):
            self.owner.refresh_from_db()

        # Associated profile should also be removed
        with self.assertRaises(UserProfile.DoesNotExist):
            UserProfile.objects.get(user=user_pk)

        # Associated profile picture should be removed from the filesystem
        self.assertFalse(os.path.exists(profile_picture_path))

    def test_delete_account_with_default_profile_picture(self):
        """Deleting user with default profile picture should leave default profile pic intact."""
        self.authorize(self.owner)

        # Set default profile picture and manually move to MEDIA_ROOT directory
        img_file = create_image_file()
        img_path = os.path.join(settings.MEDIA_ROOT, "profile_pictures/default.png")
        shutil.copy(img_file.name, img_path)
        self.owner.profile.profile_picture = img_path
        self.owner.profile.save()

        profile_picture_path = self.owner.profile.profile_picture.path
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))

        user_pk = self.owner.pk
        url = reverse(USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": user_pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Default profile picture should not be removed from filesystem
        self.assertTrue(os.path.exists(profile_picture_path))

    def test_password_reset(self):
        """Password should be correctly updated."""
        self.authorize(self.owner)

        url = reverse(PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.put(url, {"password": "new_password"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertTrue(check_password("new_password", self.owner.password))

    def test_password_reset_errors(self):
        """Errors should be returned if password is too short of password field is missing."""
        self.authorize(self.owner)

        url = reverse(PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        # Too short password
        response = self.client.put(url, {"password": "123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

        # Incorrect field name
        response = self.client.put(url, {"pass": "123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_reset_for_other_user(self):
        """Changing other user password is forbidden."""
        self.authorize(self.owner)

        url = reverse(PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        # Too short password
        response = self.client.put(url, {"password": "new_password"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_password_reset_wrong_http_methods(self):
        """Password reset endpoint only accepts PUT requests."""
        self.authorize(self.owner)

        url = reverse(PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "post", "delete"):
            response = self.client.__getattribute__(method)(
                url, {"password": "new_password"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_email_reset(self):
        """User can change his email."""
        self.authorize(self.owner)

        url = reverse(EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"email": "new@email.com"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertEqual(self.owner.email, "new@email.com")

    def test_email_reset_errors(self):
        """Invalid email should not be set."""
        self.authorize(self.owner)

        url = reverse(EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"email": "invalidemail-com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "Enter a valid email address.")

        response = self.client.put(url, {"imail": "new@email.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "This field is required.")

    def test_email_reset_for_other_user(self):
        """User cannot reset email of other user."""
        self.authorize(self.owner)

        url = reverse(EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        response = self.client.put(url, {"email": "new@email.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_reset_wrong_http_methods(self):
        """Email reset endpoint only accepts PUT requests."""
        self.authorize(self.owner)

        url = reverse(EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "post", "delete"):
            response = self.client.__getattribute__(method)(
                url, {"email": "new@email.com"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_data(self):
        """User can update his own profile data."""
        self.authorize(self.owner)
        json_data = {
            "pk": self.owner.pk + 1,
            "username": self.owner.username + "_edited",
            "first_name": "Editedfirstname",
            "last_name": "Editedlastname",
            "profile": {
                "country": "Poland",
                "city": "Warsaw",
                "gender": "f",
                "date_of_birth": "10.10.1992",
            },
        }

        url = reverse(USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()

        # ensure that username can't be edited
        self.assertEqual(self.owner.username, "owner")

        # rest of the fields are edited correctly
        self.assertEqual(self.owner.first_name, "Editedfirstname")
        self.assertEqual(self.owner.last_name, "Editedlastname")
        self.assertEqual(self.owner.profile.country, "Poland")
        self.assertEqual(self.owner.profile.city, "Warsaw")
        self.assertEqual(self.owner.profile.gender, "f")
        self.assertEqual(self.owner.profile.date_of_birth, datetime.date(1992, 10, 10))

    def test_update_user_profile_data_errors(self):
        """Profile data should be validated."""
        self.authorize(self.owner)

        # prepare data to contain too long strings, profile picture should be image not str
        json_data = {
            "pk": self.owner.pk + 1,
            "username": self.owner.username + "_edited",
            "first_name": "a" * 151,
            "last_name": "b" * 151,
            "profile": {
                "country": "c" * 101,
                "city": "d" * 101,
                "gender": "x",
                "date_of_birth": "1992 X 2",
            },
        }

        url = reverse(USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # errors should be raised for three keys
        # note that pk and username is read_only so should not be validated
        errors = response.data
        self.assertIn("first_name", errors)
        self.assertIn("last_name", errors)
        self.assertIn("profile", errors)
        self.assertEqual(len(errors), 3)

        # errors should also be raised for nested object
        nested_errors = errors["profile"]
        self.assertIn("country", nested_errors)
        self.assertIn("city", nested_errors)
        self.assertIn("gender", nested_errors)
        self.assertIn("date_of_birth", nested_errors)
        self.assertEqual(len(nested_errors), 4)

    def test_update_profile_picture(self):
        """User can update their profile picture."""
        self.authorize(self.owner)

        img_file = create_image_file()

        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"profile_picture": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Response yields correct url
        self.assertTrue(
            response.data["profile_picture"].startswith(settings.MEDIA_URL + "profile_pictures")
        )

        # Profile pic was updated
        self.owner.refresh_from_db()
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))

    def test_delete_profile_picture(self):
        """User can delete their profile picture. Default profile picture should be restored."""
        self.authorize(self.owner)
        profile = self.owner.profile

        img_file = create_image_file()
        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        # Upload profile picture first
        self.client.put(url, {"profile_picture": img_file}, format="multipart")
        profile.refresh_from_db()
        img_path = profile.profile_picture.path

        # Delete profile picture
        self.client.delete(url)
        profile.refresh_from_db()

        # Profile pic was removed, default picture was set and not removed from storage
        self.assertFalse(os.path.exists(img_path))
        self.assertEqual(profile.profile_picture.name, UserProfile().profile_picture.name)
        self.assertTrue(os.path.exists, profile.profile_picture.path)

    def test_delete_default_profile_picture(self):
        """Requesting DELETE on profile picture endpoint should take no effect if user has default
        profile picture."""
        self.authorize(self.owner)
        profile = self.owner.profile

        # Delete profile picture
        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        self.client.delete(url)
        profile.refresh_from_db()

        # User still has default profile picture, file was not removed
        self.assertEqual(profile.profile_picture.name, UserProfile().profile_picture.name)
        self.assertTrue(os.path.exists, profile.profile_picture.path)

    def test_update_profile_picture_old_picture_removed(self):
        """After updating profile picture, old file should be removed."""
        self.authorize(self.owner)

        # Create two images
        old_img_file = create_image_file()
        new_img_file = create_image_file()

        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        # Upload first profile picture
        response = self.client.put(url, {"profile_picture": old_img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        old_img_path = self.owner.profile.profile_picture.path

        # Upload second profile picture
        response = self.client.put(url, {"profile_picture": new_img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))
        self.assertFalse(os.path.exists(old_img_path))

    def test_update_profile_picture_of_other_user(self):
        """User cannot update profile picture of other user."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        response = self.client.put(url, {"profile_picture": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_profile_picture_errors(self):
        """Incorrect name of the field (image instead of profile_picture) should be validated by
        serializer."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"image": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_picture", response.data)

    def test_update_profile_picture_wrong_http_methods(self):
        """Profile picture user endpoint should only accept PUT request."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "post"):
            response = self.client.__getattribute__(method)(
                url, {"profile_picture": img_file}, format="multipart"
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
