from api.models import Workout, WorkoutLogEntry, Exercise
from django.contrib.auth.models import User
from django.test import TestCase


class WorkoutTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", email="owner@email.com")

    def test_reps_validation(self):
        pass
