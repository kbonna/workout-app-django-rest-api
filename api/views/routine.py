from api.models import Exercise, Routine
from api.permissions import IsOwnerOrReadOnly
from api.serializers.routine import RoutineSerializer, RoutineUnitSerializer
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

ROUTINE_FIELDS = [field.name for field in Routine._meta.get_fields()]
ORDER_BY_OPTIONS = ROUTINE_FIELDS + [f"-{field}" for field in ROUTINE_FIELDS]


class RoutineList(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        """Adds new routine for specic user."""
        serializer = RoutineSerializer(
            data={**request.data, "owner": request.user.pk},
            context={"requesting_user_pk": request.user.pk},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)

    def get(self, request, format=None):
        """Return a list of all routines.

        Querystring params:
            ?user.eq=<int>:
                Routines for user with specific pk.
            ?user.neq=<int>:
                Routines that can be discovered by user with specific pk (routines which are not
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

        queryset = Routine.objects.all()

        if user_pk_filter:
            queryset = queryset.filter(owner=user_pk_filter)
        if user_pk_exclude:
            queryset = queryset.exclude(owner=user_pk_exclude)
        if order_by_field:
            queryset = queryset.order_by(order_by_field)
        if limit:
            queryset = queryset[: int(limit)]

        serializer = RoutineSerializer(
            queryset, context={"requesting_user_pk": request.user.pk}, many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class RoutineDetail(APIView):

    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)

    def get_object(self, pk, validate_permissions=True):
        try:
            instance = Routine.objects.get(pk=pk)
            if validate_permissions:
                self.check_object_permissions(request=self.request, obj=instance)
            return instance
        except Routine.DoesNotExist:
            raise Http404

    def get(self, request, routine_id, format=None):
        """Get information about specific routine."""
        routine = self.get_object(routine_id)
        serializer = RoutineSerializer(routine, context={"requesting_user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, routine_id, format=None):
        """Delete specific routine. This can be done only if the user requesting delete is an
        routine owner.
        """
        routine = self.get_object(routine_id)
        routine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, routine_id, format=None):
        """Edit routine data. This can be done only if the user requesting edit is routine owner."""
        routine = self.get_object(routine_id)
        serializer = RoutineSerializer(
            routine,
            data={**request.data, "owner": request.user.pk},
            context={"requesting_user_pk": request.user.pk},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, routine_id, format=None):
        """Fork (copy) routine. This operation creates new routine with all internal values
        copied but new owner. New owner is the author of the request.

        Routine many-to-many relation with exercises works as follows: if user making fork request
        owns an exercise contained in routine (exercise name must match) his version will be used,
        otherwise according exercise will be automatically forked along.

        If fork is successful updated instance of forked exercise is send in response payload.

        If fork is unsuccessful dict with errors is send in response payload.
        """
        routine = self.get_object(routine_id, validate_permissions=False)

        # Detect name collision
        if Routine.objects.filter(owner=request.user, name=routine.name).count():
            return Response(
                {"non_field_errors": "You already own routine with this name."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Grab all associated exercises
        routine_units = routine.routine_units.all()
        serializer = RoutineUnitSerializer(routine_units, many=True)

        routine.pk = None
        routine.owner = request.user
        routine.forks_count = 0
        routine.save()  # pk was set to None, so new db instance will be created

        for routine_unit_dict in serializer.data:
            try:
                # Scenario 1: user making fork already owns an exercise
                exercise = Exercise.objects.get(
                    name=routine_unit_dict["exercise_name"], owner=request.user
                )
            except Exercise.DoesNotExist:
                # Scenario 2: exercise is forked along routine
                exercise = Exercise.objects.get(pk=routine_unit_dict["exercise"]).fork(request.user)

            # Add new routine unit
            routine.exercises.add(
                exercise,
                through_defaults={
                    "sets": routine_unit_dict["sets"],
                    "instructions": routine_unit_dict["instructions"],
                },
            )

        # Increase routine forks count
        routine = self.get_object(routine_id, validate_permissions=False)
        routine.forks_count += 1
        routine.save()

        serializer = RoutineSerializer(routine, context={"requesting_user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
