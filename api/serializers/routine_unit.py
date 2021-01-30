from rest_framework import serializers
from rest_framework.validators import ValidationError

from ..models import RoutineUnit


class RoutineUnitSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)
    routine_name = serializers.CharField(source="routine.name", read_only=True)
    # exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())

    class Meta:
        model = RoutineUnit
        fields = ["routine", "routine_name", "exercise", "exercise_name", "sets", "instructions"]
        read_only_fields = ["routine"]

    def validate_exercise(self, exercise):
        routine_owner_pk = self.context["user_pk"]
        if exercise.owner.pk != routine_owner_pk:
            raise ValidationError("This is not your exercise.")
        return exercise
