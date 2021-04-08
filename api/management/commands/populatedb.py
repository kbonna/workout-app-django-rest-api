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
from lorem_text import lorem

random.seed(0)


def create_exercise(
    name, kind, owner, instructions="", forks_count=0, tags=[], tutorials=[], muscles=[]
):
    exercise = Exercise(
        name=name, kind=kind, instructions=instructions, owner=owner, forks_count=forks_count
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
        name=name, kind=kind, instructions=instructions, owner=owner, forks_count=forks_count
    )
    for exercise_dict in exercises:
        exercise = Exercise.objects.get(name=exercise_dict.pop("name"))
        RoutineUnit.objects.create(exercise=exercise, routine=routine, **exercise_dict)


class Command(BaseCommand):
    help = "Command populating database"

    def reset_db(self):
        # Remove all migrations and database file
        path_migrations = "api/migrations"
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
        os.system("./manage.py makemigrations")
        os.system("./manage.py migrate")

    def create_users(self):
        # Create superuser (pk = 1)
        superuser_command = (
            """from django.contrib.auth.models import User;"""
            + """User.objects.create_superuser('kmb', 'kmb@mail.com', 'test')"""
        )
        os.system(f'./manage.py shell -c "{superuser_command}"')

        # First test user (pk=2)
        u1 = User.objects.create_user(
            "test", "test@mail.com", password="test", first_name="Test", last_name="Smith"
        )
        u1.profile.date_of_birth = datetime.date(1990, 1, 10)
        u1.profile.country = "Poland"
        u1.profile.city = "Warsaw"
        u1.profile.gender = "m"
        u1.profile.save()

        # Second test user (pk=3)
        u2 = User.objects.create_user(
            "test2", "test2@mail.com", password="test", first_name="Diana", last_name="Davis"
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
        for i in range(100):
            video_code = "".join(random.choices(CHARSET, k=7))
            YoutubeLink(url=f"https://www.youtube.com/watch?v={video_code}").save()

        # Create muscles
        for muscle_abbrev, muscle_name in Muscle.MUSCLES:
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
        ...

    def handle(self, *args, **options):
        self.reset_db()
        self.create_users()
        self.create_supporting_models()
        self.create_exercises()
        self.create_routines()
