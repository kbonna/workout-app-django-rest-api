from rest_framework import serializers

from api.models import Muscle


class MuscleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscle
        fields = ["name"]
        extra_kwargs = {"name": {"validators": []}}
