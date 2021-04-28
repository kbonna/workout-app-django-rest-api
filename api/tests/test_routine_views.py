from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers.exercise import ExerciseSerializer
from api.serializers.routine import RoutineSerializer, RoutineUnitSerializer
from api.models import Exercise, Routine


class RoutineViewsTest(APITestCase):

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
        "can_be_modified",
        "forks_count",
        "exercises",
        "muscles_count",
    ]

    def authorize(self, user_obj):
        refresh = RefreshToken.for_user(user_obj)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def assertCorrectRoutine(self, routine_dict, routine_obj, user_request_pk):
        """Custom assertion for this APITestCase checking whether routine dict retrieved from API
        response match underlying database entry.

        Args:
            routine_dict (dict):
                Deserialized API response representing single routine.
            routine_obj (api.models.Exercise):
                Routine model instance.
            user_request_pk (int):
                User pk corresponding to the user making request.
        """
        self.assertEqual(set(routine_dict.keys()), set(self.ROUTINE_SERIALIZER_FIELDS))

        print(routine_dict)

        self.assertEqual(routine_dict["pk"], routine_obj.pk)
        self.assertEqual(routine_dict["name"], routine_obj.name)
        self.assertEqual(routine_dict["kind"], routine_obj.kind)
        self.assertEqual(routine_dict["instructions"], routine_obj.instructions)
        self.assertEqual(routine_dict["forks_count"], routine_obj.forks_count)

        self.assertEqual(routine_dict["kind_display"], routine_obj.get_kind_display())
        self.assertEqual(routine_dict["owner"], routine_obj.owner.pk)
        self.assertEqual(routine_dict["owner_username"], routine_obj.owner.username)
        self.assertEqual(routine_dict["can_be_forked"], routine_obj.can_be_forked(user_request_pk))
        self.assertEqual(
            routine_dict["can_be_modified"], routine_obj.can_be_modified(user_request_pk)
        )
        self.assertEqual(routine_dict["muscles_count"], routine_obj.muscles_count())

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
        self.owner = User.objects.create_user("owner", email="owner@email.com")
        self.other_user = User.objects.create_user("other_user", email="other_user@email.com")
        self.authorize(self.owner)

        # Exercises
        self.owner_exercises = [
            Exercise.objects.create(name=f"Owner exercise {i}", kind="rep", owner=self.owner)
            for i in range(1, 6)
        ] + [
            Exercise.objects.create(
                name="Same name exercise",
                kind="rep",
                owner=self.owner,
                instructions="owner instructions",
            )
        ]
        self.other_user_exercises = [
            Exercise.objects.create(name=f"Other exercise {i}", kind="rew", owner=self.other_user)
            for i in range(1, 6)
        ] + [
            Exercise.objects.create(
                name="Same name exercise",
                kind="rew",
                owner=self.other_user,
                instructions="other user instructions",
            )
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
            Routine.objects.create(name="Same name routine", kind="cir", owner=self.other_user),
            Routine.objects.create(
                name="Routine to fork",
                kind="cir",
                owner=self.other_user,
                instructions="routine fork me",
                forks_count=10,
            ),
        ]
        self.other_user_routines[0].exercises.set(
            self.other_user_exercises[:2], through_defaults={"sets": 3}
        )
        self.other_user_routines[1].exercises.set(
            self.other_user_exercises[2:], through_defaults={"sets": 4}
        )
        self.other_user_routines[-1].exercises.set(
            self.other_user_exercises, through_defaults={"sets": 10, "instructions": "fork me"}
        )

    def test_get_my_routines(self):
        """Get list of routines owned by you."""
        url = f"{reverse(self.LIST_URLPATTERN_NAME)}?user.eq={self.owner.pk}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.owner_routines))

        for routine_dict, routine_obj in zip(response.data, self.owner_routines):
            self.assertCorrectRoutine(routine_dict, routine_obj, self.owner.pk)

        # Ensure your own exercises cannot be forked
        for routine_dict in response.data:
            self.assertFalse(routine_dict["can_be_forked"])

    def test_get_discover_routines(self):
        """Get list of routines owned by other users."""
        url = f"{reverse(self.LIST_URLPATTERN_NAME)}?user.neq={self.owner.pk}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.other_user_routines))

        for routine_dict, routine_obj in zip(response.data, self.other_user_routines):
            self.assertCorrectRoutine(routine_dict, routine_obj, self.owner.pk)

        # Ensure other user routines that have same name as one of your routines cannot be forked
        self.assertTrue(response.data[0]["can_be_forked"])
        self.assertTrue(response.data[1]["can_be_forked"])
        self.assertFalse(response.data[2]["can_be_forked"])  # name collision
        self.assertTrue(response.data[3]["can_be_forked"])

    def test_get_routines_query_params(self):
        """Routine list endpoint should accept several query parameters: orderby, limit, user.eq
        and user.neq."""
        url = (
            f"{reverse(self.LIST_URLPATTERN_NAME)}"
            + f"?limit=2&orderby=-forks_count&user.eq={self.other_user.pk}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Right owner
        self.assertTrue(all(r["owner_username"] == "other_user" for r in response.data))

        # Limit to two routines
        self.assertEqual(len(response.data), 2)

        # Sorted by forks_count descending
        self.assertEqual(response.data[0]["forks_count"], 10)

    def test_get_routines_query_params_errors(self):
        """Wrong values of query parameters should result in 400."""
        querystrings = [
            "orderby=+forks_count",
            "orderby=notExistingColumn",
            "orderby=1",
            "limit=three",
            "limit=-500",
            "user.eq=owner",
            "user.eq=-999",
            "user.neq=",
            "user.neq=3.14",
        ]

        for querystring in querystrings:
            url = f"{reverse(self.LIST_URLPATTERN_NAME)}?{querystring}"
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_routines_query_params_emptyqs(self):
        """Right but extreme values of query parameters should return empty queryset."""
        querystrings = [
            "limit=0",
            "limit=0&orderby=-exercises",
            "user.eq=1000",
        ]

        for querystring in querystrings:
            url = f"{reverse(self.LIST_URLPATTERN_NAME)}?{querystring}"
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, [])

    def test_get_routine_detail(self):
        """Get detail of single routine."""
        routine = self.owner_routines[0]

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, dict))
        self.assertCorrectRoutine(response.data, routine, self.owner.pk)

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
        print(response.data)
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
            "can_be_forked": False,
            "can_be_modified": True,
            "forks_count": 0,
            "exercises": [],
            "muscles_count": {},
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
        self.assertDictEqual(response.data, {"name": ["You already own this routine."]})

    def test_edit_routine(self):
        """Edit routine with valid data."""
        owner_exercises_pk = [exercise.pk for exercise in self.owner_exercises]
        json_data = {
            "name": "Owner routine 1 edited",
            "kind": "cir",
            "instructions": "edited instructions",
            "exercises": [
                {"exercise": owner_exercises_pk[0], "sets": 3, "instructions": ""},
                {"exercise": owner_exercises_pk[3], "sets": 6, "instructions": "edited 3"},
                {"exercise": owner_exercises_pk[4], "sets": 6, "instructions": "edited 4"},
            ],
        }

        routine_to_edit = Routine.objects.get(owner=self.owner.pk, name="Owner routine 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        routine_to_edit.refresh_from_db()
        self.assertEqual(routine_to_edit.name, json_data["name"])
        self.assertEqual(routine_to_edit.kind, json_data["kind"])
        self.assertEqual(routine_to_edit.instructions, json_data["instructions"])
        self.assertEqual(routine_to_edit.owner, self.owner)

        # Ensure new routine units contain correct data (unused exercises should be removed)
        self.assertEqual(routine_to_edit.exercises.count(), 3)

        self.assertListEqual(
            [
                (ru.exercise.pk, ru.sets, ru.instructions)
                for ru in routine_to_edit.routine_units.all()
            ],
            [
                (ru_dict["exercise"], ru_dict["sets"], ru_dict["instructions"])
                for ru_dict in json_data["exercises"]
            ],
        )

    def test_edit_routine_not_owned_by_you(self):
        """Try to edid routine of other user. That should not be possible."""
        json_data = {
            "name": "Other routine 1 edited",
            "kind": "cir",
            "instructions": "",
        }

        routine_to_edit = Routine.objects.get(owner=self.other_user.pk, name="Other routine 1")
        routine_stringified_before = str(model_to_dict(routine_to_edit))

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        routine_to_edit.refresh_from_db()
        routine_stringified_after = str(model_to_dict(routine_to_edit))
        self.assertEqual(routine_stringified_before, routine_stringified_after)

    def test_edit_routine_incorrect_data(self):
        """Try to edit routine with incorrect data and expect errors."""
        json_data = {
            "name": "",
            "kind": "xxx",
            "exercises": [{}],
        }

        routine_to_edit = Routine.objects.get(owner=self.owner.pk, name="Owner routine 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "name": [ErrorDetail(string="This field may not be blank.", code="blank")],
                "kind": [ErrorDetail(string='"xxx" is not a valid choice.', code="invalid_choice")],
                "exercises": [
                    {
                        "exercise": [
                            ErrorDetail(string="This field is required.", code="required")
                        ],
                        "sets": [ErrorDetail(string="This field is required.", code="required")],
                    }
                ],
            },
        )

    def test_edit_routine_name_collision(self):
        """Try to edit routine with valid data but with name of routine you already own. This
        should be impossible due to owner and routine name should be unique together."""
        json_data = {
            "name": "Owner routine 2",
            "kind": "sta",
            "exercises": [],
        }

        routine_to_edit = Routine.objects.get(owner=self.owner.pk, name="Owner routine 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_edit.pk})
        response = self.client.put(url, json_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data, {"name": ["You already own this routine."]})

    def test_fork_routine(self):
        """Fork other user's routine when this is permitted (no name collision)."""
        routine_to_fork = Routine.objects.get(owner=self.other_user.pk, name="Routine to fork")

        # Grab exercise that should be a part of new routine but should not be recreated
        owner_exercise = Exercise.objects.get(owner=self.owner, name="Same name exercise")
        owner_exercise_data_before = ExerciseSerializer(owner_exercise).data

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_fork.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routine_to_fork.refresh_from_db()
        routine_forked = Routine.objects.get(owner=self.owner, name=routine_to_fork.name)

        # Test forking logic
        self.assertEqual(routine_forked.forks_count, 0, msg="forked routine should have 0 forks")
        self.assertEqual(
            routine_to_fork.forks_count, 11, msg="original routine should have new fork"
        )

        self.assertEqual(routine_forked.kind, routine_to_fork.kind)
        self.assertEqual(routine_forked.instructions, routine_to_fork.instructions)

        serializer = RoutineUnitSerializer(routine_forked.routine_units.all(), many=True)

        exercise_names = [
            "Other exercise 1",
            "Other exercise 2",
            "Other exercise 3",
            "Other exercise 4",
            "Other exercise 5",
            "Same name exercise",
        ]
        for exercise_name, routine_unit_dict in zip(exercise_names, serializer.data):
            self.assertEqual(routine_unit_dict["exercise_name"], exercise_name)
            self.assertEqual(routine_unit_dict["sets"], 10)
            self.assertEqual(routine_unit_dict["instructions"], "fork me")

        # Ensure forked rouine contains original owner exercise
        self.assertEqual(serializer.data[-1]["exercise"], owner_exercise_data_before["pk"])

        # Ensure owner "Same name exercise" exercise was not modified
        owner_exercise.refresh_from_db()
        owner_exercise_data_after = ExerciseSerializer(owner_exercise).data
        self.assertEqual(owner_exercise_data_before, owner_exercise_data_after)

    def test_fork_routine_name_collision(self):
        """Try to fork other user's routine when you already owns a routine with this name."""
        routine_to_fork = Routine.objects.get(owner=self.other_user.pk, name="Same name routine")
        owner_routine = Routine.objects.get(owner=self.owner.pk, name="Same name routine")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_fork.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertDictEqual(response.data, {"name": ["You already own routine with this name."]})

    def test_fork_routine_you_own(self):
        """Try to fork your own routine."""
        routine_to_fork = Routine.objects.get(owner=self.owner.pk, name="Owner routine 1")

        url = reverse(self.DETAIL_URLPATTERN_NAME, kwargs={"routine_id": routine_to_fork.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
