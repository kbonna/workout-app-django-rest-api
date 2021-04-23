from rest_framework.views import APIView
from api.serializers.workout import WorkoutSerializer
from rest_framework import permissions, status
from rest_framework.response import Response


class WorkoutList(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        """Adds new workout for specic user."""
        serializer = WorkoutSerializer(
            data=request.data,
            context={"requesting_user_pk": request.user.pk},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)