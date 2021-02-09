from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from api.serializers.user import UserProfilePictureSerializer
from api.models import UserProfile


class ImageList(APIView):
    """
    ...
    """

    permission_classes = (permissions.AllowAny,)
    parser_classes = (MultiPartParser,)

    def put(self, request, format=None):
        try:
            image_type = self.request.data.pop("image_type")[0]
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if image_type == "profile_picture":
            serializer = UserProfilePictureSerializer(
                instance=UserProfile.objects.get(user=self.request.user), data=request.data
            )
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_200_OK)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)
