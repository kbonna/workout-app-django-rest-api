from unittest import skip

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ErrorDetail

from ..models import Exercise, Routine


class RoutineTest(APITestCase):

    LIST_URLPATTERN_NAME = "routine-list"
    DETAIL_URLPATTERN_NAME = "routine-detail"
    ROUTINE_SERIALIZER_FIELDS = [
        "pk",
        "name",
        "kind",
        "kind_display",
        "owner",
        "owner_username",
        "instructions",
        "can_be_forked",
        "forks_count",
        "exercises",
    ]

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def assertCorrectRoutine(self, routine_dict, routine_obj, user_request):
        """Custom assertion for this APITestCase checking whether routine dict retrieved from API
        response match underlying database entry.

        Args:
            routine_dict (dict):
                Deserialized API response representing single routine.
            routine_obj (api.models.Exercise):
                Routine model instance.
            user_request (User):
                User model instance corresponding to the user making request.
        """
        self.assertEqual(set(routine_dict.keys()), set(self.ROUTINE_SERIALIZER_FIELDS))

        self.assertEqual(routine_dict["pk"], routine_obj.pk)
        self.assertEqual(routine_dict["name"], routine_obj.name)
        self.assertEqual(routine_dict["kind"], routine_obj.kind)
        self.assertEqual(routine_dict["instructions"], routine_obj.instructions)
        self.assertEqual(routine_dict["forks_count"], routine_obj.forks_count)

        self.assertEqual(routine_dict["kind_display"], routine_obj.get_kind_display())
        self.assertEqual(routine_dict["owner"], routine_obj.owner.pk)
        self.assertEqual(routine_dict["owner_username"], routine_obj.owner.username)
        self.assertEqual(routine_dict["can_be_forked"], routine_obj.can_be_forked(user_request))

        # Correct form of deserialized list of routine units
        exercises = [
            {
                "routine": ru.routine.pk,
                "routine_name": ru.routine.name,
                "exercise": ru.exercise.pk,
                "exercise_name": ru.exercise.name,
                "sets": ru.sets,
                "instructions": ru.instructions,
            }
            for ru in routine_obj.routine_units.all()
        ]
        self.assertEqual(routine_dict["exercises"], exercises)

    def setUp(self):
        # Users
        self.owner = User.objects.create_user("owner")
        self.other_user = User.objects.create_user("other_user")
        self.authorize(self.owner)

        # Exercises
        self.owner_exercises = [
            Exercise.objects.create(name=f"Owner exercise {i}", kind="rep", owner=self.owner)
            for i in range(1, 6)
        ]
        self.other_user_exercises = [
            Exercise.objects.create(name=f"Other exercise {i}", kind="rew", owner=self.other_user)
            for i in range(1, 6)
        ]

        # Routines
        self.owner_routines = [
            Routine.objects.create(name="Owner routine 1", kind="sta", owner=self.owner),
            Routine.objects.create(name="Owner routine 2", kind="sta", owner=self.owner),
            Routine.objects.create(name="Same name routine", kind="sta", owner=self.owner),
        ]
        self.owner_routines[0].exercises.set(self.owner_exercises[:2], through_defaults={"sets": 3})
        self.owner_routines[1].exercises.set(self.owner_exercises[2:], through_defaults={"sets": 4})

        self.other_user_routines = [
            Routine.objects.create(name="Other routine 1", kind="cir", owner=self.other_user),
            Routine.objects.create(name="Other routine 2", kind="cir", owner=self.other_user),
            Routine.objects.create(name="Same name routine", kind="sta", owner=self.other_user),
        ]
        self.other_user_routines[0].exercises.set(
            self.other_user_exercises[:2], through_defaults={"sets": 3}
        )
        self.other_user_routines[1].exercises.set(
            self.other_user_exercises[2:], through_defaults={"sets": 4}
        )

    def test_get_my_routines(self):
        """Get list of routines owned by you."""
        url = f"{reverse(self.LIST_URLPATTERN_NAME)}?user={self.owner.pk}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.owner_routines))

        for routine_dict, routine_obj in zip(response.data, self.owner_routines):
            self.assertCorrectRoutine(routine_dict, routine_obj, self.owner)

        # Ensure your own exercises cannot be forked
        for routine_dict in response.data:
            self.assertFalse(routine_dict["can_be_forked"])

    def test_get_discover_routines(self):
        """Get list of routines owned by other users."""
        url = f"{reverse(self.LIST_URLPATTERN_NAME)}?user={self.owner.pk}&discover=True"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.other_user_routines))

        for routine_dicv, routine_obj in zip(response.data, self.other_user_routines):
            self.assertCorrectRoutine(routine_dicv, routine_obj, self.owner)

        # Ensure other user routines that have same name as one of your routines cannot be forked
        self.assertTrue(response.data[0]["can_be_forked"])
        self.assertTrue(response.data[1]["can_be_forked"])
        self.assertFalse(response.data[2]["can_be_forked"])

    def test_get_routine_detail(self):
        """Get detail of single routine."""
        routine = self.owner_routines[0]

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, dict))
        self.assertCorrectRoutine(response.data, routine, self.owner)

    def test_delete_routine(self):
        """Delete routine when you are an routine owner."""
        routine_to_delete = Routine.objects.get(owner=self.owner.pk, name="Owner routine 1")
        n_routines_before = Routine.objects.all().count()

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Routine.objects.all().count(), n_routines_before - 1)
        with self.assertRaises(Routine.DoesNotExist):
            self.owner.routine_set.get(name="Owner routine 1")

    def test_delete_routine_fail(self):
        """Try to delete routine if you are not an owner."""
        routine_to_delete = Routine.objects.get(owner=self.other_user.pk, name="Other routine 1")
        n_routines_before = Routine.objects.all().count()

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Routine.objects.all().count(), n_routines_before)
        try:
            self.other_user.routine_set.get(name="Other routine 1")
        except Exercise.DoesNotExist:
            self.fail("routine that you don't own should not be deleted")

    def test_create_routine(self):
        """Create new routine with valid data."""
        exercises_pk = [exercise.pk for exercise in self.owner_exercises]
        json_data = {
            "name": "New routine",
            "kind": "sta",
            "instructions": "test instructions",
            "exercises": [
                {"exercise": exercises_pk[0], "sets": 5, "instructions": "test5"},
                {"exercise": exercises_pk[2], "sets": 6, "instructions": "test6"},
                {"exercise": exercises_pk[4], "sets": 7, "instructions": "test7"},
            ],
        }

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Object is created properly
        created_routine = Routine.objects.get(owner=self.owner.pk, name=json_data["name"])

        self.assertEqual(created_routine.kind, json_data["kind"])
        self.assertEqual(created_routine.owner, self.owner)
        self.assertEqual(created_routine.owner.username, self.owner.username)
        self.assertEqual(created_routine.forks_count, 0)
        self.assertEqual(created_routine.instructions, json_data["instructions"])

        self.assertEqual(created_routine.exercises.count(), 3)
        for routine_unit_dict, routine_unit_obj in zip(
            json_data["exercises"], created_routine.routine_units.all()
        ):
            self.assertEqual(routine_unit_dict["exercise"], routine_unit_obj.exercise.pk)
            self.assertEqual(routine_unit_dict["sets"], routine_unit_obj.sets)
            self.assertEqual(routine_unit_dict["instructions"], routine_unit_obj.instructions)

    def test_create_routine_without_exercises(self):
        """Create new routine without any exercises."""
        json_data = {
            "name": "New routine",
            "kind": "cir",
        }

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Response contain created resource data
        expected_response_data = {
            "name": "New routine",
            "kind": "cir",
            "kind_display": "circuit",
            "owner": 1,
            "owner_username": "owner",
            "instructions": "",
            "can_be_forked": None,
            "forks_count": 0,
            "exercises": [],
        }

        # Check only subset of keys excluding pk since it may vary
        self.assertTrue(
            all(item in response.data.items() for item in expected_response_data.items())
        )

        # Object is created properly
        created_routine = Routine.objects.get(owner=self.owner.pk, name=json_data["name"])

        self.assertEqual(created_routine.kind, json_data["kind"])
        self.assertEqual(created_routine.owner, self.owner)
        self.assertEqual(created_routine.owner.username, self.owner.username)
        self.assertEqual(created_routine.forks_count, 0)
        self.assertEqual(created_routine.instructions, "")
        self.assertEqual(created_routine.exercises.count(), 0)

    def test_create_routine_with_exercises_owned_by_other_user(self):
        """Try to create new routine with invalid data – with exercises owned by other user."""
        owner_exercises_pk = [exercise.pk for exercise in self.owner_exercises]
        other_user_exercises_pk = [exercise.pk for exercise in self.other_user_exercises]
        json_data = {
            "name": "New routine",
            "kind": "sta",
            "instructions": "test instructions",
            "exercises": [
                {"exercise": owner_exercises_pk[0], "sets": 5, "instructions": "test5"},
                {"exercise": other_user_exercises_pk[2], "sets": 6, "instructions": "test6"},
                {"exercise": other_user_exercises_pk[4], "sets": 7, "instructions": "test7"},
            ],
        }

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data,
            {
                "exercises": [
                    {},
                    {"exercise": ["This is not your exercise."]},
                    {"exercise": ["This is not your exercise."]},
                ]
            },
        )

    def test_create_routine_errors(self):
        """Try to create new routine with only invalid data and expect validation errors."""
        json_data = {
            "name": "",
            "kind": "sta",
            "exercises": [
                {"exercise": 0, "sets": -1},
                {"exercise": 0, "sets": "x"},
                {"exercise": 0},
            ],
        }

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data,
            {
                "name": [ErrorDetail(string="This field may not be blank.", code="blank")],
                "exercises": [
                    {
                        "exercise": [
                            ErrorDetail(
                                string='Invalid pk "0" - object does not exist.',
                                code="does_not_exist",
                            )
                        ],
                        "sets": [
                            ErrorDetail(
                                string="Ensure this value is greater than or equal to 1.",
                                code="min_value",
                            )
                        ],
                    },
                    {
                        "exercise": [
                            ErrorDetail(
                                string='Invalid pk "0" - object does not exist.',
                                code="does_not_exist",
                            )
                        ],
                        "sets": [
                            ErrorDetail(string="A valid integer is required.", code="invalid")
                        ],
                    },
                    {
                        "exercise": [
                            ErrorDetail(
                                string='Invalid pk "0" - object does not exist.',
                                code="does_not_exist",
                            )
                        ],
                        "sets": [ErrorDetail(string="This field is required.", code="required")],
                    },
                ],
            },
        )

    def test_create_routine_name_collision(self):
        """Try to create routine with name of the routine you already own."""
        json_data = {
            "name": "Owner routine 1",
            "kind": "cir",
        }

        url = reverse(self.LIST_URLPATTERN_NAME)
        response = self.client.post(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"non_field_errors": ["You already own this routine."]})

    def test_edit_routine(self):
        """Edit routine with valid data."""
        owner_exercises_pk = [exercise.pk for exercise in self.owner_exercises]
        json_data = {
            "name": "Owner routine 1 edited",
            "kind": "cir",
            "instructions": "edited instructions",
            "exercises": [
                {"exercise": owner_exercises_pk[2], "sets": 4, "instructions": "edited 1"},
                {"exercise": owner_exercises_pk[3], "sets": 5, "instructions": ""},
                {"exercise": owner_exercises_pk[4], "sets": 6, "instructions": ""},
            ],
        }

        routine_to_edit = Routine.objects.get(owner=self.owner.pk, name="Owner routine 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_edit.pk})
        response = self.client.put(url, json_data, format="json")
        print(response)