from django.urls import path
from .views.user import (
    current_user,
    UserList,
    UserDetail,
    UserEmailUpdate,
    UserPasswordUpdate,
    UserProfilePicture,
)

urlpatterns = [
    path("current_user/", current_user),
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:user_pk>", UserDetail.as_view(), name="user-detail"),
    path("users/<int:user_pk>/password-reset", UserPasswordUpdate.as_view(), name="password-reset"),
    path("users/<int:user_pk>/email-reset", UserEmailUpdate.as_view(), name="email-reset"),
    path(
        "users/<int:user_pk>/profile-picture", UserProfilePicture.as_view(), name="profile-picture"
    ),
]
