from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .utils import USER_LIST_URLPATTERN_NAME
from django.contrib.auth.models import User

# URL common for all tests
url = reverse(USER_LIST_URLPATTERN_NAME)


class UserListTest(APITestCase):
    def setUp(self):
        User.objects.create_user(
            username="owner",
            email="owner@mail.com",
            password="test",
        )

    def test_create_new_user(self):
        """Anyone can create new user."""
        json_data = {"username": "new_user", "password": "password", "email": "user@mail.com"}

        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "new_user")

    def test_create_new_user_too_short_password(self):
        """Password for newly created user should be at least 4 characters long."""
        json_data = {"username": "new_user", "password": "123", "email": "user@mail.com"}

        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_new_user_incorrect_email(self):
        """Email for newly created user should have correct format."""
        json_data = {"username": "new_user", "password": "123", "email": "myemail"}

        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_new_user_not_unique_username(self):
        """Newly created users should have unique username."""
        json_data = {"username": "owner", "password": "password", "email": "new_email@mail.com"}

        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertEqual(len(response.data), 1)

    def test_create_new_user_not_unique_email(self):
        """Newly created users should have unique email."""
        json_data = {"username": "new_user", "password": "password", "email": "owner@mail.com"}

        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(len(response.data), 1)
