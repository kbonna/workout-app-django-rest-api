from datetime import datetime

from api.models import Exercise, Routine, Workout
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from utils.decorators import authorize_fn
from utils.functions import query_params

data = {
    "user1": {
        "exercises": [
            {"name": "Exercise 1", "kind": "rep"},
            {"name": "Exercise 2", "kind": "rep"},
            {"name": "Exercise 3", "kind": "rep"},
        ],
        "routines": [
            {"name": "Routine 1", "kind": "sta"},
        ],
        "workouts": [
            {
                "date": "2020-01-01",
                "completed": True,
                "routine": "Routine 1",
                "exercises": ["Exercise 1", "Exercise 2"],
            },
            {
                "date": "2020-01-02",
                "completed": True,
                "routine": "Routine 1",
                "exercises": ["Exercise 2", "Exercise 3"],
            },
            {
                "date": "2020-01-03",
                "completed": True,
                "routine": "Routine 1",
                "exercises": ["Exercise 1", "Exercise 3"],
            },
            {
                "date": "2020-01-04",
                "completed": True,
            },
            {
                "date": "2020-01-05",
                "completed": True,
            },
            {
                "date": "2020-01-06",
                "completed": False,
            },
            {
                "date": "2020-01-07",
                "completed": False,
            },
            {
                "date": "2020-01-08",
                "completed": False,
            },
            {
                "date": "2020-01-09",
                "completed": False,
            },
            {
                "date": "2020-01-10",
                "completed": False,
            },
        ],
    },
    "user2": {
        "exercises": [
            {"name": "Exercise 1", "kind": "rep"},
        ],
        "routines": [
            {"name": "Routine 1", "kind": "sta"},
        ],
        "workouts": [
            {
                "date": "2020-01-01",
                "completed": True,
                "routine": "Routine 1",
                "exercises": ["Exercise 1"],
            },
            {
                "date": "2020-01-02",
                "completed": True,
            },
            {
                "date": "2020-01-03",
                "completed": True,
            },
            {
                "date": "2020-01-04",
                "completed": True,
            },
            {
                "date": "2020-01-05",
                "completed": True,
            },
            {
                "date": "2020-01-06",
                "completed": True,
            },
            {
                "date": "2020-01-07",
                "completed": True,
            },
            {
                "date": "2020-01-08",
                "completed": True,
            },
            {
                "date": "2020-01-09",
                "completed": True,
            },
            {
                "date": "2020-01-10",
                "completed": True,
            },
        ],
    },
}

workouts_user1 = data["user1"]["workouts"]
workouts_user2 = data["user2"]["workouts"]
workouts_all = workouts_user1 + workouts_user2


def str2date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


@authorize_fn
class WorkoutFiltersTest(APITestCase):

    LIST_URLPATTERN_NAME = "workout-list"

    def setUp(self):
        # Users
        for user in data:
            User.objects.create_user(user, email=f"{user}@mail.com")
        self.authorize(User.objects.get(pk=1))

        for user, entities in data.items():
            user_obj = User.objects.get(username=user)

            for exercise in entities["exercises"]:
                Exercise.objects.create(**exercise, owner=user_obj)
            for routine in entities["routines"]:
                Routine.objects.create(**routine, owner=user_obj)
            for workout in entities["workouts"]:
                routine_name = workout.get("routine", None)
                exercise_names = workout.get("exercises", None)
                routine_obj = (
                    Routine.objects.get(name=routine_name, owner=user_obj) if routine_name else None
                )
                exercise_objs = (
                    [
                        Exercise.objects.get(name=exercise_name, owner=user_obj)
                        for exercise_name in exercise_names
                    ]
                    if exercise_names
                    else None
                )
                w = Workout.objects.create(
                    date=workout["date"],
                    completed=workout["completed"],
                    routine=routine_obj,
                    owner=user_obj,
                )
                if exercise_objs:
                    w.exercises.add(*exercise_objs, through_defaults={"set_number": 1, "reps": 1})

    def test_no_filters(self):
        """Get all workouts."""
        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(workouts_all))

    def test_limit(self):
        """Limit search with first n results."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(limit=5)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_user_eq(self):
        """Filter workouts owned by a specific user."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"user.eq": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(workouts_user1))
        self.assertTrue(all(workout["owner"] == 1 for workout in response.data))

    def test_user_neq(self):
        """Filter workouts not owned by a specific user."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"user.neq": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(workouts_user2))
        self.assertTrue(all(workout["owner"] != 1 for workout in response.data))

    def test_completed(self):
        """Filter only completed workouts."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(completed=True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(w["completed"] for w in workouts_all))
        self.assertTrue(all(workout["completed"] for workout in response.data))

    def test_not_completed(self):
        """Filter only planned workouts."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(completed=False)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(not w["completed"] for w in workouts_all))
        self.assertTrue(all(not workout["completed"] for workout in response.data))

    def test_date_eq(self):
        """Filter only workouts for certain date."""
        date = str2date("2020-01-01")
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"date.eq": "2020-01-01"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(str2date(w["date"]) == date for w in workouts_all))
        self.assertTrue(all(workout["date"] == "2020-01-01" for workout in response.data))

    def test_date_gt(self):
        """Filter only workouts for after certain date."""
        date = str2date("2020-01-05")
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"date.gt": "2020-01-05"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(str2date(w["date"]) > date for w in workouts_all))
        self.assertTrue(all(str2date(workout["date"]) > date for workout in response.data))

    def test_date_gte(self):
        """Filter only workout for or after certain date."""
        date = str2date("2020-01-05")
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"date.gte": "2020-01-05"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(str2date(w["date"]) >= date for w in workouts_all))
        self.assertTrue(all(str2date(workout["date"]) >= date for workout in response.data))

    def test_date_lt(self):
        date = str2date("2020-01-05")
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"date.lt": "2020-01-05"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(str2date(w["date"]) < date for w in workouts_all))
        self.assertTrue(all(str2date(workout["date"]) < date for workout in response.data))

    def test_date_lte(self):
        date = str2date("2020-01-05")
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(**{"date.lte": "2020-01-05"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), sum(str2date(w["date"]) <= date for w in workouts_all))
        self.assertTrue(all(str2date(workout["date"]) <= date for workout in response.data))

    def test_filter_by_exercise(self):
        """Filter workout containing specific exercise."""
        e = Exercise.objects.get(name="Exercise 1", owner=1)
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(exercise=e.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            len(response.data), sum("Exercise 1" in w.get("exercises", []) for w in workouts_user1)
        )
        for exercise in response.data:
            self.assertTrue(
                any(log_entry["exercise"] == e.pk for log_entry in exercise["log_entries"])
            )

    def test_filter_by_routine(self):
        """Filter workout for specific routine."""
        r = Routine.objects.get(name="Routine 1", owner=1)
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(routine=r.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            len(response.data), sum(w.get("routine") == "Routine 1" for w in workouts_user1)
        )
        for exercise in response.data:
            self.assertTrue(exercise["routine"] == r.pk)

    def test_orderby_date(self):
        """Order workouts by date."""
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(orderby="date")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        date_list = [str2date(workout["date"]) for workout in response.data]
        self.assertEqual(date_list, sorted(date_list))

        # Reversed order
        url = reverse(self.LIST_URLPATTERN_NAME) + query_params(orderby="-date")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        date_list = [str2date(workout["date"]) for workout in response.data]
        self.assertEqual(date_list, sorted(date_list, reverse=True))
