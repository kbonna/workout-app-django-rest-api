from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.filters.exercise import ExerciseFilter
from api.models import Exercise
from api.permissions import IsOwnerOrReadOnly
from api.serializers.exercise import ExerciseSerializer


class ExerciseList(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):

    permission_classes = (permissions.IsAuthenticated,)
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ExerciseFilter


class ExerciseDetail(
    GenericViewSet, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin
):

    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    lookup_url_kwarg = "exercise_pk"

    def get_permissions(self):
        if self.action == "fork":
            return [permissions.IsAuthenticated()]
        return [IsOwnerOrReadOnly()]

    def fork(self, request, exercise_pk, format=None):
        """Fork (copy) exercise. This operation creates new exercise with all internal values
        copied but new owner. New owner is the author of the request.

        If fork is successful updated instance of forked exercise is send in response payload.

        If fork is unsuccessful dict with errors is send in response payload.
        """
        exercise = self.get_object()

        # Detect name collision
        if Exercise.objects.filter(owner=request.user, name=exercise.name).count():
            return Response(
                {"name": "You already own an exercise with this name"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create a copy
        exercise.fork(request.user)

        # Increase forks count
        exercise = self.get_object()
        exercise.forks_count += 1
        exercise.save()

        serializer = ExerciseSerializer(exercise, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
