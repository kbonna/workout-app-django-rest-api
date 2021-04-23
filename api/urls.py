from django.urls import path

from api.views.exercise import ExerciseList, ExerciseDetail
from api.views.routine import RoutineList, RoutineDetail
from api.views.workout import WorkoutList


urlpatterns = [
    path("exercises/", ExerciseList.as_view(), name="exercise-list"),
    path("exercises/<int:exercise_id>", ExerciseDetail.as_view(), name="exercise-detail"),
    path("routines/", RoutineList.as_view(), name="routine-list"),
    path("routines/<int:routine_id>", RoutineDetail.as_view(), name="routine-detail"),
    path("workouts/", WorkoutList.as_view(), name="workout-list"),
]
