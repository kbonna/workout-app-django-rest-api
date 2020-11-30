from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Exercise, Muscle, Tag, YoutubeLink


class ExerciseTest(APITestCase):

    YT_URL = "https://www.youtube.com/watch?v="
    EXERCISE_SERIALIZER_FIELDS = [
        "pk",
        "name",
        "kind",
        "kind_display",
        "owner",
        "owner_username",
        "can_be_forked",
        "forks_count",
        "tags",
        "muscles",
        "tutorials",
        "instructions",
    ]

    def setUp(self):
        # Users
        user1 = User.objects.create_user("user1")
        user2 = User.objects.create_user("user2")

        refresh = RefreshToken.for_user(user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Exercise-related objects
        tags = [Tag.objects.create(name=name) for name in ("t1", "t2", "t3")]
        tutorials = [YoutubeLink.objects.create(url=self.YT_URL + 11 * c) for c in "abc"]
        muscles = [Muscle.objects.create(name=muscle_tpl[0]) for muscle_tpl in Muscle.MUSCLES]

        # Owner exercises
        exercise1 = Exercise.objects.create(
            name="exercise 1",
            kind="rep",
            instructions="lorem ipsum",
            owner=user1,
        )
        exercise1.tutorials.add(*tutorials)
        exercise1.tags.add(*tags)
        exercise1.muscles.add(*muscles[:3])
        exercise2 = Exercise.objects.create(name="exercise 2", kind="rep", owner=user1)

        self.owner = user1
        self.other_user = user2
        self.owner_exercises = [exercise1, exercise2]
        self.other_user_exercises = [
            Exercise.objects.create(name="exercise 1", kind="rew", owner=user2),
            Exercise.objects.create(name="exercise 2", kind="rew", owner=user2),
            Exercise.objects.create(name="exercise 3", kind="rew", owner=user2),
            Exercise.objects.create(name="exercise 4", kind="rew", owner=user2),
        ]

        self.tags = tags
        self.tutorials = tutorials
        self.muscles = muscles

    def test_get_my_exercises(self):
        """Exercise list endpoint with exercise list for specific user."""
        url = f"{reverse('exercises-list')}?user={self.owner.pk}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.owner.exercise_set.all()))

        exercise_dict = response.data[0]
        exercise_obj = self.owner_exercises[0]

        self.assertEqual(set(exercise_dict.keys()), set(self.EXERCISE_SERIALIZER_FIELDS))
        self.assertEqual(exercise_dict["pk"], exercise_obj.pk)
        self.assertEqual(exercise_dict["name"], exercise_obj.name)
        self.assertEqual(exercise_dict["kind"], exercise_obj.kind)
        self.assertEqual(exercise_dict["kind_display"], exercise_obj.get_kind_display())
        self.assertEqual(exercise_dict["owner"], self.owner.pk)
        self.assertEqual(exercise_dict["owner_username"], self.owner.username)
        self.assertEqual(exercise_dict["can_be_forked"], False)
        self.assertEqual(exercise_dict["forks_count"], 0)
        self.assertEqual(exercise_dict["tags"], [{"name": tag.name} for tag in self.tags])
        self.assertEqual(exercise_dict["muscles"], [{"name": mus.name} for mus in self.muscles[:3]])
        self.assertEqual(exercise_dict["tutorials"], [{"url": tut.url} for tut in self.tutorials])
        self.assertEqual(exercise_dict["instructions"], exercise_obj.instructions)

    def test_get_discover_exercises(self):
        """Exercise list endpoint with discover exercise list (exercises of other users) for
        specific user."""
        url = f"{reverse('exercises-list')}?user={self.owner.pk}&discover=True"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.other_user.exercise_set.all()))

        self.assertFalse(response.data[0]["can_be_forked"])
        self.assertFalse(response.data[1]["can_be_forked"])
        self.assertTrue(response.data[2]["can_be_forked"])
        self.assertTrue(response.data[3]["can_be_forked"])

        for exercise_dict in response.data:
            self.assertEqual(set(exercise_dict.keys()), set(self.EXERCISE_SERIALIZER_FIELDS))
            self.assertEqual(exercise_dict["owner"], self.other_user.pk)
            self.assertEqual(exercise_dict["owner_username"], self.other_user.username)
            self.assertEqual(exercise_dict["forks_count"], 0)
            self.assertListEqual(exercise_dict["tags"], [])
            self.assertListEqual(exercise_dict["muscles"], [])
            self.assertListEqual(exercise_dict["tutorials"], [])
            self.assertEqual(exercise_dict["instructions"], "")

    def test_get_exercise_detail(self):
        pass

    def test_delete_exercise(self):
        """Delete exercise if you are exercise owner."""
        exercise_to_delete = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")
        n_exercises_before = len(Exercise.objects.all())

        url = reverse("exercises-detail", kwargs={"exercise_id": exercise_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(Exercise.objects.all()), n_exercises_before - 1)
        with self.assertRaises(Exercise.DoesNotExist):
            self.owner.exercise_set.get(name="exercise 1")

    def test_delete_exercise_fail(self):
        """Try to delete exercise if you are not an owner."""
        exercise_to_delete = Exercise.objects.get(owner=self.other_user.pk, name="exercise 1")
        n_exercises_before = len(Exercise.objects.all())

        url = reverse("exercises-detail", kwargs={"exercise_id": exercise_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Exercise.objects.all()), n_exercises_before)
        self.assertEqual
        try:
            self.other_user.exercise_set.get(name="exercise 1")
        except Exercise.DoesNotExist:
            self.fail("exercise should not be deleted")

    def test_create_exercise(self):
        """Create new exercise with valid data."""
        json_data = {
            "name": "exercise 3",
            "kind": "rep",
            "instructions": "test description",
            "tags": [{"name": "t1"}, {"name": "t4"}],
            "muscles": [{"name": "tri"}, {"name": "bic"}, {"name": "for"}],
            "tutorials": [{"url": self.YT_URL + 11 * c} for c in "def"],
        }

        url = reverse("exercises-list")
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, 201)

        # Object is created properly
        created_exercise = Exercise.objects.get(owner=self.owner.pk, name=json_data["name"])
        self.assertEqual(created_exercise.name, json_data["name"])
        self.assertEqual(created_exercise.kind, json_data["kind"])
        self.assertEqual(created_exercise.owner, self.owner)
        self.assertEqual(created_exercise.owner.username, self.owner.username)
        self.assertEqual(created_exercise.forks_count, 0)
        self.assertListEqual(
            [{"name": tag.name} for tag in created_exercise.tags.all()], json_data["tags"]
        )
        self.assertListEqual(
            [{"name": mus.name} for mus in created_exercise.muscles.all()], json_data["muscles"]
        )
        self.assertListEqual(
            [{"url": tut.url} for tut in created_exercise.tutorials.all()], json_data["tutorials"]
        )
        self.assertEqual(created_exercise.instructions, json_data["instructions"])

        # Associated objects should also be created
        try:
            for tutorial in json_data["tutorials"]:
                YoutubeLink.objects.get(url=tutorial["url"])
        except YoutubeLink.DoesNotExist:
            self.fail("associated youtube links should be created")
        try:
            for tag in json_data["tags"]:
                Tag.objects.get(name=tag["name"])
        except Tag.DoesNotExist:
            self.fail("associated tags should be created")

    def test_create_exercise_errors(self):
        """Try to create new exercise with only invalid data and expect validation errors."""
        json_data = {
            "name": "",
            "kind": "xxx",
            "tags": [{"name": "x x"}, {"name": "??"}, {"name": ""}],
            "muscles": [{"name": "xx1"}],
            "tutorials": [
                {"url": "https://www.youtube.com/"},
                {"url": ""},
                {"url": "https://www.xoutube.com/watch?v=AAAAAAAAAAA"},
            ],
        }

        url = reverse("exercises-list")
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, 400)
        for field, value in json_data.items():
            self.assertTrue(field in response.data, msg=f"{field} should give validation error")
            if isinstance(value, list):
                self.assertEqual(
                    len(value),
                    len(response.data[field]),
                    msg=f"{field} should give {len(value)} validation errors"
                    + f" but gave {len(response.data[field])}",
                )

    def test_edit_exercise(self):
        json_data = {
            "name": "exercise 1 edited",
            "kind": "tim",
            "tags": [{"name": "t1"}, {"name": "t2"}, {"name": "t3edited"}],
            "muscles": [{"name": muscle.name} for muscle in self.muscles[2:5]],
            "tutorials": [{"url": self.YT_URL + c * 11} for c in "abcdef"],
            "instructions": "lorem ipsum edited",
        }
        exercise_to_edit = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")

        url = reverse("exercises-detail", kwargs={"exercise_id": exercise_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, 200)

        edited_exercise = Exercise.objects.get(pk=exercise_to_edit.pk)
        self.assertEqual(edited_exercise.name, json_data["name"])
        self.assertEqual(edited_exercise.kind, json_data["kind"])
        self.assertEqual(edited_exercise.owner, self.owner)
        self.assertEqual(edited_exercise.owner.username, self.owner.username)
        self.assertEqual(edited_exercise.forks_count, 0)
        self.assertListEqual(
            [{"name": tag.name} for tag in edited_exercise.tags.all()], json_data["tags"]
        )
        self.assertListEqual(
            [{"name": mus.name} for mus in edited_exercise.muscles.all()], json_data["muscles"]
        )
        self.assertListEqual(
            [{"url": tut.url} for tut in edited_exercise.tutorials.all()], json_data["tutorials"]
        )
        self.assertEqual(edited_exercise.instructions, json_data["instructions"])

    def test_edit_exercise_fail(self):
        pass

    def test_edit_exercise_errors(self):
        pass
