from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Workout, Exercise, Routine
import datetime


class WorkoutViewsTestCase(APITestCase):

    LIST_URLPATTERN_NAME = "workout-list"
    DETAIL_URLPATTERN_NAME = "workout-detail"

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def setUp(self):
        # Users
        self.owner = User.objects.create_user("owner", email="owner@email.com")
        self.other_user = User.objects.create_user("other_user", email="other_user@email.com")
        self.authorize(self.owner)
        # Exercises & Routines
        self.owner_exercise_rep = Exercise.objects.create(name="Rep", kind="rep", owner=self.owner)
        self.owner_exercise_rew = Exercise.objects.create(name="Rew", kind="rew", owner=self.owner)
        self.owner_routine = Routine.objects.create(name="Routine", kind="sta", owner=self.owner)
        self.owner_routine.exercises.add(self.owner_exercise_rep, through_defaults={"sets": 3})
        self.other_user_exercise_rep = Exercise.objects.create(
            name="Rep", kind="rep", owner=self.other_user
        )
        # Workouts
        self.owner_workout_1 = Workout.objects.create(
            owner=self.owner, date=datetime.date(2021, 1, 1)
        )
        self.owner_workout_2 = Workout.objects.create(
            owner=self.owner, date=datetime.date(2021, 2, 1)
        )
        self.other_user_workout = Workout.objects.create(
            owner=self.other_user, date=datetime.date(2021, 1, 1)
        )
        self.other_user_workout.exercises.add(
            self.other_user_exercise_rep, through_defaults={"set_number": 1, "reps": 10}
        )

    def test_create_workout(self):
        """Create new workout with valid data."""
        json_data = {
            "date": "2020-01-01",
            "completed": True,
        }

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_workout_detail(self):
        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"workout_id": self.owner_workout_1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data,
            {
                "owner": self.owner.pk,
                "owner_username": self.owner.username,
                "date": "2021-01-01",
                "completed": False,
                "routine": None,
                "log_entries": [],
            },
        )

    def test_get_workout_detail_other_user(self):
        """Any user can get workout detail for all workouts."""
        url = reverse(
            self.DETAIL_URLPATTERN_NAME, kwargs={"workout_id": self.other_user_workout.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_workout_list(self):
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
