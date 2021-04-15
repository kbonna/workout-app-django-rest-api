from api.models import Workout, WorkoutLogEntry, Exercise
from django.contrib.auth.models import User
from django.test import TestCase
from api.serializers.workout import WorkoutLogEntrySerializer


class WorkoutSerializersTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create()
        self.exercise = Exercise.objects.create(name="Exercise", kind="rep", owner=self.user)
        self.workout = Workout.objects.create(owner=self.user)
        self.log_entry = WorkoutLogEntry.objects.create(
            workout=self.workout, exercise=self.exercise, set_number=1, reps=10
        )

    def test_workout_log_entry_serialization(self):
        data = {
            "workout": 1,
            "exercise": 1,
            "exercise_name": "Exercise",
            "set_number": 1,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        ser = WorkoutLogEntrySerializer(self.log_entry)
        self.assertEqual(ser.data, data)

    def test_workout_log_entry_deserialization(self):
        data = {
            "workout": 1,
            "exercise": 1,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.user.pk})
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_errors(self):
        data = {
            "workout": 1,
            "exercise": 1,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.user.pk})
        self.assertFalse(deser.is_valid())
        print(deser.errors)
