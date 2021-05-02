from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Exercise
from utils.functions import query_params


class ExerciseTest(APITestCase):

    LIST_URLPATTERN_NAME = "exercise-list"

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def setUp(self):
        # Users
        self.u1 = User.objects.create_user("u1", email="u1@mail.com")
        self.u2 = User.objects.create_user("u2", email="u2@mail.com")
        self.u3 = User.objects.create_user("u3", email="u3@mail.com")
        self.authorize(self.u1)

        # Exercises
        Exercise.objects.create(name="Exercise 1", kind="rep", owner=self.u1, forks_count=1000)
        Exercise.objects.create(name="Exercise 2", kind="rep", owner=self.u1)
        Exercise.objects.create(name="Exercise 3", kind="rep", owner=self.u1, forks_count=100)
        Exercise.objects.create(name="Exercise 4", kind="rep", owner=self.u1)
        Exercise.objects.create(name="Exercise 10", kind="tim", owner=self.u2, forks_count=10)
        Exercise.objects.create(name="Exercise 20", kind="tim", owner=self.u2)
        Exercise.objects.create(name="Exercise 30", kind="rew", owner=self.u2, forks_count=1)
        Exercise.objects.create(name="Exercise 40", kind="rew", owner=self.u2)
        Exercise.objects.create(name="Exercise 1", kind="dis", owner=self.u3)
        Exercise.objects.create(name="Exercise 2", kind="dis", owner=self.u3)

    def test_get_exercises(self):
        """Endpoint without any query parameters."""
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

    def test_get_exercises_by_owner_equal(self):
        """Filter exercises owned by a specific user."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"user.eq": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        self.assertTrue(all(exercise["owner"] == 1 for exercise in response.data))

    def test_get_exercises_by_owner_errors(self):
        """Value for user parameter has to be a primary key, not string."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"user.eq": "u1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_exercises_by_owner_not_equal(self):
        """Filter exercises not owned by a specific user."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"user.neq": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        self.assertTrue(all(exercise["owner"] != 1 for exercise in response.data))

    def test_get_exercises_order_by_forks_count(self):
        """Sort returned data by column."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(orderby="forks_count")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [exercise["forks_count"] for exercise in response.data],
            [0, 0, 0, 0, 0, 0, 1, 10, 100, 1000],
        )

    def test_get_exercises_orderby_errors(self):
        """Only subset of columns can be used for sorting."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(orderby="not_existing_column")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_exercises_order_by_forks_count_descending(self):
        """Sort (descending order) returned data by column."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(orderby="-forks_count")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [exercise["forks_count"] for exercise in response.data],
            [1000, 100, 10, 1, 0, 0, 0, 0, 0, 0],
        )

    def test_get_exercises_limit(self):
        """Limit list to only few results."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(limit="3")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_exercises_limit_errors(self):
        """Limit parameter value has to be an integer."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(limit="3.14")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data, {"limit": ["Enter a whole number."]})

    def test_get_exercises_mulitple_parameters(self):
        """Multiple query parameters can be specified during filtering."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(
            **{"user.eq": 1, "orderby": "-forks_count", "limit": 2}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [exercise["name"] for exercise in response.data],
            ["Exercise 1", "Exercise 3"],
        )
