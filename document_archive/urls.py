"""
URL configuration for document_archive project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import RegisterView
from rest_framework.routers import DefaultRouter
from documents.views import (
    DocumentDetailViewSet,
    TagViewSet,
    CorrespondentViewSet,
    ProjectViewSet,
    DocumentTypeViewSet,
    NoteViewSet,
)

router = DefaultRouter()
router.register(r"documents", DocumentDetailViewSet)
router.register(r"projects", ProjectViewSet)
router.register(r"tags", TagViewSet)
router.register(r"document-type", DocumentTypeViewSet)
router.register(r"notes", NoteViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('accounts/', include('accounts.urls')),
    path('', include(router.urls)),
] + debug_toolbar_urls()