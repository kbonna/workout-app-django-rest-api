from api.filters.workout import WorkoutFilter
from api.models import Workout
from api.permissions import IsOwnerOrReadOnly
from api.serializers.workout import WorkoutSerializer
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from utils.mixins import GetWithFilteringMixin, PostMixin


class WorkoutList(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):

    queryset = Workout.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkoutSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = WorkoutFilter


class WorkoutDetail(APIView):

    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)

    def get_object(self, pk, validate_permissions=True):
        try:
            instance = Workout.objects.get(pk=pk)
            if validate_permissions:
                self.check_object_permissions(request=self.request, obj=instance)
            return instance
        except Workout.DoesNotExist:
            raise Http404

    def get(self, request, workout_id, format=None):
        """Get information about specific workout."""
        workout = self.get_object(workout_id)
        serializer = WorkoutSerializer(workout, context={"requesting_user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, workout_id, format=None):
        """Delete specific workout. This can be done only if the user requesting delete is an
        workout owner.
        """
        workout = self.get_object(workout_id)
        workout.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
