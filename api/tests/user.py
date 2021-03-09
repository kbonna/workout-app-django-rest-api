import os
import tempfile
import shutil
import datetime

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from api.models import UserProfile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

# Override MEDIA_ROOT directory just for tests
# This way real /media/ folder would not be littered by test files
TEMP_MEDIA_ROOT = tempfile.TemporaryDirectory(prefix="testMEDIA")
settings.MEDIA_ROOT = TEMP_MEDIA_ROOT.name


def create_image_file(suffix=".png"):
    """Generate blank image file and return file object."""
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    img_file = tempfile.NamedTemporaryFile(suffix=suffix)
    img.save(img_file)
    img_file.seek(0)
    return img_file


class UserTest(APITestCase):

    USER_LIST_URLPATTERN_NAME = "user-list"
    USER_DETAIL_URLPATTERN_NAME = "user-detail"
    PROFILE_PICTURE_URLPATTERN_NAME = "user-picture-reset"
    PASSWORD_RESET_URLPATTERN_NAME = "user-password-reset"
    EMAIL_RESET_URLPATTERN_NAME = "user-email-reset"

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def setUp(self):
        # First user
        self.owner = User.objects.create_user(
            "owner", "owner@mail.com", "test", first_name="Test", last_name="Smith"
        )
        self.owner.profile.gender = "m"
        self.owner.profile.date_of_birth = datetime.date(1990, 1, 20)
        self.owner.profile.save()
        # Second user
        self.other_user = User.objects.create_user("other_user", "other_user@mail.com", "test")

    def test_create_new_user(self):
        json_data = {"username": "new_user", "password": "password", "email": "user@mail.com"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "new_user")

    def test_create_new_user_too_short_password(self):
        """Password for newly created user should be at least 4 characters long."""
        json_data = {"username": "new_user", "password": "123", "email": "user@mail.com"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_new_user_wrong_email(self):
        """Email for newly created user should have correct format."""
        json_data = {"username": "new_user", "password": "123", "email": "myemail"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_new_user_unique_username(self):
        """Newly created users should have unique username."""
        json_data = {"username": "owner", "password": "password", "email": "new_email@mail.com"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertEqual(len(response.data), 1)

    def test_create_new_user_unique_email(self):
        """Newly created users should have unique email."""
        json_data = {"username": "new_user", "password": "password", "email": "owner@mail.com"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(len(response.data), 1)

    def test_get_user_profile_data(self):
        """User is able to get own profile data including email."""
        self.authorize(self.owner)
        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["username"], "owner")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "Smith")
        self.assertEqual(data["email"], "owner@mail.com")
        self.assertNotIn("password", data)

        profile = data["profile"]
        self.assertEqual(
            profile["profile_picture"], settings.MEDIA_URL + "profile_pictures/default.png"
        )
        self.assertEqual(profile["gender"], "m")
        self.assertEqual(profile["gender_display"], "male")
        self.assertEqual(profile["date_of_birth"], "20.01.1990")

    def test_get_user_profile_data_other_user(self):
        """Any authenticated user is able to get data of other user but without email field."""
        self.authorize(self.owner)
        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["username"], "other_user")
        self.assertEqual(data["first_name"], "")
        self.assertEqual(data["last_name"], "")

        # These fields should not be in the response
        self.assertNotIn("password", data)
        self.assertNotIn("email", data)

        profile = data["profile"]
        self.assertEqual(
            profile["profile_picture"], settings.MEDIA_URL + "profile_pictures/default.png"
        )
        self.assertEqual(profile["gender"], "")
        self.assertEqual(profile["gender_display"], "")
        self.assertEqual(profile["date_of_birth"], None)

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

        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
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
                "profile_picture": "picture",
                "gender": "x",
                "date_of_birth": "1992 X 2",
            },
        }

        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
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

    def test_delete_user(self):
        """User can delete their own account."""
        self.authorize(self.owner)

        # Set profile picture and manually move to MEDIA_ROOT directory
        img_file = create_image_file()
        img_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(img_file.name))
        shutil.copy(img_file.name, img_path)

        self.owner.profile.profile_picture = img_path
        self.owner.profile.save()

        profile_picture_path = self.owner.profile.profile_picture.path
        self.assertTrue(os.path.exists(profile_picture_path))

        user_pk = self.owner.pk
        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": user_pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that User object is gone
        with self.assertRaises(User.DoesNotExist):
            self.owner.refresh_from_db()

        # Associated profile should also be removed
        with self.assertRaises(UserProfile.DoesNotExist):
            UserProfile.objects.get(user=user_pk)

        # Associated profile picture should be removed from filesystem
        self.assertFalse(os.path.exists(profile_picture_path))

    def test_delete_user_with_default_profile_picture(self):
        """Deleting user with default profile picture should leave default profile pic intact."""
        self.authorize(self.owner)

        # Set profile picture and manually move to MEDIA_ROOT directory
        img_file = create_image_file()
        img_path = os.path.join(settings.MEDIA_ROOT, "default.png")
        shutil.copy(img_file.name, img_path)

        self.owner.profile.profile_picture = img_path
        self.owner.profile.save()
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))

        user_pk = self.owner.pk
        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": user_pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Default profile picture should not be removed from filesystem
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))

    def test_update_profile_picture(self):
        """User can update their profile picture."""
        self.authorize(self.owner)

        img_file = create_image_file()
        img_fname = os.path.basename(img_file.name)

        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"profile_picture": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Profile pic was updated
        self.owner.refresh_from_db()
        self.assertEqual(os.path.basename(self.owner.profile.profile_picture.name), img_fname)
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))

    def test_update_profile_picture_old_picture_removed(self):
        """After updating profile picture, old file should be removed."""
        self.authorize(self.owner)

        # Create two images
        old_img_file = create_image_file()
        new_img_file = create_image_file()

        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        # Upload first profile picture
        response = self.client.put(url, {"profile_picture": old_img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        old_img_path = self.owner.profile.profile_picture.path

        # Upload second profile picture
        response = self.client.put(url, {"profile_picture": new_img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertEqual(
            os.path.basename(self.owner.profile.profile_picture.name),
            os.path.basename(new_img_file.name),
        )
        self.assertTrue(os.path.exists(self.owner.profile.profile_picture.path))
        self.assertFalse(os.path.exists(old_img_path))

    def test_update_profile_picture_of_other_user(self):
        """User cannot update profile picture of other user."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        response = self.client.put(url, {"profile_picture": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_profile_picture_errors(self):
        """Incorrect name of the field (image instead of profile_picture) should be validated by
        serializer."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"image": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_picture", response.data)

    def test_update_profile_picture_wrong_http_methods(self):
        """Profile picture user endpoint should only accept PUT request."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "post", "delete"):
            response = self.client.__getattribute__(method)(
                url, {"profile_picture": img_file}, format="multipart"
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_password_reset(self):
        """Password should be correctly updated."""
        self.authorize(self.owner)

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.put(url, {"password": "new_password"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertTrue(check_password("new_password", self.owner.password))

    def test_password_reset_errors(self):
        """Errors should be returned if password is too short of password field is missing."""
        self.authorize(self.owner)

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

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

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        # Too short password
        response = self.client.put(url, {"password": "new_password"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_password_reset_wrong_http_methods(self):
        """Password reset endpoint only accepts PUT requests."""
        self.authorize(self.owner)

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "post", "delete"):
            response = self.client.__getattribute__(method)(
                url, {"password": "new_password"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_email_reset(self):
        """User changes his email."""
        self.authorize(self.owner)

        url = reverse(self.EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"email": "new@email.com"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertEqual(self.owner.email, "new@email.com")

    def test_email_reset_errors(self):
        """Invalid email should not be set."""
        self.authorize(self.owner)

        url = reverse(self.EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"email": "invalidemail-com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "Enter a valid email address.")

        response = self.client.put(url, {"imail": "new@email.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "This field is required.")

    def test_email_reset_for_other_user(self):
        """User cannot reset email of other user."""
        self.authorize(self.owner)

        url = reverse(self.EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        response = self.client.put(url, {"email": "new@email.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_reset_wrong_http_methods(self):
        """Email reset endpoint only accepts PUT requests."""
        self.authorize(self.owner)

        url = reverse(self.EMAIL_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "post", "delete"):
            response = self.client.__getattribute__(method)(
                url, {"email": "new@email.com"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
