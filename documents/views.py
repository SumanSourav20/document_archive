from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from rest_framework import filters
import json

from django_filters.rest_framework import DjangoFilterBackend
from pathlib import Path
from django.conf import settings

from documents.serializers import (
    TagSerializer,
    CorrespondentSerializer,
    DocumentTypeSerializer,
    DocumentListSerializer,
    DocumentDetailSerializer,
    PostDocumentSerializer,
    ProjectSerializer,
    NotesSerializer,
)

from documents.models import (
    Document,
    Project,
    Tag,
    DocumentType,
    Note,
    Correspondent,
)
import magic
import hashlib


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    filter_backends=[DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status",]
    search_fields = ["title", "description"]
    ordering_fields = ["start_date"]

class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = DocumentType.objects.all()
    def get_serializer(self, *args, **kwargs):
        pass


class CorrespondentViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = DocumentType.objects.all()
    serializer_class = CorrespondentSerializer


class DocumentTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Note.objects.all()
    serializer_class = NotesSerializer

    filter_backends=[DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["document"]
    ordering_fields = ["created"]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user.id
        document = serializer.validated_data["document"]
        note = serializer.validated_data["note"]

        note = Note.objects.create(
            note=note,
            user=user,
            document=document,
        )
        response = NotesSerializer(note)
        return Response(
            {"status": "success", "note": response.data},
            status=status.HTTP_201_CREATED
        )
        
    

class DocumentDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Document.objects.all()
    filter_backends=[DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tags", "project", "document_type", ]
    ordering_fields = ["created", "added", "project"]


    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer
        elif self.action == "retrieve" :
            return DocumentDetailSerializer
        return PostDocumentSerializer


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_name, doc_data = serializer.validated_data.get("document")
        correspondent_id = serializer.validated_data.get("correspondent")
        document_type_id = serializer.validated_data.get("document_type")
        tag_ids = serializer.validated_data.get("tags")
        title = serializer.validated_data.get("title")
        created = serializer.validated_data.get("created")

        mime_type = magic.from_buffer(doc_data, mime=True)
        checksum = hashlib.md5(doc_data).hexdigest()

        filename = f"{checksum}_{doc_name}"
        full_path = Path(settings.ORIGINAL_DIR) / filename

        if not full_path.exists():
            with open(full_path, "wb") as f:
                f.write(doc_data)


        document = Document.objects.create(
            filename=filename,
            original_filename=doc_name,
            title=title,
            correspondent_id=correspondent_id,
            document_type_id=document_type_id,
            created=created,
            mime_type=mime_type,
            storage_type=Document.STORAGE_TYPE_UNENCRYPTED,
            checksum=checksum
        )

        if tag_ids:
            document.tags.set(tag_ids)

        return Response(
            {"status": "success", "id": document.id}, 
            status=status.HTTP_201_CREATED
        )


    