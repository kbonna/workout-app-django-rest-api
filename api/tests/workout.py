from api.models import Workout, WorkoutLogEntry, Exercise
from django.contrib.auth.models import User
from django.test import TestCase
from api.serializers.workout import WorkoutLogEntrySerializer, WorkoutSerializer


class WorkoutSerializersTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create()
        self.exercises = {
            "rep": Exercise.objects.create(name="Exercise rep", kind="rep", owner=self.owner),
            "rew": Exercise.objects.create(name="Exercise rew", kind="rew", owner=self.owner),
            "tim": Exercise.objects.create(name="Exercise tim", kind="tim", owner=self.owner),
            "dis": Exercise.objects.create(name="Exercise dis", kind="dis", owner=self.owner),
        }
        self.workout = Workout.objects.create(owner=self.owner, date="2020-01-01")
        self.log_entry = WorkoutLogEntry.objects.create(
            workout=self.workout, exercise=self.exercises["rep"], set_number=1, reps=10
        )
        # Additional context required for deserialization
        self.context = {"requesting_user_pk": self.owner.pk}

    def test_workout_log_entry_serialization(self):
        """Database objects are correctly translated into dictionaries."""
        data = {
            "workout": 1,
            "exercise": self.exercises["rep"].pk,
            "exercise_name": self.exercises["rep"].name,
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
            "exercise": self.exercises["rep"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_rew(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["rew"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": 50.5,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_tim(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["tim"].pk,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": 3600,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_dis(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["dis"].pk,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": None,
            "distance": 1000,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertTrue(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_no_data(self):
        """Regardless of exercise kind at least one unit should be specified."""
        for exercise_kind in ["rep", "rew", "tim", "dis"]:
            data = {
                "workout": 1,
                "exercise": self.exercises[exercise_kind].pk,
                "set_number": 2,
                "reps": None,
                "weight": None,
                "time": None,
                "distance": None,
            }
            deser = WorkoutLogEntrySerializer(
                data=data, context={"requesting_user_pk": self.owner.pk}
            )
            self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_rep(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["rep"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": 5,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_rew(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["rew"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": 50.5,
            "time": 5,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_tim(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["tim"].pk,
            "set_number": 2,
            "reps": 10,
            "weight": None,
            "time": 5,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_dis(self):
        data = {
            "workout": 1,
            "exercise": self.exercises["dis"].pk,
            "set_number": 2,
            "reps": None,
            "weight": None,
            "time": 5,
            "distance": 1000,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertFalse(deser.is_valid())

    def test_workout_log_entry_deserialization_errors_set_number_not_unique(self):
        """Only single workout log entry can have same workout, exercise and set number."""
        data = {
            "workout": 1,
            "exercise": self.exercises["rep"].pk,
            "set_number": 1,
            "reps": 10,
            "weight": None,
            "time": None,
            "distance": None,
        }
        deser = WorkoutLogEntrySerializer(data=data, context={"requesting_user_pk": self.owner.pk})
        self.assertFalse(deser.is_valid())

    def test_workout_serialization(self):
        ser = WorkoutSerializer(self.workout)
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
                "exercise": self.exercises["rep"].pk,
                "exercise_name": self.exercises["rep"].name,
                "set_number": 1,
                "reps": 10,
                "weight": None,
                "time": None,
                "distance": None,
            },
        )

    def test_workout_deserialization(self):
        data = {
            "date": "2020-01-01",
            "completed": True,
            "log_entries": [
                {"exercise": self.exercises["rep"].pk, "set_number": 1, "reps": 10},
                {"exercise": self.exercises["rep"].pk, "set_number": 2, "reps": 10},
                {"exercise": self.exercises["rep"].pk, "set_number": 3, "reps": 10},
            ],
        }
        deser = WorkoutSerializer(data=data, context=self.context)
        self.assertTrue(deser.is_valid())