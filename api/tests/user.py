from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import override_settings
import tempfile
import os
from django.contrib.auth.hashers import check_password


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
    PROFILE_PICTURE_URLPATTERN_NAME = "profile-picture"
    PASSWORD_RESET_URLPATTERN_NAME = "password-reset"
    EMAIL_RESET_URLPATTERN_NAME = "email-reset"

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def setUp(self):
        self.owner = User.objects.create_user(
            "owner", "owner@mail.com", "test", first_name="Test", last_name="Smith"
        )
        self.other_user = User.objects.create_user("other_user", "other_user@mail.com", "test")

    def test_create_new_user(self):
        json_data = {"username": "new_user", "password": "password"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "new_user")

    def test_create_new_user_too_short_password(self):
        """Password for newly created user should be at least 4 characters long."""
        json_data = {"username": "new_user", "password": "123"}

        url = reverse(self.USER_LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_profile_data(self):
        self.authorize(self.owner)
        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["username"], "owner")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "Smith")
        self.assertEqual(data["email"], "owner@mail.com")
        self.assertEqual(data["username"], "owner")
        self.assertNotIn("password", data)

        profile = data["profile"]
        self.assertEqual(profile["profile_picture"], settings.MEDIA_URL + "default.png")

    def test_get_user_profile_data_unauthorized(self):
        self.authorize(self.owner)
        url = reverse(self.USER_DETAIL_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_profile_data(self):
        self.authorize(self.owner)
        json_data = {
            "pk": self.owner.pk + 1,
            "username": self.owner.username + "_edited",
            "first_name": "Editedfirstname",
            "last_name": "Editedlastname",
            "profile": {"country": "Poland", "city": "Warsaw"},
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

    def test_update_user_profile_data_errors(self):
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
        self.assertEqual(len(nested_errors), 2)

    # This way real /media/ folder would not be littered by test files
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    def test_update_profile_picture(self):
        self.authorize(self.owner)

        img_file = create_image_file()
        img_fname = os.path.basename(img_file.name)

        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"profile_picture": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Profile pic was updated
        self.owner.refresh_from_db()
        self.assertEqual(os.path.basename(self.owner.profile.profile_picture.name), img_fname)

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    def test_update_profile_picture_of_other_user(self):
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        response = self.client.put(url, {"profile_picture": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    def test_update_profile_picture_errors(self):
        """Incorrect name of the field (image instead of profile_picture) should be validated by
        serializer."""
        self.authorize(self.owner)

        img_file = create_image_file()
        url = reverse(self.PROFILE_PICTURE_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        response = self.client.put(url, {"image": img_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_picture", response.data)

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
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
        response = self.client.post(url, {"password": "new_password"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner.refresh_from_db()
        self.assertTrue(check_password("new_password", self.owner.password))

    def test_password_reset_errors(self):
        """Errors should be returned if password is too short of password field is missing."""
        self.authorize(self.owner)

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        # Too short password
        response = self.client.post(url, {"password": "123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

        # Incorrect field name
        response = self.client.post(url, {"pass": "123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_reset_for_other_user(self):
        """Changing other user password is forbidden."""
        self.authorize(self.owner)

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.other_user.pk})

        # Too short password
        response = self.client.post(url, {"password": "new_password"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_password_reset_wrong_http_methods(self):
        """Password reset endpoint only accepts POST requests."""
        self.authorize(self.owner)

        url = reverse(self.PASSWORD_RESET_URLPATTERN_NAME, kwargs={"user_pk": self.owner.pk})

        for method in ("get", "put", "delete"):
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
        # TODO: implement this
        pass
