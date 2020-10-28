from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404
from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Exercise
from .serializers import (
    ExerciseDetailSerializer,
    ExerciseListSerializer,
    UserSerializer,
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
        """
        Creates new user. Data passed in request has to contain username and
        password.
        """
        serializer = UserSerializer(data=request.data)
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

    # permission_classes = (permissions.AllowAny,)
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
            ?discover=<bool>:
                Parameter for discover tab. If True, all exercise not owned by
                the user will be returned.
        """
        user_id = request.GET.get('user', None)
        discover = request.GET.get('discover', False)

        if user_id:
            if discover:
                queryset = Exercise.objects.all().exclude(owner=user_id)
            else:
                queryset = Exercise.objects.filter(owner=user_id)
        else:
            queryset = Exercise.objects.all()

        serializer = ExerciseListSerializer(
            queryset, context={'user_id': user_id}, many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class ExerciseDetail(APIView):

    # permission_classes = (permissions.AllowAny,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Exercise.objects.get(pk=pk)
        except Exercise.DoesNotExist:
            raise Http404

    def get(self, request, exercise_id, format=None):
        """
        Detailed information about specific exercise.
        """
        exercise = self.get_object(exercise_id)
        serializer = ExerciseDetailSerializer(exercise)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, exercise_id, format=None):
        pass

    def post(self, request, exercise_id, format=None):
        """
        Fork.
        """
        print(request.user)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, exercise_id, format=None):
        """
        Delete specific exercise. This can be done only if the user requesting
        delete is an exercise owner.
        """
        exercise = self.get_object(exercise_id)
        if request.user == exercise.owner:
            exercise.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)