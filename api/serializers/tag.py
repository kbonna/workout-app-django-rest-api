from rest_framework import serializers
from api.validators import only_letters_and_numbers

from api.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]
        extra_kwargs = {"name": {"validators": [only_letters_and_numbers]}}
