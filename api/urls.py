from django.urls import path

from api.views.exercise import ExerciseList, ExerciseDetail
from api.views.routine import RoutineList, RoutineDetail
from api.views.workout import WorkoutList, WorkoutDetail


urlpatterns = [
    path(
        "exercises/", ExerciseList.as_view({"post": "create", "get": "list"}), name="exercise-list"
    ),
    path("exercises/<int:exercise_id>", ExerciseDetail.as_view(), name="exercise-detail"),
    path("routines/", RoutineList.as_view({"post": "create", "get": "list"}), name="routine-list"),
    path("routines/<int:routine_id>", RoutineDetail.as_view(), name="routine-detail"),
    path("workouts/", WorkoutList.as_view({"post": "post", "get": "get"}), name="workout-list"),
    path("workouts/<int:workout_id>", WorkoutDetail.as_view(), name="workout-detail"),
]
