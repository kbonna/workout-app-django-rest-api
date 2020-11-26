from rest_framework import serializers
from ..validators import only_letters_and_numbers

from ..models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']
        extra_kwargs = {'name': {'validators': [only_letters_and_numbers]}}
