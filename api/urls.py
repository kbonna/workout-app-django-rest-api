from django.urls import path
from .views.user import current_user, UserList, UserDetail
from .views.exercise import ExerciseList, ExerciseDetail
from .views.routine import RoutineList, RoutineDetail
from .views.image import ImageList

urlpatterns = [
    path("current_user/", current_user),
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:user_pk>", UserDetail.as_view(), name="user-detail"),
    path("exercises/", ExerciseList.as_view(), name="exercise-list"),
    path("exercises/<int:exercise_id>", ExerciseDetail.as_view(), name="exercise-detail"),
    path("routines/", RoutineList.as_view(), name="routine-list"),
    path("routines/<int:routine_id>", RoutineDetail.as_view(), name="routine-detail"),
    path("images/", ImageList.as_view(), name="image-list"),
]
