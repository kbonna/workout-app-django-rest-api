from api.permissions import IsHisResource, IsUserOrReadOnly  # TODO: move to utils?
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import UserProfile

# TODO: switch to that import later
from accounts.serializers import UserProfilePictureSerializer

from ..serializers.user import (
    BasicUserDetailSerializer,
    FullUserDetailSerializer,
    UserEmailSerializer,
    UserPasswordSerializer,
    UserSerializer,
)


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

    GET:
        Acessible for any authenticated user. Serializer class is different depending on if user
        requests his own data. In this case email field is visible, otherwise it is hidden.
    PUT:
        Accessible only for users trying to change their own profile data.
    DELETE:
        Accessible only for users wanting to delete their own account.
    """

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

    def delete(self, request, user_pk, format=None):
        user = self.get_object(user_pk)
        user.profile.delete()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class UserProfilePicture(APIView):
    """..."""

    permission_classes = (permissions.IsAuthenticated, IsHisResource)
    parser_classes = (MultiPartParser,)

    @staticmethod
    def delete_profile_picture_from_storage(profile):
        """Delete current profile picture for profile instance only when it is not default."""
        if profile.profile_picture.name != profile._meta.get_field("profile_picture").default:
            storage = profile.profile_picture.storage
            storage.delete(profile.profile_picture.name)

    def get_object(self, pk):
        try:
            profile = UserProfile.objects.get(user_id=pk)
            self.check_object_permissions(request=self.request, obj=profile)
            return profile
        except UserProfile.DoesNotExist:
            raise Http404

    def put(self, request, user_pk, format=None):
        profile = self.get_object(user_pk)
        serializer = UserProfilePictureSerializer(profile, data=request.data)
        if serializer.is_valid():
            self.delete_profile_picture_from_storage(profile=profile)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_pk, format=None):
        profile = self.get_object(user_pk)
        self.delete_profile_picture_from_storage(profile=profile)
        # Restore default profile picture
        profile.profile_picture = UserProfile().profile_picture
        profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
