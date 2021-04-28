import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from api.models import Exercise, Routine, Workout, WorkoutLogEntry
from api.serializers.workout import WorkoutLogEntrySerializer, WorkoutSerializer


class RequestMock:
    def __init__(self, user):
        self.user = user


class WorkoutSerializersTestCase(TestCase):
    def setUp(self):
        # User owner related records
        self.owner = User.objects.create(username="owner", email="owner@mail.com")
        self.owner_exercises = {
            "rep": Exercise.objects.create(name="Exercise rep", kind="rep", owner=self.owner),
            "rew": Exercise.objects.create(name="Exercise rew", kind="rew", owner=self.owner),
            "tim": Exercise.objects.create(name="Exercise tim", kind="tim", owner=self.owner),
            "dis": Exercise.objects.create(name="Exercise dis", kind="dis", owner=self.owner),
        }
        self.owner_routine = Routine.objects.create(name="Routine", kind="sta", owner=self.owner)
        self.owner_routine.exercises.add(self.owner_exercises["rep"], through_defaults={"sets": 3})
        self.owner_workout = Workout.objects.create(owner=self.owner, date="2020-01-01")
        self.log_entry = WorkoutLogEntry.objects.create(
            workout=self.owner_workout, exercise=self.owner_exercises["rep"], set_number=1, reps=10
        )
        # User other_user related records
        self.other_user = User.objects.create(username="other_user", email="other_user@mail.com")
        self.other_user_exercises = {
            "rep": Exercise.objects.create(name="Exercise rep", kind="rep", owner=self.other_user),
        }
        self.other_user_routine = Routine.objects.create(
            name="Routine", kind="sta", owner=self.other_user
        )
        # Additional context required for deserialization
        self.context = {"request": RequestMock(user=self.owner)}

    def test_workout_log_entry_serialization(self):
        """Database objects are correctly translated into dictionaries."""
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["rep"].pk,
            "exercise_name": self.owner_exercises["rep"].name,
            "set_number": 1,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        ser = WorkoutLogEntrySerializer(self.log_entry)
        self.assertEqual(ser.data, data)

    def test_workout_log_entry_deserialization_rep(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["rep"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_rew(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["rew"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": 50.5,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_tim(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["tim"].pk,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": 3600,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_dis(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["dis"].pk,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": None,
            "distance": 1000,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_no_data(self):
        """Regardless of exercise kind at least one unit should be specified."""
        for exercise_kind in ["rep", "rew", "tim", "dis"]:
            data = {
                "workout": 1,
                "exercise": self.owner_exercises[exercise_kind].pk,
                "set_number": 2,
                "reps": None,
                "weight": None,
                "time": None,
                "distance": None,
            }
            deser = WorkoutLogEntrySerializer(
                data=data, context={"request": RequestMock(user=self.owner)}
            )
            self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_rep(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["rep"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": 5,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_rew(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["rew"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": 50.5,
            "time": 5,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_tim(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["tim"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": 5,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_dis(self):
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["dis"].pk,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": 5,
            "distance": 1000,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_set_number_not_unique(self):
        """Only single workout log entry can have same workout, exercise and set number."""
        data = {
            "workout": 1,
            "exercise": self.owner_exercises["rep"].pk,
            "set_number": 1,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(
            data=data, context={"request": RequestMock(user=self.owner)}
        )
        self.assertFalse(deser.is_valid())

    def test_workout_serialization(self):
        ser = WorkoutSerializer(self.owner_workout)
        data = ser.data
        self.assertEqual(data["date"], "2020-01-01")
        self.assertEqual(data["completed"], False)
        self.assertEqual(data["routine"], None)

        log_entries = data["log_entries"]
        self.assertEqual(len(log_entries), 1)
        self.assertDictEqual(
            log_entries[0],
            {
                "workout": 1,
                "exercise": self.owner_exercises["rep"].pk,
                "exercise_name": self.owner_exercises["rep"].name,
                "set_number": 1,
                "reps": 10,
                "weight": None,
                "time": None,
                "distance": None,
            },
        )

    def test_workout_deserialization(self):
        """Workout object can be sucesfully created from JSON data."""
        data = {
            "date": "2020-01-01",
            "completed": True,
            "log_entries": [
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 1, "reps": 10},
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 2, "reps": 10},
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 3, "reps": 10},
            ],
        }
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        self.assertDictEqual(deser.errors, {})

    def test_workout_deserialization_errors_not_owned_routine(self):
        """You cannot add workout with not your routine."""
        data = {"date": "2020-01-01", "completed": True, "routine": self.other_user_routine.pk}
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        self.assertDictEqual(deser.errors, {"routine": ["This is not your routine."]})

    def test_workout_deserialization_errors_not_owned_exercise(self):
        """You cannot add workout with an exercise that is not owned by you."""
        data = {
            "date": "2020-01-01",
            "completed": True,
            "log_entries": [
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 1, "reps": 10},
                {"exercise": self.other_user_exercises["rep"].pk, "set_number": 1, "reps": 10},
            ],
        }
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        self.assertDictEqual(
            deser.errors, {"log_entries": [{}, {"exercise": ["This is not your exercise."]}]}
        )

    def test_workout_deserialization_errors_routine_integrity(self):
        """You cannot add workout with exercises not conforming to routine scheme."""
        data = {
            "date": "2020-01-01",
            "routine": self.owner_routine.pk,
            "log_entries": [
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 1, "reps": 10},
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 2, "reps": 10},
                {"exercise": self.owner_exercises["tim"].pk, "set_number": 3, "time": 60},
            ],
        }
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        self.assertDictEqual(
            deser.errors,
            {
                "integrity": [
                    "Exercise Exercise rep: set 3 is missing.",
                    "Exercise Exercise tim: set 3 should not be specified for this routine.",
                ]
            },
        )

    def test_workout_deserialization_errors_set_number_integrity(self):
        """You cannot add workout with exercises with missing sets."""
        data = {
            "date": "2020-01-01",
            "log_entries": [
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 1, "reps": 10},
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 3, "reps": 10},
                {"exercise": self.owner_exercises["tim"].pk, "set_number": 5, "time": 60},
                {"exercise": self.owner_exercises["dis"].pk, "set_number": 2, "distance": 1000},
            ],
        }
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        self.assertDictEqual(
            deser.errors,
            {
                "integrity": [
                    "Exercise Exercise dis: set 1 is missing.",
                    "Exercise Exercise rep: set 2 is missing.",
                    "Exercise Exercise tim: set 1 is missing.",
                    "Exercise Exercise tim: set 2 is missing.",
                    "Exercise Exercise tim: set 3 is missing.",
                    "Exercise Exercise tim: set 4 is missing.",
                ]
            },
        )

    def test_workout_create_default_values(self):
        """Workout can be created without any data, then default values are set. Default day is
        today's date, owner is derived from the context, completed defaults to False, routine
        defaults to None."""
        data = {}
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        new_workout = deser.save()
        self.assertEqual(new_workout.date, datetime.datetime.now().date())
        self.assertEqual(new_workout.owner, self.owner)
        self.assertEqual(new_workout.completed, False)
        self.assertEqual(new_workout.routine, None)
        self.assertEqual(new_workout.log_entries.count(), 0)

    def test_workout_create_non_default_values(self):
        """Workout can be created without any data, then default values are set. Default day is
        today's date, owner is derived from the context, completed defaults to False, routine
        defaults to None."""
        data = {
            "date": "2021-01-01",
            "completed": True,
            "routine": None,
            "log_entries": [],
        }
        deser = WorkoutSerializer(data=data, context=self.context)
        deser.is_valid()
        new_workout = deser.save()
        self.assertEqual(new_workout.date, datetime.date(2021, 1, 1))
        self.assertEqual(new_workout.owner, self.owner)
        self.assertEqual(new_workout.completed, True)
        self.assertEqual(new_workout.routine, None)
        self.assertEqual(new_workout.log_entries.count(), 0)

    def test_workout_update(self):
        """Workout can be updated with new values."""
        data = {
            "date": "2021-01-01",
            "routine": self.owner_routine.pk,
            "log_entries": [
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 1, "reps": 10},
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 2, "reps": 20},
                {"exercise": self.owner_exercises["rep"].pk, "set_number": 3, "reps": 30},
            ],
        }
        deser = WorkoutSerializer(self.owner_workout, data=data, context=self.context)
        deser.is_valid()
        deser.save()

        workout = self.owner_workout
        workout.refresh_from_db()
        self.assertEqual(workout.date, datetime.date(2021, 1, 1))
        self.assertEqual(workout.routine, self.owner_routine)
        self.assertEqual(workout.log_entries.count(), 3)
        # Previous log entry should be removed
        with self.assertRaises(WorkoutLogEntry.DoesNotExist):
            self.log_entry.refresh_from_db()
