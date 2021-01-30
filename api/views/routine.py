from api.models import Routine, Exercise
from api.serializers.routine import RoutineSerializer
from api.serializers.routine_unit import RoutineUnitSerializer
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class RoutineList(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        """Adds new routine for specic user."""
        serializer = RoutineSerializer(
            data={**request.data, "owner": request.user.pk}, context={"user_pk": request.user.pk}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)

    def get(self, request, format=None):
        """Return a list of all routines.

        Querystring params:
            ?user=<int>:
                Routines for user with specific pk.
            ?discover=<bool>:
                Parameter for discover tab. If True, all routines not owned by the user will be
                returned.
        """
        user_pk_filter = request.GET.get("user", None)
        discover = request.GET.get("discover", False)

        if user_pk_filter:
            if discover:
                queryset = Routine.objects.exclude(owner=user_pk_filter)
            else:
                queryset = Routine.objects.filter(owner=user_pk_filter)
        else:
            queryset = Routine.objects.all()

        serializer = RoutineSerializer(queryset, context={"user_pk": request.user.pk}, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class RoutineDetail(APIView):

    permission_classes = (permissions.AllowAny,)

    def get_object(self, pk):
        try:
            return Routine.objects.get(pk=pk)
        except Routine.DoesNotExist:
            raise Http404

    def get(self, request, routine_id, format=None):
        """Get information about specific routine."""
        routine = self.get_object(routine_id)
        serializer = RoutineSerializer(routine, context={"user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, routine_id, format=None):
        """Delete specific routine. This can be done only if the user requesting delete is an
        routine owner.
        """
        routine = self.get_object(routine_id)
        if request.user == routine.owner:
            routine.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self, request, routine_id, format=None):
        """Edit routine data. This can be done only if the user requesting edit is routine owner."""
        routine = self.get_object(routine_id)
        if request.user == routine.owner:
            serializer = RoutineSerializer(
                routine,
                data={**request.data, "owner": request.user.pk},
                context={"user_pk": request.user.pk},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request, routine_id, format=None):
        """Fork (copy) routine. This operation creates new routine with all internal values
        copied but new owner. New owner is the author of the request.

        Routine many-to-many relation with exercises works as follows: if user making fork request
        owns an exercise contained in routine (exercise name must match) his version will be used,
        otherwise according exercise will be automatically forked along.

        If fork is successful updated instance of forked exercise is send in response payload.

        If fork is unsuccessful dict with errors is send in response payload.
        """
        routine = self.get_object(routine_id)

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
        routine = self.get_object(routine_id)
        routine.forks_count += 1
        routine.save()

        serializer = RoutineSerializer(routine, context={"user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
