from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from api.models import Routine, RoutineUnit


class RoutineUnitSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)
    routine_name = serializers.CharField(source="routine.name", read_only=True)

    class Meta:
        model = RoutineUnit
        fields = ["routine", "routine_name", "exercise", "exercise_name", "sets", "instructions"]
        read_only_fields = ["routine"]

    def validate_exercise(self, exercise):
        if exercise.owner.pk != self.context["request"].user.pk:
            raise ValidationError("This is not your exercise.")
        return exercise


class RoutineSerializer(serializers.ModelSerializer):
    exercises = RoutineUnitSerializer(source="routine_units", many=True, required=False)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    can_be_forked = serializers.SerializerMethodField("_can_be_forked", read_only=True)
    can_be_modified = serializers.SerializerMethodField("_can_be_modified", read_only=True)
    muscles_count = serializers.DictField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Passing context to the nested serializer (context contain request object which is required
        # for validating exercise)
        self.fields["exercises"].context.update(self.context)

    def _can_be_forked(self, obj):
        request = self.context.get("request")
        if request is not None:
            return obj.can_be_forked(request.user.pk)
        return None

    def _can_be_modified(self, obj):
        request = self.context.get("request")
        if request is not None:
            return obj.can_be_modified(request.user.pk)
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
            "can_be_modified",
            "forks_count",
            "exercises",
            "muscles_count",
        )
        extra_kwargs = {"owner": {"read_only": True}}

    def validate(self, data):
        requesting_user = self.context["request"].user
        if Routine.objects.filter(owner=requesting_user, name=data["name"]).exists():
            raise ValidationError({"name": "You already own this routine."})
        return data

    def create(self, validated_data):
        routine_units = validated_data.pop("routine_units", [])

        instance = Routine(**validated_data, owner=self.context["request"].user)
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
