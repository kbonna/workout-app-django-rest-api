from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from api.models import Workout, WorkoutLogEntry, Exercise
from api.validators import validate_exercite_units
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


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
        if exercise.owner != self.context["request"].user:
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
        extra_kwargs = {"owner": {"read_only": True}, "completed": {"default": False}}

    def validate_routine(self, routine):
        # Validate only if routine is specified, skip for None or empty string
        if routine:
            if routine.owner != self.context["request"].user:
                raise ValidationError("This is not your routine.")
        return routine

    def validate(self, data):
        # User provided log entries
        log_entries = data.get("log_entries", [])
        data_logs = set()
        for log_entry in log_entries:
            data_logs.add((log_entry["exercise"], log_entry["set_number"]))

        if data.get("routine"):
            # Routine is specified
            routine_required_logs = set()
            for ru in data["routine"].routine_units.all():
                routine_required_logs.update([(ru.exercise, s) for s in range(1, ru.sets + 1)])
            excess_logs = data_logs - routine_required_logs
            missing_logs = routine_required_logs - data_logs

        elif log_entries:
            # Routine is not specified but log entries are specified
            integrity_required_logs = set()
            for log_entry in log_entries:
                integrity_required_logs.update(
                    [(log_entry["exercise"], s) for s in range(1, log_entry["set_number"] + 1)]
                )
            excess_logs = set()
            missing_logs = integrity_required_logs - data_logs

        else:
            # Neither routine nor log entries are specified
            excess_logs, missing_logs = set(), set()

        errors = []
        for exercise, set_number in excess_logs:
            errors.append(
                f"Exercise {exercise.name}: set {set_number} should not be specified for this routine."
            )
        for exercise, set_number in missing_logs:
            errors.append(f"Exercise {exercise.name}: set {set_number} is missing.")

        if errors:
            raise ValidationError({"integrity": sorted(errors)})

        return data

    def create(self, validated_data):
        log_entries = validated_data.pop("log_entries", [])

        instance = Workout(owner=self.context["request"].user, **validated_data)
        instance.save()

        # Setup many to many relations
        for log_entry in log_entries:
            WorkoutLogEntry.objects.create(workout=instance, **log_entry)

        return instance

    def update(self, instance, validated_data):
        instance.date = validated_data.pop("date")
        instance.completed = validated_data.pop("completed")
        instance.routine = validated_data.pop("routine")

        # Clear and setup again many to many relations
        log_entries = validated_data.pop("log_entries", [])
        instance.exercises.clear()
        for log_entry in log_entries:
            WorkoutLogEntry.objects.create(workout=instance, **log_entry)

        instance.save()
        return instance
