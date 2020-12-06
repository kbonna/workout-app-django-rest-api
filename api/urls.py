from django.urls import path
from .views.user import current_user, UserList
from .views.exercise import ExerciseList, ExerciseDetail

urlpatterns = [
    path("current_user/", current_user),
    path("users/", UserList.as_view(), name="user-list"),
    path("exercises/", ExerciseList.as_view(), name="exercise-list"),
    path("exercises/<int:exercise_id>", ExerciseDetail.as_view(), name="exercise-detail"),
]
