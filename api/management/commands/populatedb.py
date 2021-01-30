import os
import random
import shutil
import string

from api.data.db_dummy_data import EXERCISES_USER_1
from api.models import Exercise, Muscle, Routine, Tag, YoutubeLink
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


class Command(BaseCommand):
    help = "Command printing hello"

    def handle(self, *args, **options):
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

        # Create superuser
        superuser_command = (
            """from django.contrib.auth.models import User;"""
            + """User.objects.create_superuser('kmb', 'kmb@mail.com', 'test')"""
        )
        os.system(f'./manage.py shell -c "{superuser_command}"')

        # Create users
        User.objects.create_user("test", "test@mail.com", password="test")
        User.objects.create_user("test2", "test2@mail.com", password="test")

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

        # Create exercises for user with pk: 2
        user = User.objects.get(pk=2)
        for exercise_dict in EXERCISES_USER_1:
            create_exercise(**exercise_dict, owner=user)

        # Create routines for user with pk: 2
        r = Routine.objects.create(
            name="Leg workout A",
            kind="sta",
            instructions="This is the first leg workout.",
            owner=user,
        )
        leg_exercises = Exercise.objects.filter(
            name__in=[
                "bulgarian split squat",
                "romanian single leg deadlift",
                "pistol squat",
                "lunges",
                "box jumps",
            ]
        )
        r.exercises.set(leg_exercises, through_defaults={"sets": 3})

        r = Routine.objects.create(
            name="Leg workout B",
            instructions="My favourite leg workout.",
            kind="cir",
            owner=user,
        )
        leg_exercises = Exercise.objects.filter(
            name__in=("bridge", "hip thrust", "step ups", "jogging")
        )
        instructions = [lorem.words(n) for n in (5, 10, 20, 40)]
        for exercise, instruction in zip(leg_exercises, instructions):
            r.exercises.add(exercise, through_defaults={"sets": 4, "instructions": instruction})

        Routine.objects.create(name="Push A", kind="sta", owner=user, forks_count=11)
        Routine.objects.create(name="Push B", kind="sta", owner=user)
        Routine.objects.create(name="Push C", kind="sta", owner=user)
        Routine.objects.create(name="Push D", kind="sta", owner=user)
        Routine.objects.create(name="Pull A", kind="sta", owner=user, forks_count=3)
        Routine.objects.create(name="Pull B", kind="sta", owner=user, forks_count=2)
        Routine.objects.create(name="Pull C", kind="sta", owner=user)
        Routine.objects.create(name="Pull D", kind="sta", owner=user)
        Routine.objects.create(name="FBW A", kind="sta", owner=user, forks_count=1)
        Routine.objects.create(name="FBW B", kind="sta", owner=user)
        Routine.objects.create(name="FBW C", kind="sta", owner=user)
        Routine.objects.create(name="FBW D", kind="sta", owner=user)
        for i in range(30):
            Routine.objects.create(name=f"Routine {i}", kind="sta", owner=user)

        # Create exercises for user with pk: 3
        user = User.objects.get(pk=3)

        Exercise(name="bench press", kind="rew", owner=user).save()
        Exercise(name="planche", kind="tim", owner=user).save()
        Exercise(name="diamond push ups", kind="rep", owner=user).save()
        Exercise(name="pike push ups", kind="rep", owner=user).save()
        Exercise(name="archer push ups", kind="rep", owner=user).save()
        Exercise(name="sphinx push ups", kind="rep", owner=user).save()
        Exercise(name="hindu push ups", kind="rep", owner=user).save()
        Exercise(name="one arm push ups", kind="rep", owner=user).save()
        Exercise(name="push ups", kind="rep", owner=user).save()
        Exercise(name="pull ups", kind="rep", owner=user).save()

        ex = Exercise(
            name="plank",
            kind="tim",
            instructions="Arms should be straight.",
            owner=user,
        )
        ex.save()
        ex.tutorials.set([YoutubeLink.objects.all()[60], YoutubeLink.objects.all()[61]])
        ex.muscles.set([Muscle.objects.get(name="abs")])

        # Create routines for user with pk:
        Routine.objects.create(name="Chest, triceps and shoulders", kind="sta", owner=user)
        Routine.objects.create(name="Arms", kind="cir", owner=user)
        Routine.objects.create(name="Upper body (bodyweight)", kind="sta", owner=user)
        Routine.objects.create(name="Upper body (weights)", kind="sta", owner=user)
        Routine.objects.create(name="Powerlifting", kind="sta", owner=user, forks_count=3)
        Routine.objects.create(name="Begginers", kind="sta", owner=user, forks_count=2)
        Routine.objects.create(name="Advanced abs", kind="sta", owner=user)
        Routine.objects.create(name="Quads, hamstrings", kind="sta", owner=user)
        Routine.objects.create(name="Endurance", kind="sta", owner=user, forks_count=1)
        Routine.objects.create(name="Full body", kind="cir", owner=user)
        Routine.objects.create(name="Strenght", kind="sta", owner=user)
        Routine.objects.create(name="Hypertrophy", kind="sta", owner=user)
