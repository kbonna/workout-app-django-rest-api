from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from ..models import Routine, RoutineUnit  # , Exercise
from api.serializers.routine_unit import RoutineUnitSerializer


class RoutineSerializer(serializers.ModelSerializer):
    """..."""

    exercises = RoutineUnitSerializer(source="routine_units", many=True, required=False)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    can_be_forked = serializers.SerializerMethodField("_can_be_forked", read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Passing context to the nested serializer (context contain user pk, which is required for
        # validating exercise owner match routine owner)
        self.fields["exercises"].context.update(self.context)

    def _can_be_forked(self, obj):
        user_id = self.context.get("user_id")
        if user_id is not None:
            return obj.can_be_forked(user_id)
        return None

    class Meta:
        model = Routine
        fields = (
            "pk",
            "name",
            "kind",
            "kind_display",
            "owner",
            "owner_username",
            "instructions",
            "can_be_forked",
            "forks_count",
            "exercises",
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Routine.objects.all(),
                fields=["name", "owner"],
                message="You already own this routine.",
            )
        ]

    def create(self, validated_data):
        routine_units = validated_data.pop("routine_units", [])

        instance = Routine(**validated_data)
        instance.save()

        # Setup many to many relations
        for routine_unit in routine_units:
            exercise = routine_unit.pop("exercise")
            instance.exercises.add(exercise, through_defaults=routine_unit)

        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.kind = validated_data.get("kind")
        instance.instructions = validated_data.get("instructions")

        # Clear and setup again many to many relations
        instance.exercises.clear()
        for routine_unit in validated_data["routine_units"]:
            exercise = routine_unit.pop("exercise")
            instance.exercises.add(exercise, through_defaults=routine_unit)

        instance.save()

        return instance
