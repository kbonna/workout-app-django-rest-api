from django.urls import path
from .views.user import (
    current_user,
    UserList,
    UserDetail,
    profile_picture_upload,
    password_reset,
    UserEmailUpdate,
)
from .views.exercise import ExerciseList, ExerciseDetail
from .views.routine import RoutineList, RoutineDetail


urlpatterns = [
    path("current_user/", current_user),
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:user_pk>", UserDetail.as_view(), name="user-detail"),
    path("users/<int:user_pk>/profile_picture", profile_picture_upload, name="profile-picture"),
    path("users/<int:user_pk>/password_reset", password_reset, name="password-reset"),
    path("users/<int:user_pk>/email_reset", UserEmailUpdate.as_view(), name="email-reset"),
    path("exercises/", ExerciseList.as_view(), name="exercise-list"),
    path("exercises/<int:exercise_id>", ExerciseDetail.as_view(), name="exercise-detail"),
    path("routines/", RoutineList.as_view(), name="routine-list"),
    path("routines/<int:routine_id>", RoutineDetail.as_view(), name="routine-detail"),
]
