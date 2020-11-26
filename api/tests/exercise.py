from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Exercise, Muscle, Tag, YoutubeLink
from ..serializers.exercise import ExerciseSerializer


# import pytest
# @pytest.fixture
# def api_client():
#     user = User.objects.create_user('user1')
#     client = APIClient()
#     refresh = RefreshToken.for_user(user)
#     client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
#     return client


class ReadExerciseTest(APITestCase):
    def setUp(self):
        # Users
        user1 = User.objects.create_user("user1")
        user2 = User.objects.create_user("user2")

        refresh = RefreshToken.for_user(user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Exercise-related objects
        url = "https://www.youtube.com/watch?v="
        tags = [Tag.objects.create(name=name) for name in ("t1", "t2", "t3")]
        tutorials = [YoutubeLink.objects.create(url=url + c) for c in "abc"]
        muscles = [Muscle.objects.create(name=name) for name in Muscle.MUSCLES]

        # Exercises
        exercise1 = Exercise.objects.create(
            name="exercise 1",
            kind="rep",
            instructions="lorem ipsum",
            owner=user1,
        )
        exercise1.tutorials.add(*tutorials)
        exercise1.tags.add(*tags)
        exercise1.muscles.add(*muscles[:3])
        exercise2 = Exercise.objects.create(name="exercise 2", kind="rew", owner=user2)

        self.exercises = [exercise1, exercise2]
        self.users = [user1, user2]
        self.tags = tags
        self.tutorials = tutorials
        self.muscles = muscles

    def test_get_my_exercises(self):
        url = reverse("exercises-list")
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(1, 1)

    def test_get_discover(self):
        pass
