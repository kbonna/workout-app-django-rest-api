from api.models import Routine
from api.serializers.routine import RoutineSerializer
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class RoutineList(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        """Adds new routine for specic user."""
        serializer = RoutineSerializer(
            data={**request.data, "owner": request.user.pk}, context={"owner": request.user.pk}
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
        user_id = request.GET.get("user", None)
        discover = request.GET.get("discover", False)

        if user_id:
            if discover:
                queryset = Routine.objects.exclude(owner=user_id)
            else:
                queryset = Routine.objects.filter(owner=user_id)
        else:
            queryset = Routine.objects.all()

        serializer = RoutineSerializer(queryset, context={"user_id": user_id}, many=True)

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
        serializer = RoutineSerializer(routine, context={"user_id": request.user.pk})
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
                context={"owner": request.user.pk},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)
