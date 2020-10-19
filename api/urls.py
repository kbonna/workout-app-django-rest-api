from django.urls import path
from .views import current_user, UserList, ExerciseList, ExerciseDetail

urlpatterns = [
    path('current_user/', current_user),
    path('users/', UserList.as_view()),
    path('exercises/', ExerciseList.as_view()),
    path('exercises/<int:exercise_id>', ExerciseDetail.as_view()),
]