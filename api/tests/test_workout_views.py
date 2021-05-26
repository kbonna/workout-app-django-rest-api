import datetime

from api.models import Exercise, Routine, Workout
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from utils.decorators import authorize_fn


@authorize_fn
class WorkoutViewsTestCase(APITestCase):

    LIST_URLPATTERN_NAME = "workout-list"
    DETAIL_URLPATTERN_NAME = "workout-detail"

    def setUp(self):
        # Users
        self.owner = User.objects.create_user("owner", email="owner@email.com")
        self.other_user = User.objects.create_user("other_user", email="other_user@email.com")
        self.authorize(self.owner)
        # Exercises & Routines
        self.owner_exercise_rep = Exercise.objects.create(name="Rep", kind="rep", owner=self.owner)
        self.owner_exercise_rew = Exercise.objects.create(name="Rew", kind="rew", owner=self.owner)
        self.owner_exercise_tim = Exercise.objects.create(name="Tim", kind="tim", owner=self.owner)
        self.owner_exercise_dis = Exercise.objects.create(name="Dis", kind="dis", owner=self.owner)
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

    def test_create_workout_from_routine(self):
        json_data = {
            "date": "2020-01-01",
            "completed": False,
            "routine": self.owner_routine.pk,
            "log_entries": [
                {"exercise": self.owner_exercise_rep.pk, "set_number": 1, "reps": 10},
                {"exercise": self.owner_exercise_rep.pk, "set_number": 2, "reps": 10},
                {"exercise": self.owner_exercise_rep.pk, "set_number": 3, "reps": 10},
            ],
        }
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_workout_from_routine_incorrect_exercise(self):
        json_data = {
            "date": "2020-01-01",
            "completed": False,
            "routine": self.owner_routine.pk,
            "log_entries": [
                {"exercise": self.owner_exercise_rew.pk, "set_number": 1, "reps": 10, "weight": 1},
                {"exercise": self.owner_exercise_rew.pk, "set_number": 2, "reps": 10, "weight": 1},
                {"exercise": self.owner_exercise_rew.pk, "set_number": 3, "reps": 10, "weight": 1},
            ],
        }
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_workout_from_routine_missing_set(self):
        json_data = {
            "date": "2020-01-01",
            "completed": False,
            "routine": self.owner_routine.pk,
            "log_entries": [
                {"exercise": self.owner_exercise_rep.pk, "set_number": 2, "reps": 10},
                {"exercise": self.owner_exercise_rep.pk, "set_number": 3, "reps": 10},
            ],
        }
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"integrity": ["Exercise Rep: set 1 is missing."]})

    def test_create_workout_manual(self):
        json_data = {
            "date": "2020-01-01",
            "log_entries": [
                {"exercise": self.owner_exercise_rep.pk, "set_number": 1, "reps": 20},
                {"exercise": self.owner_exercise_rep.pk, "set_number": 2, "reps": 20},
                {"exercise": self.owner_exercise_tim.pk, "set_number": 1, "time": 3600},
                {"exercise": self.owner_exercise_tim.pk, "set_number": 2, "time": 3600},
                {"exercise": self.owner_exercise_dis.pk, "set_number": 1, "distance": 10000},
                {"exercise": self.owner_exercise_dis.pk, "set_number": 2, "distance": 10000},
                {
                    "exercise": self.owner_exercise_rew.pk,
                    "set_number": 1,
                    "reps": 10,
                    "weight": 7.5,
                },
                {
                    "exercise": self.owner_exercise_rew.pk,
                    "set_number": 2,
                    "reps": 10,
                    "weight": 7.5,
                },
            ],
        }
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_workout_manual_incorrect_units(self):
        json_data = {
            "date": "2020-01-01",
            "log_entries": [
                {"exercise": self.owner_exercise_rep.pk, "set_number": 1, "weight": 50},
                {"exercise": self.owner_exercise_tim.pk, "set_number": 1, "distance": 10000},
                {"exercise": self.owner_exercise_dis.pk, "set_number": 1, "time": 3600},
                {"exercise": self.owner_exercise_rew.pk, "set_number": 1, "reps": 10},
            ],
        }
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.data,
            {
                "log_entries": [
                    {"reps": ["For this exercise reps should be specified."]},
                    {"time": ["For this exercise time should be specified."]},
                    {"distance": ["For this exercise distance should be specified."]},
                    {"weight": ["For this exercise weight should be specified."]},
                ]
            },
        )

    def test_create_workout_manual_missing_sets(self):
        json_data = {
            "date": "2020-01-01",
            "log_entries": [
                {"exercise": self.owner_exercise_rep.pk, "set_number": 1, "reps": 50},
                {"exercise": self.owner_exercise_rep.pk, "set_number": 3, "reps": 50},
                {"exercise": self.owner_exercise_rep.pk, "set_number": 5, "reps": 50},
            ],
        }
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.data,
            {"integrity": ["Exercise Rep: set 2 is missing.", "Exercise Rep: set 4 is missing."]},
        )

    def test_get_workout_detail(self):
        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"workout_pk": self.owner_workout_1.pk})
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
            self.DETAIL_URLPATTERN_NAME, kwargs={"workout_pk": self.other_user_workout.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_workout_list(self):
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_workout(self):
        """Remove your own workout."""
        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"workout_pk": self.owner_workout_1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Workout.objects.filter(owner=self.owner).count(), 1)

    def test_delete_workout_of_other_user(self):
        """Try to remove other user's workout."""
        url = reverse(
            self.DETAIL_URLPATTERN_NAME, kwargs={"workout_pk": self.other_user_workout.pk}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_workout_change_date(self):
        """Perform simple update on workout object changing date."""
        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"workout_pk": self.owner_workout_1.pk})
        json_data = {
            "date": "2021-01-15",
            "completed": True,
        }
        response = self.client.put(url, data=json_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["date"], "2021-01-15")
        self.assertEqual(response.data["completed"], True)