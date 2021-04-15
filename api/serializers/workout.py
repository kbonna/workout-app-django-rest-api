from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from ..models import Workout, WorkoutLogEntry, Exercise


class WorkoutLogEntrySerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = WorkoutLogEntry
        fields = [
            "workout",
            "exercise",
            "exercise_name",
            "set_number",
            "reps",
            "weight",
            "time",
            "distance",
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=WorkoutLogEntry.objects.all(),
                fields=["workout", "exercise", "set_number"],
                message="You already created entry for this set.",
            )
        ]

    def validate_exercise(self, exercise):
        routine_owner_pk = self.context["requesting_user_pk"]
        if exercise.owner.pk != routine_owner_pk:
            raise ValidationError("This is not your exercise.")
        return exercise

    def validate(self, data):
        """Check units values correspond to exercise type. For example rep type exercise should only
        have reps field filled and rest of the units field set to NULL."""
        exercise_kind = data["exercise"].kind
        if exercise_kind == "rep":
            if data["reps"] is None:
                raise ValidationError("For this exercise reps should be specified.")
            if (data["weight"], data["time"], data["distance"]) != (None, None, None):
                raise ValidationError("For this exercise only reps should be specified.")

        return data


# class RoutineSerializer(serializers.ModelSerializer):
#     exercises = RoutineUnitSerializer(source="routine_units", many=True, required=False)
#     owner_username = serializers.CharField(source="owner.username", read_only=True)
#     kind_display = serializers.CharField(source="get_kind_display", read_only=True)
#     can_be_forked = serializers.SerializerMethodField("_can_be_forked", read_only=True)
#     can_be_modified = serializers.SerializerMethodField("_can_be_modified", read_only=True)
#     muscles_count = serializers.DictField(read_only=True)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Passing context to the nested serializer (context contain user pk, which is required for
#         # validating exercise owner match routine owner)
#         self.fields["exercises"].context.update(self.context)

#     def _can_be_forked(self, obj):
#         requesting_user_pk = self.context.get("requesting_user_pk")
#         if requesting_user_pk is not None:
#             return obj.can_be_forked(requesting_user_pk)
#         return None

#     def _can_be_modified(self, obj):
#         requesting_user_pk = self.context.get("requesting_user_pk")
#         if requesting_user_pk is not None:
#             return obj.can_be_modified(requesting_user_pk)
#         return None

#     class Meta:
#         model = Routine
#         fields = (
#             "pk",
#             "name",
#             "kind",
#             "kind_display",
#             "owner",
#             "owner_username",
#             "instructions",
#             "can_be_forked",
#             "can_be_modified",
#             "forks_count",
#             "exercises",
#             "muscles_count",
#         )
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Routine.objects.all(),
#                 fields=["name", "owner"],
#                 message="You already own this routine.",
#             )
#         ]

#     def create(self, validated_data):
#         routine_units = validated_data.pop("routine_units", [])

#         instance = Routine(**validated_data)
#         instance.save()

#         # Setup many to many relations
#         for routine_unit in routine_units:
#             exercise = routine_unit.pop("exercise")
#             instance.exercises.add(exercise, through_defaults=routine_unit)

#         return instance

#     def update(self, instance, validated_data):
#         instance.name = validated_data.get("name")
#         instance.kind = validated_data.get("kind")
#         instance.instructions = validated_data.get("instructions")

#         # Clear and setup again many to many relations
#         instance.exercises.clear()
#         for routine_unit in validated_data["routine_units"]:
#             exercise = routine_unit.pop("exercise")
#             instance.exercises.add(exercise, through_defaults=routine_unit)

#         instance.save()

#         return instance
