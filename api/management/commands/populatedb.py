import os
import random
import shutil
import string

import django
from api.models import Exercise, Muscle, Tag, YoutubeLink
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from lorem_text import lorem

random.seed(0)
# May not be useful anymore
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wapp.settings')
# django.setup()


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

        ex = Exercise(
            name="push ups",
            kind="rep",
            instructions="Remember about hollow body position.",
            owner=user,
        )
        ex.save()
        ex.tags.set([Tag.objects.get(name="easy"), Tag.objects.get(name="popular")])
        ex.tutorials.set([YoutubeLink.objects.all()[10]])
        ex.muscles.set([Muscle.objects.get(name="pec"), Muscle.objects.get(name="tri")])

        ex = Exercise(
            name="pull ups",
            kind="rep",
            instructions="Tense your core during movement.",
            owner=user,
        )
        ex.save()
        ex.tutorials.set([YoutubeLink.objects.all()[20]])
        ex.muscles.set([Muscle.objects.get(name="tra")])

        Exercise(
            name="bulgarian split squat",
            kind="rep",
            instructions=lorem.words(10),
            owner=user,
        ).save()
        Exercise(
            name="romanian single leg deadlift",
            kind="rep",
            instructions=lorem.words(20),
            owner=user,
        ).save()
        Exercise(
            name="pistol squat",
            kind="rep",
            instructions=lorem.words(30),
            owner=user,
            forks_count=12,
        ).save()
        Exercise(
            name="sumo walk",
            kind="rew",
            instructions=lorem.words(100),
            owner=user,
            forks_count=8,
        ).save()
        Exercise(
            name="calf raises",
            kind="rep",
            owner=user,
        ).save()
        Exercise(
            name="squat",
            kind="rew",
            owner=user,
        ).save()
        Exercise(
            name="jogging",
            kind="dis",
            owner=user,
            forks_count=2,
        ).save()
        Exercise(
            name="lunges",
            kind="rep",
            owner=user,
        ).save()
        Exercise(
            name="step ups",
            kind="rep",
            owner=user,
        ).save()
        Exercise(
            name="box jumps",
            kind="rep",
            owner=user,
        ).save()
        Exercise(
            name="bridge",
            kind="tim",
            owner=user,
        ).save()
        Exercise(
            name="dance",
            kind="tim",
            owner=user,
        ).save()
        Exercise(
            name="intervals run",
            kind="tim",
            owner=user,
        ).save()
        Exercise(
            name="hip thrust",
            kind="rew",
            owner=user,
        ).save()

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
