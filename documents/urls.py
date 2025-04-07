from django.urls import path, include

from accounts.views import RegisterView
from rest_framework.routers import DefaultRouter
from documents.views import (
    DocumentDetailViewSet, 
    PostDocumentView,
    TagViewSet,
    CorrespondentViewSet,
    ProjectViewSet,
    DocumentTypeViewSet,
    NoteViewSet,
)

router = DefaultRouter()
router.register(r"documents", DocumentDetailViewSet)
router.register(r"tags", TagViewSet)
router.register(r"document-type", DocumentTypeViewSet)
router.register(r"Note", NoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]