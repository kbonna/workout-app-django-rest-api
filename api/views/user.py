from api.models import UserProfile
from api.permissions import IsHisResource, IsUserOrReadOnly
from api.serializers.user import (
    BasicUserDetailSerializer,
    FullUserDetailSerializer,
    UserEmailSerializer,
    UserPasswordSerializer,
    UserProfilePictureSerializer,
    UserSerializer,
)
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView


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
    """Read and update user profile data.

    GET is acessible for any authenticated user. Serializer class is different depending on if user
    requests his own data. In this case email field is visible, otherwise it is hidden. PUT is
    accessible only for users trying to change their own profile data."""

    permission_classes = (permissions.IsAuthenticated, IsUserOrReadOnly)

    def get_object(self, pk):
        try:
            user = User.objects.get(pk=pk)
            self.check_object_permissions(request=self.request, obj=user)
            return user
        except User.DoesNotExist:
            raise Http404

    def get(self, request, user_pk, format=None):
        user = self.get_object(user_pk)

        if request.user.pk == user_pk:
            serializer = FullUserDetailSerializer(user)
        else:
            serializer = BasicUserDetailSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_pk, format=None):
        user = self.get_object(user_pk)
        serializer = FullUserDetailSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfilePictureUpdate(generics.UpdateAPIView):
    queryset = UserProfile
    serializer_class = UserProfilePictureSerializer
    permission_classes = (permissions.IsAuthenticated, IsHisResource)
    parser_classes = (MultiPartParser,)
    lookup_url_kwarg = "user_pk"

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.objects.get(user=self.kwargs["user_pk"])
        return obj


class UserPasswordUpdate(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPasswordSerializer
    permission_classes = (permissions.IsAuthenticated, IsHisResource)
    lookup_url_kwarg = "user_pk"


class UserEmailUpdate(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserEmailSerializer
    permission_classes = (permissions.IsAuthenticated, IsHisResource)
    lookup_url_kwarg = "user_pk"
