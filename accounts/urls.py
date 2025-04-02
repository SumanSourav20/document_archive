from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ActivateUserView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
)

from .views import ProfileViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    path('activate/<str:token>/', ActivateUserView.as_view(), name='activate-user'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('', include(router.urls))
]