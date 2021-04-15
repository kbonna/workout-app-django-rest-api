import datetime
import os
import random
import shutil
import string

from api.data.db_dummy_data import (
    EXERCISES_USER_1,
    EXERCISES_USER_2,
    ROUTINES_USER_1,
    ROUTINES_USER_2,
    WORKOUTS_USER_1,
    WORKOUTS_USER_2,
)
from api.models import (
    Exercise,
    Muscle,
    Routine,
    RoutineUnit,
    Tag,
    Workout,
    WorkoutLogEntry,
    YoutubeLink,
)
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

random.seed(0)


def create_exercise(
    name, kind, owner, instructions="", forks_count=0, tags=[], tutorials=[], muscles=[]
):
    exercise = Exercise(
        name=name,
        kind=kind,
        instructions=instructions,
        owner=owner,
        forks_count=forks_count,
    )
    exercise.save()

    if tags:
        exercise.tags.set(Tag.objects.filter(name__in=tags))
    if tutorials:
        exercise.tutorials.set(YoutubeLink.objects.filter(pk__in=tutorials))
    if muscles:
        exercise.muscles.set(Muscle.objects.filter(name__in=muscles))


def create_routine(name, kind, owner, instructions="", forks_count=0, exercises=[]):
    routine = Routine.objects.create(
        name=name,
        kind=kind,
        instructions=instructions,
        owner=owner,
        forks_count=forks_count,
    )
    for exercise_dict in exercises:
        exercise = Exercise.objects.get(name=exercise_dict.pop("name"))
        RoutineUnit.objects.create(exercise=exercise, routine=routine, **exercise_dict)


def create_workout(date, owner, completed=False, routine=None, exercises=[]):
    """
    date (str or Date object):
        If string is specified it should have YYYY-MM-DD format.
    owner (User instance):
        Workout owner.
    completed (bool):
        Whether the workout was completed or not. Defaults to False.
    routine (str, optional):
        Should be passed as a routine name string.
    exercises (list, optional):
        List of workout log dictionaries. It has to contain "exercise" key with exercise name as
        value and "set_number" key with integer as value.
    """
    if routine:
        routine = Routine.objects.get(owner=owner, name=routine)

    workout = Workout.objects.create(date=date, owner=owner, completed=completed, routine=routine)

    # Add exercises
    for log_entry in exercises:
        exercise_name = log_entry.pop("exercise")
        exercise = Exercise.objects.get(owner=owner, name=exercise_name)
        WorkoutLogEntry.objects.create(workout=workout, exercise=exercise, **log_entry)


class Command(BaseCommand):
    help = "Command populating database"

    def reset_db(self):
        apps = ["accounts", "api"]
        # Remove all migrations and database file
        for app in apps:
            path_migrations = os.path.join(app, "migrations")
            if os.path.exists(path_migrations):
                for file in os.listdir(path_migrations):
                    if file != "__init__.py":
                        try:
                            os.remove(os.path.join(path_migrations, file))
                        except IsADirectoryError:
                            shutil.rmtree(os.path.join(path_migrations, file))

        path_db = "db.sqlite3"
        try:
            os.remove(path_db)
        except FileNotFoundError:
            pass

        # Recreate all tables
        for app in apps:
            os.system(f"./manage.py makemigrations {app}")
            os.system(f"./manage.py migrate {app}")
        os.system(f"./manage.py migrate")

    def create_users(self):
        # Create superuser (pk = 1)
        superuser_command = (
            """from django.contrib.auth.models import User;"""
            + """User.objects.create_superuser('kmb', 'kmb@mail.com', 'test')"""
        )
        os.system(f'./manage.py shell -c "{superuser_command}"')

        # First test user (pk=2)
        u1 = User.objects.create_user(
            "test",
            "test@mail.com",
            password="test",
            first_name="Test",
            last_name="Smith",
        )
        u1.profile.date_of_birth = datetime.date(1990, 1, 10)
        u1.profile.country = "Poland"
        u1.profile.city = "Warsaw"
        u1.profile.gender = "m"
        u1.profile.save()

        # Second test user (pk=3)
        u2 = User.objects.create_user(
            "test2",
            "test2@mail.com",
            password="test",
            first_name="Diana",
            last_name="Davis",
        )
        u2.profile.city = "New York"
        u2.profile.gender = "f"
        u2.profile.save()

    def create_supporting_models(self):
        # Create tags
        tagnames = (
            "easy",
            "medium",
            "hard",
            "core",
            "legs",
            "arms",
            "strength",
            "mobility",
            "endurance",
            "popular",
        )
        for tagname in tagnames:
            Tag(name=tagname).save()

        # Create youtube videos
        CHARSET = string.ascii_letters + string.digits
        for _ in range(100):
            video_code = "".join(random.choices(CHARSET, k=7))
            YoutubeLink(url=f"https://www.youtube.com/watch?v={video_code}").save()

        # Create muscles
        for muscle_abbrev, _ in Muscle.MUSCLES:
            Muscle(name=muscle_abbrev).save()

    def create_exercises(self):
        users = {2: EXERCISES_USER_1, 3: EXERCISES_USER_2}

        for user_pk, user_exercises in users.items():
            user = User.objects.get(pk=user_pk)
            for exercise_dict in user_exercises:
                create_exercise(**exercise_dict, owner=user)

    def create_routines(self):
        users = {2: ROUTINES_USER_1, 3: ROUTINES_USER_2}

        for user_pk, user_routines in users.items():
            user = User.objects.get(pk=user_pk)
            for routine_dict in user_routines:
                create_routine(**routine_dict, owner=user)

    def create_workouts(self):
        users = {2: WORKOUTS_USER_1, 3: WORKOUTS_USER_2}

        for user_pk, user_workouts in users.items():
            user = User.objects.get(pk=user_pk)
            for workout_dict in user_workouts:
                create_workout(**workout_dict, owner=user)

    def handle(self, *args, **options):
        self.reset_db()
        self.create_users()
        self.create_supporting_models()
        self.create_exercises()
        self.create_routines()
        self.create_workouts()
