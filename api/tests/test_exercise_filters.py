from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Exercise, Muscle, Tag


def query_params(**d):
    return "?" + "&".join(f"{k}={v}" for k, v in d.items())


class ExerciseTest(APITestCase):

    LIST_URLPATTERN_NAME = "exercise-list"

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def setUp(self):
        # Users
        self.u1 = User.objects.create_user("u1", email="u1@mail.com")
        self.u2 = User.objects.create_user("u2", email="u2@mail.com")
        self.authorize(self.u1)

        # Exercise-related objects
        self.tags = {name: Tag.objects.create(name=name) for name in ("tag1", "tag2", "tag3")}
        self.muscles = {muscle: Muscle.objects.create(name=muscle) for muscle, _ in Muscle.MUSCLES}

        # Exercises
        Exercise.objects.create(name="Exercise 1", kind="rep", owner=self.u1, forks_count=1000)
        Exercise.objects.create(name="Exercise 2", kind="rep", owner=self.u1, forks_count=1)
        Exercise.objects.create(name="Exercise 3", kind="rep", owner=self.u1, forks_count=100)
        Exercise.objects.create(name="Exercise 4", kind="rep", owner=self.u1, forks_count=10)
        Exercise.objects.create(name="Exercise 1", kind="rep", owner=self.u2)
        Exercise.objects.create(name="Exercise 2", kind="rep", owner=self.u2)
        Exercise.objects.create(name="Exercise 3", kind="rep", owner=self.u2)
        Exercise.objects.create(name="Exercise 4", kind="rep", owner=self.u2)

    def test_get_exercises(self):
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(
            **{"orderby": "-forks_count", "limit": 3.1415}
        )
        response = self.client.get(url)
        print(url, "\n\n", len(response.data), [e["forks_count"] for e in response.data])