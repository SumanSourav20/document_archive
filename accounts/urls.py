from django.urls import path, include

from accounts.views import (
    ActivateUserView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    ProfileListView,
    MyProfileView,
)

urlpatterns = [
    path('activate/<str:token>/', ActivateUserView.as_view(), name='activate-user'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('profiles/', ProfileListView.as_view(), name='profile-list'),
    path('profiles/me/', MyProfileView.as_view(), name='my-profile'),
]