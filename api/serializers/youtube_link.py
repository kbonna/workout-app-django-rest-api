from rest_framework import serializers

from ..models import YoutubeLink
from ..validators import youtube_link


class YoutubeLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeLink
        fields = ['url']
        extra_kwargs = {'url': {'validators': [youtube_link]}}
