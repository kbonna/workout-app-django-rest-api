from django.http import Http404
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from utils.mixins import GetWithFilteringMixin, PostMixin

from api.filters.routines import RoutineFilter
from api.models import Exercise, Routine
from api.permissions import IsOwnerOrReadOnly
from api.serializers.routine import RoutineSerializer, RoutineUnitSerializer

# ROUTINE_FIELDS = [field.name for field in Routine._meta.get_fields()]
# ORDER_BY_OPTIONS = ROUTINE_FIELDS + [f"-{field}" for field in ROUTINE_FIELDS]


# class RoutineList(GenericViewSet, GetWithFilteringMixin, PostMixin):

#     queryset = Routine.objects.all()
#     permission_classes = (permissions.IsAuthenticated,)
#     serializer_class = RoutineSerializer

#     def get_filtering_kwargs(self):
#         return {"prefetch_related": ("owner", "exercises"), "order_by_options": ORDER_BY_OPTIONS}


class RoutineList(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):

    queryset = Routine.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RoutineSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RoutineFilter


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
        serializer = RoutineSerializer(routine, context={"request": request})
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
        serializer = RoutineSerializer(routine, data=request.data, context={"request": request})
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
        if Routine.objects.filter(owner=request.user, name=routine.name).exists():
            return Response(
                {"name": ["You already own routine with this name."]},
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

        serializer = RoutineSerializer(routine, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
