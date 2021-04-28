from api.models import Workout
from api.permissions import IsOwnerOrReadOnly
from api.serializers.workout import WorkoutSerializer
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from utils.mixins import PostMixin, GetWithFilteringMixin


WORKOUT_FIELDS = [field.name for field in Workout._meta.get_fields()]
ORDER_BY_OPTIONS = WORKOUT_FIELDS + [f"-{field}" for field in WORKOUT_FIELDS]


class WorkoutList(GenericViewSet, PostMixin, GetWithFilteringMixin):

    queryset = Workout.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkoutSerializer

    def get_prefetch_related(self):
        return ("owner",)

    def get_filtering_kwargs(self):
        return {"prefetch_related": ("owner",), "order_by_options": ORDER_BY_OPTIONS}


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
