from collections import Counter

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.fields.related import ManyToManyField


class Tag(models.Model):
    """Tags used to label exercises. They are global and can be added by all users. They can only be
    removed if all exercises (and other related enities) with corresponding tags are removed."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class YoutubeLink(models.Model):
    """Youtube links used to represent tutorial videos for exercises."""

    url = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.url


class Muscle(models.Model):
    """Muscle names used for graphical representation of muscle groups trained during the exercise.
    This table should be read only and contain rows corresponding to each muscle choice."""

    MUSCLES = (
        ("cal", "Calves"),
        ("qua", "Quadriceps"),
        ("ham", "Hamstrings"),
        ("glu", "Gluteus"),
        ("lob", "Lower back"),
        ("lat", "Lats"),
        ("sca", "Scapular muscles"),
        ("abs", "Abdominals"),
        ("pec", "Pectorals"),
        ("tra", "Trapezius"),
        ("del", "Deltoids"),
        ("tri", "Triceps"),
        ("bic", "Biceps"),
        ("for", "Forearms"),
    )

    name = models.CharField(max_length=3, choices=MUSCLES, unique=True)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    """Basic app entity used to represent single exercise."""

    EXERCISE_KINDS = (
        ("rep", "reps"),
        ("rew", "reps x weight"),
        ("tim", "time"),
        ("dis", "distance"),
    )

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=3, choices=EXERCISE_KINDS)
    instructions = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    forks_count = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag)
    tutorials = models.ManyToManyField(YoutubeLink)
    muscles = models.ManyToManyField(Muscle)

    class Meta:
        unique_together = [["name", "owner"]]

    def __str__(self):
        return f"Exercise(name={self.name}, kind={self.kind}, owner={self.owner})"

    def can_be_forked(self, user_pk):
        """Determine if user with user_pk already have any exercise with this exercise name. In such
        case exercise cannot be forked."""
        if Exercise.objects.filter(name=self.name, owner=user_pk):
            return False
        return True

    def fork(self, new_owner_pk):
        """Copy exercise to another user.

        Method assumes that this operation can be done, i.e. there is no name collision meaning that
        new_owner don't have exercise of this name yet. This method also don't automatically
        increase fork count of forked exercise.
        """
        many_to_many_fieldnames = [
            field.name for field in self._meta.get_fields() if isinstance(field, ManyToManyField)
        ]
        many_to_many_objects = {
            field: getattr(self, field).all() for field in many_to_many_fieldnames
        }

        self.pk = None
        self.owner = new_owner_pk
        self.forks_count = 0
        self.save()  # pk was set to None, so new db instance will be created

        for field, queryset in many_to_many_objects.items():
            getattr(self, field).set(queryset)

        return self


class Routine(models.Model):
    """Collection of exercises representing single workout template."""

    ROUTINE_KINDS = (("sta", "standard"), ("cir", "circuit"))

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=3, choices=ROUTINE_KINDS)
    instructions = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    forks_count = models.IntegerField(default=0)
    exercises = models.ManyToManyField(Exercise, through="RoutineUnit", related_name="routines")

    class Meta:
        unique_together = [["name", "owner"]]

    def __str__(self):
        return f"Routine(name={self.name}, kind={self.kind}, owner={self.owner})"

    def can_be_forked(self, user_pk):
        """Determine if user with user_pk already have any routine with this exercise name. In such
        case routine cannot be forked."""
        if Routine.objects.filter(name=self.name, owner=user_pk):
            return False
        return True

    def can_be_modified(self, user_pk):
        """Determine if user with user_pk is owner of the routine allowing him to modify or delete
        this routine."""
        return user_pk == self.owner.pk

    def muscles_count(self):
        """Create dictionary with all muscles targeted with specific routine. Each key will
        correspond to specific muscle and value will be integer equal to number of exercise
        targeting this muscle."""
        muscles_list = [
            muscle.name
            for muscle in Muscle.objects.filter(exercise__routine_units__routine__pk=self.pk)
        ]
        return dict(Counter(muscles_list))


class RoutineUnit(models.Model):
    """Exercise with additional information used to compose routines."""

    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name="routine_units")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="routine_units")
    sets = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    instructions = models.TextField(blank=True)

    def __str__(self):
        return f"RoutineUnit(routine={self.routine.name}, exercise={self.exercise.name}"


class Workout(models.Model):
    """Completed or planned routine. """

    routine = models.ForeignKey(Routine, related_name="workouts", on_delete=...)
    date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)


class WorkoutLogEntry(model.Model):
    ...