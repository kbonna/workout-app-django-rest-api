from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from ..models import Workout, WorkoutLogEntry, Exercise
from api.validators import validate_exercite_units
from django.contrib.auth.models import User


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
        validate_exercite_units(data["exercise"], data)
        return data


class WorkoutLogEntryNestedSerializer(WorkoutLogEntrySerializer):
    """Modified version of WorkoutLogEntrySerialzier used to serialize and deserialize nested
    log_entries field on Workout model.

    Notes:
        It differs from original version by setting workout field to read only since when we upload
        workout data we don't know workout pk in advance (it is not yet created in the db). Unique
        together validator is also remove to avoid conflicts with existing workouts – integrity
        related to set numbers is validated on the WorkoutSerializer (object level validation).
    """

    class Meta(WorkoutLogEntrySerializer.Meta):
        extra_kwargs = {"workout": {"read_only": True}}
        validators = []


class WorkoutSerializer(serializers.ModelSerializer):
    log_entries = WorkoutLogEntryNestedSerializer(many=True, required=False)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    routine_name = serializers.CharField(source="routine.name", read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Passing context to the nested serializer (context contain user pk, which is required for
        # validating workout owner match exercise owner)
        self.fields["log_entries"].context.update(self.context)

    class Meta:
        model = Workout
        fields = (
            "owner",
            "owner_username",
            "date",
            "completed",
            "routine",
            "routine_name",
            "log_entries",
        )
        extra_kwargs = {"owner": {"read_only": True}}

    def create(self, validated_data):
        log_entries = validated_data.pop("log_entries", [])

        owner = User.objects.get(pk=self.context["requesting_user_pk"])
        instance = Workout(owner=owner, **validated_data)
        instance.save()

        # Setup many to many relations
        for log_entry in log_entries:
            WorkoutLogEntry.objects.create(workout=instance, **log_entry)

        return instance

    def update(self, instance, validated_data):
        pass
        # instance.name = validated_data.get("name")
        # instance.kind = validated_data.get("kind")
        # instance.instructions = validated_data.get("instructions")

        # # Clear and setup again many to many relations
        # instance.exercises.clear()
        # for routine_unit in validated_data["routine_units"]:
        #     exercise = routine_unit.pop("exercise")
        #     instance.exercises.add(exercise, through_defaults=routine_unit)

        # instance.save()

        # return instance
