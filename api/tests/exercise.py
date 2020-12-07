from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Exercise, Muscle, Tag, YoutubeLink


class ExerciseTest(APITestCase):

    LIST_URLPATTERN_NAME = "exercise-list"
    DETAIL_URLPATTERN_NAME = "exercise-detail"
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

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def assertCorrectExercise(self, exercise_dict, exercise_obj, user_request):
        """Custom assertion for this APITestCase checking whether exercise dict retrieved from API
        response match underlying database entry.

        Args:
            exercise_dict (dict):
                Deserialized API response representing single exercise.
            exercise_obj (api.models.Exercise):
                Exercise model instance.
            user_request (User):
                User model instance corresponding to the user making request.
        """
        self.assertEqual(set(exercise_dict.keys()), set(self.EXERCISE_SERIALIZER_FIELDS))

        self.assertEqual(exercise_dict["pk"], exercise_obj.pk)
        self.assertEqual(exercise_dict["name"], exercise_obj.name)
        self.assertEqual(exercise_dict["kind"], exercise_obj.kind)
        self.assertEqual(exercise_dict["instructions"], exercise_obj.instructions)
        self.assertEqual(exercise_dict["forks_count"], exercise_obj.forks_count)

        self.assertEqual(exercise_dict["kind_display"], exercise_obj.get_kind_display())
        self.assertEqual(exercise_dict["owner"], exercise_obj.owner.pk)
        self.assertEqual(exercise_dict["owner_username"], exercise_obj.owner.username)
        self.assertEqual(exercise_dict["can_be_forked"], exercise_obj.can_be_forked(user_request))

        tags = [{"name": tag.name} for tag in exercise_obj.tags.all()]
        muscles = [{"name": muscle.name} for muscle in exercise_obj.muscles.all()]
        tutorials = [{"url": tutorial.url} for tutorial in exercise_obj.tutorials.all()]

        self.assertEqual(exercise_dict["tags"], tags)
        self.assertEqual(exercise_dict["muscles"], muscles)
        self.assertEqual(exercise_dict["tutorials"], tutorials)

    def setUp(self):
        # Users
        owner = User.objects.create_user("owner")
        self.authorize(owner)
        other_user = User.objects.create_user("other_user")

        # Exercise-related objects
        tags = [Tag.objects.create(name=name) for name in ("t1", "t2", "t3")]
        tutorials = [YoutubeLink.objects.create(url=self.YT_URL + 11 * c) for c in "abc"]
        muscles = [Muscle.objects.create(name=muscle_tpl[0]) for muscle_tpl in Muscle.MUSCLES]

        # Owner exercises
        exercise1 = Exercise.objects.create(
            name="exercise 1",
            kind="rep",
            instructions="lorem ipsum",
            owner=owner,
        )
        exercise1.tutorials.add(*tutorials)
        exercise1.tags.add(*tags)
        exercise1.muscles.add(*muscles[:3])
        exercise2 = Exercise.objects.create(name="exercise 2", kind="rep", owner=owner)
        owner_exercises = [exercise1, exercise2]

        # Other user exercises
        other_user_exercises = [
            Exercise.objects.create(name="exercise 1", kind="rew", owner=other_user),
            Exercise.objects.create(name="exercise 2", kind="rew", owner=other_user),
            Exercise.objects.create(name="exercise 3", kind="rew", owner=other_user),
            Exercise.objects.create(name="exercise 4", kind="rew", owner=other_user),
        ]
        exercise_to_fork = Exercise.objects.create(
            name="fork me",
            kind="tim",
            instructions="fork fork fork",
            owner=other_user,
            forks_count=10,
        )
        exercise_to_fork.tutorials.add(*tutorials)
        exercise_to_fork.tags.add(*tags)
        exercise_to_fork.muscles.add(*muscles[-3:])
        other_user_exercises.append(exercise_to_fork)

        # Store db objects
        self.owner = owner
        self.other_user = other_user
        self.owner_exercises = owner_exercises
        self.other_user_exercises = other_user_exercises
        self.tags = tags
        self.tutorials = tutorials
        self.muscles = muscles

    def test_get_my_exercises(self):
        """Get list of exercises owned by you."""
        url = f"{reverse(self.LIST_URLPATTERN_NAME)}?user={self.owner.pk}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.owner_exercises))

        for exercise_dict, exercise_obj in zip(response.data, self.owner_exercises):
            self.assertCorrectExercise(exercise_dict, exercise_obj, self.owner)

        # Ensure your own exercises cannot be forked
        for exercise_dict in response.data:
            self.assertFalse(exercise_dict["can_be_forked"])

    def test_get_discover_exercises(self):
        """Get list of exercises owned by other users."""
        url = f"{reverse(self.LIST_URLPATTERN_NAME)}?user={self.owner.pk}&discover=True"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.other_user_exercises))

        for exercise_dict, exercise_obj in zip(response.data, self.other_user_exercises):
            self.assertCorrectExercise(exercise_dict, exercise_obj, self.owner)

        # Ensure other user exercises that have same name as one of your exercises cannot be forked
        self.assertFalse(response.data[0]["can_be_forked"])
        self.assertFalse(response.data[1]["can_be_forked"])
        self.assertTrue(response.data[2]["can_be_forked"])
        self.assertTrue(response.data[3]["can_be_forked"])
        self.assertTrue(response.data[4]["can_be_forked"])

    def test_get_exercise_detail(self):
        """Get detail of single exercise."""
        exercise = self.owner_exercises[0]

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, dict))
        self.assertCorrectExercise(response.data, exercise, self.owner)

    def test_delete_exercise(self):
        """Delete exercise when you are an exercise owner."""
        exercise_to_delete = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")
        n_exercises_before = len(Exercise.objects.all())

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(Exercise.objects.all()), n_exercises_before - 1)
        with self.assertRaises(Exercise.DoesNotExist):
            self.owner.exercise_set.get(name="exercise 1")

    def test_delete_exercise_fail(self):
        """Try to delete exercise if you are not an owner."""
        exercise_to_delete = Exercise.objects.get(owner=self.other_user.pk, name="exercise 1")
        n_exercises_before = len(Exercise.objects.all())

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Exercise.objects.all()), n_exercises_before)
        try:
            self.other_user.exercise_set.get(name="exercise 1")
        except Exercise.DoesNotExist:
            self.fail("exercise that you don't own should not be deleted")

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

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Object is created properly
        created_exercise = Exercise.objects.get(owner=self.owner.pk, name=json_data["name"])
        self.assertEqual(created_exercise.name, json_data["name"])
        self.assertEqual(created_exercise.kind, json_data["kind"])
        self.assertEqual(created_exercise.owner, self.owner)
        self.assertEqual(created_exercise.owner.username, self.owner.username)
        self.assertEqual(created_exercise.forks_count, 0)
        self.assertEqual(created_exercise.instructions, json_data["instructions"])

        tags = [{"name": tag.name} for tag in created_exercise.tags.all()]
        muscles = [{"name": muscle.name} for muscle in created_exercise.muscles.all()]
        tutorials = [{"url": tutorial.url} for tutorial in created_exercise.tutorials.all()]

        self.assertListEqual(tags, json_data["tags"])
        self.assertListEqual(muscles, json_data["muscles"])
        self.assertListEqual(tutorials, json_data["tutorials"])

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

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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
        """Edit exercise with valid data."""
        json_data = {
            "name": "exercise 1 edited",
            "kind": "tim",
            "tags": [{"name": "t1"}, {"name": "t2"}, {"name": "t3edited"}],
            "muscles": [{"name": muscle.name} for muscle in self.muscles[2:5]],
            "tutorials": [{"url": self.YT_URL + c * 11} for c in "abcdef"],
            "instructions": "lorem ipsum edited",
        }
        exercise_to_edit = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        exercise_to_edit.refresh_from_db()
        self.assertEqual(exercise_to_edit.name, json_data["name"])
        self.assertEqual(exercise_to_edit.kind, json_data["kind"])
        self.assertEqual(exercise_to_edit.owner, self.owner)
        self.assertEqual(exercise_to_edit.owner.username, self.owner.username)
        self.assertEqual(exercise_to_edit.forks_count, 0)
        self.assertEqual(exercise_to_edit.instructions, json_data["instructions"])

        tags = [{"name": tag.name} for tag in exercise_to_edit.tags.all()]
        muscles = [{"name": muscle.name} for muscle in exercise_to_edit.muscles.all()]
        tutorials = [{"url": tutorial.url} for tutorial in exercise_to_edit.tutorials.all()]

        self.assertListEqual(tags, json_data["tags"])
        self.assertListEqual(muscles, json_data["muscles"])
        self.assertListEqual(tutorials, json_data["tutorials"])

    def test_edit_exercise_fail(self):
        """Try to edit exercise not owned by you."""
        json_data = {
            "name": "exercise 1 edited",
            "kind": "tim",
            "tags": [],
            "muscles": [],
            "tutorials": [],
            "instructions": "",
        }

        exercise_to_edit = Exercise.objects.get(owner=self.other_user.pk, name="exercise 1")
        exercise_stringified_before = str(model_to_dict(exercise_to_edit))

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        exercise_to_edit.refresh_from_db()
        exercise_stringified_after = str(model_to_dict(exercise_to_edit))
        self.assertEquals(exercise_stringified_before, exercise_stringified_after)

    def test_edit_exercise_errors(self):
        """Try to edit exercise with invalid data and expect validation errors."""
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

        exercise_to_edit = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")
        exercise_stringified_before = str(model_to_dict(exercise_to_edit))

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field, value in json_data.items():
            self.assertTrue(field in response.data, msg=f"{field} should give validation error")
            if isinstance(value, list):
                self.assertEqual(
                    len(value),
                    len(response.data[field]),
                    msg=f"{field} should give {len(value)} validation errors"
                    + f" but gave {len(response.data[field])}",
                )

        exercise_to_edit.refresh_from_db()
        exercise_stringified_after = str(model_to_dict(exercise_to_edit))
        self.assertEquals(exercise_stringified_before, exercise_stringified_after)

    def test_edit_exercise_name_collision(self):
        """Try to edit exercise with valid data but with name of exercise you already own. This
        should be impossible due to owner and exercise name should be unique together."""
        json_data = {
            "name": "exercise 2",
            "kind": "rew",
            "tags": [],
            "muscles": [],
            "tutorials": [],
            "instructions": "",
        }

        exercise_to_edit = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")
        exercise_stringified_before = str(model_to_dict(exercise_to_edit))

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("non_field_errors" in response.data)

        exercise_to_edit.refresh_from_db()
        exercise_stringified_after = str(model_to_dict(exercise_to_edit))
        self.assertEquals(exercise_stringified_before, exercise_stringified_after)

    def test_fork_exercise(self):
        """Fork other user's exercise when this is permitted (no name collision)."""
        exercise_to_fork = Exercise.objects.get(owner=self.other_user.pk, name="fork me")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_fork.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        exercise_to_fork.refresh_from_db()
        exercise_forked = Exercise.objects.get(owner=self.owner, name="fork me")

        # Test forking logic
        self.assertEqual(exercise_forked.forks_count, 0, msg="forked exercise should have 0 forks")
        self.assertEqual(
            exercise_to_fork.forks_count, 11, msg="original exercise should have new fork"
        )

        self.assertEqual(exercise_forked.kind, exercise_to_fork.kind)
        self.assertEqual(exercise_forked.instructions, exercise_to_fork.instructions)
        for field_name in ("tags", "muscles", "tutorials"):
            self.assertListEqual(
                list(getattr(exercise_forked, field_name).all()),
                list(getattr(exercise_to_fork, field_name).all()),
            )

    def test_fork_exercise_name_collision(self):
        """Try to fork exercise of other user when you already own an exercise with same name."""
        n_exercises_before = len(Exercise.objects.all())
        exercise_to_fork = Exercise.objects.get(owner=self.other_user.pk, name="exercise 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_fork.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Exercise.objects.all()), n_exercises_before)

    def test_fork_exercise_fail(self):
        """Try to fork your own exercise"""
        n_exercises_before = len(Exercise.objects.all())
        exercise_to_fork = Exercise.objects.get(owner=self.owner.pk, name="exercise 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"exercise_id": exercise_to_fork.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Exercise.objects.all()), n_exercises_before)
