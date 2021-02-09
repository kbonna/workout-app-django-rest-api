from api.serializers.user import UserDetailSerializer, UserSerializer
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from api.permissions import IsHimself


@api_view(["GET"])
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


class UserDetail(APIView):
    """..."""

    # ! Change later
    permission_classes = (permissions.IsAuthenticated, IsHimself)

    def get_object(self, pk):
        try:
            user = User.objects.get(pk=pk)
            self.check_object_permissions(request=self.request, obj=user)
            return user
        except User.DoesNotExist:
            raise Http404

    def get(self, request, user_pk, format=None):
        user = self.get_object(user_pk)
        serializer = UserDetailSerializer(user, context={"user_pk": request.user.pk})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_pk, format=None):
        user = self.get_object(user_pk)
        serializer = UserDetailSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)