from django.http import Http404
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from api.filters.exercise import ExerciseFilter
from api.models import Exercise
from api.serializers.exercise import ExerciseSerializer


class ExerciseList(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):

    permission_classes = (permissions.IsAuthenticated,)
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ExerciseFilter


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
        serializer = ExerciseSerializer(exercise, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, exercise_id, format=None):
        """Edit exercise data. This can be done only if the user requesting edot is an exercise
        owner."""
        exercise = self.get_object(exercise_id)
        if request.user == exercise.owner:
            serializer = ExerciseSerializer(
                exercise, data=request.data, context={"request": request}
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
                {"name": "You already own an exercise with this name"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create a copy
        exercise.fork(request.user)

        # Increase forks count
        exercise = self.get_object(exercise_id)
        exercise.forks_count += 1
        exercise.save()

        serializer = ExerciseSerializer(exercise, context={"request": request})
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
