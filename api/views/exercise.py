from api.models import Exercise
from api.serializers.exercise import ExerciseSerializer
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

EXERCISE_FIELDS = [field.name for field in Exercise._meta.get_fields()]
ORDER_BY_OPTIONS = EXERCISE_FIELDS + [f"-{field}" for field in EXERCISE_FIELDS]


class ExerciseList(APIView):

    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = []

    def post(self, request, format=None):
        """Adds new exercise for specic user."""
        serializer = ExerciseSerializer(data={**request.data, "owner": request.user.pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        """Return a list of all exercises.

        Querystring params:
            ?user.eq=<int>:
                Exercises for user with specific pk.
            ?user.neq=<int>:
                Exercises that can be discovered by user with specific pk (exercises which are not
                owned by user with this pk).
            ?orderby=<str>:
                Name of db column to order queryset. Default order is given by pk values. Django
                convention is used – the negative sign in front of column name indicates descending
                order.
            ?limit=<int>:
                Limit querysearch to specific number of records.
        """
        user_pk_filter = request.query_params.get("user.eq", None)
        user_pk_exclude = request.query_params.get("user.neq", None)
        order_by_field = request.query_params.get("orderby", None)
        limit = request.query_params.get("limit", None)

        # Validation
        if user_pk_filter is not None and not user_pk_filter.isdigit():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if user_pk_exclude is not None and not user_pk_exclude.isdigit():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if limit is not None and not limit.isdigit():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if order_by_field is not None and order_by_field not in ORDER_BY_OPTIONS:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Use prefetch_related to reduce number of queries
        queryset = Exercise.objects.all().prefetch_related("tags", "muscles", "tutorials", "owner")

        if user_pk_filter:
            queryset = queryset.filter(owner=user_pk_filter)
        if user_pk_exclude:
            queryset = queryset.exclude(owner=user_pk_exclude)
        if order_by_field:
            queryset = queryset.order_by(order_by_field)
        if limit:
            queryset = queryset[: int(limit)]

        serializer = ExerciseSerializer(
            queryset, context={"requesting_user_pk": request.user.pk}, many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class ExerciseDetail(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Exercise.objects.get(pk=pk)
        except Exercise.DoesNotExist:
            raise Http404

    def get(self, request, exercise_id, format=None):
        """Get information about specific exercise."""
        exercise = self.get_object(exercise_id)
        serializer = ExerciseSerializer(exercise, context={"requesting_user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, exercise_id, format=None):
        """Edit exercise data. This can be done only if the user requesting edot is an exercise
        owner."""
        exercise = self.get_object(exercise_id)
        if request.user == exercise.owner:
            serializer = ExerciseSerializer(
                exercise, data={**request.data, "owner": request.user.pk}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request, exercise_id, format=None):
        """Fork (copy) exercise. This operation creates new exercise with all internal values
        copied but new owner. New owner is the author of the request.

        If fork is successful updated instance of forked exercise is send in response payload.

        If fork is unsuccessful dict with errors is send in response payload.
        """
        exercise = self.get_object(exercise_id)

        # Detect name collision
        if Exercise.objects.filter(owner=request.user, name=exercise.name).count():
            return Response(
                {"non_field_errors": "You already own an exercise with this name"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create a copy
        exercise.fork(request.user)

        # Increase forks count
        exercise = self.get_object(exercise_id)
        exercise.forks_count += 1
        exercise.save()

        serializer = ExerciseSerializer(exercise, context={"user_id": request.user.pk})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, exercise_id, format=None):
        """Delete specific exercise. This can be done only if the user requesting delete is an
        exercise owner.
        """
        exercise = self.get_object(exercise_id)
        if request.user == exercise.owner:
            exercise.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)
