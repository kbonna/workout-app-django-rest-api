from django.urls import path

from api.views.exercise import ExerciseList, ExerciseDetail
from api.views.routine import RoutineList, RoutineDetail
from api.views.workout import WorkoutList, WorkoutDetail

list_action_mapping = {"post": "create", "get": "list"}
detail_action_mapping = {"get": "retrieve", "put": "update", "delete": "destroy"}

urlpatterns = [
    path("exercises/", ExerciseList.as_view(list_action_mapping), name="exercise-list"),
    path(
        "exercises/<int:exercise_pk>",
        ExerciseDetail.as_view({**detail_action_mapping, "post": "fork"}),
        name="exercise-detail",
    ),
    path("routines/", RoutineList.as_view(list_action_mapping), name="routine-list"),
    path("routines/<int:routine_id>", RoutineDetail.as_view(), name="routine-detail"),
    path("workouts/", WorkoutList.as_view(list_action_mapping), name="workout-list"),
    path(
        "workouts/<int:workout_pk>",
        WorkoutDetail.as_view(detail_action_mapping),
        name="workout-detail",
    ),
]
