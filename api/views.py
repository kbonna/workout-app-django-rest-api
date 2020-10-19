from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Exercise
from .serializers import (
    UserSerializer,
    UserSerializerWithToken,
    ExerciseListSerializer,
    ExerciseDetailSerializer,
)


@api_view(['GET'])
def current_user(request):
    """
    Determine the current user by their token, and return their data
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class UserList(APIView):
    """
    Create a new user. It's called 'UserList' because normally we'd have a get
    method here too, for retrieving a list of all User objects.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = UserSerializerWithToken(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        users = [user for user in User.objects.all()]
        serializer = UserSerializer(data=users, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)


class ExerciseList(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        """
        Adds new exercise for specic user.
        """
        serializer = ExerciseListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        """
        Return a list of all exercises.

        Querystring params:
            ?user=<int>:
                Exercises for user with specific pk.
        """
        owner = request.GET.get('user', None)
        if owner:
            queryset = Exercise.objects.filter(owner=owner)
        else:
            queryset = Exercise.objects.all()

        serializer = ExerciseListSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ExerciseDetail(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, exercise_id, format=None):
        """
        Detailed information about specific exercise.
        """
        serializer = ExerciseDetailSerializer(
            Exercise.objects.get(pk=exercise_id)
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        pass

    def delete(self, request, format=None):
        print(request)