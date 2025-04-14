from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import filters
from django_filters.rest_framework import FilterSet, DateFilter, ModelMultipleChoiceFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
import json

from django_filters.rest_framework import DjangoFilterBackend
from pathlib import Path
from django.conf import settings
from django.http import FileResponse

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
from documents.tasks import process_document
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

class SetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_pages_size = 1000

class ProjectFilter(FilterSet):
    start_date_min = DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_max = DateFilter(field_name="start_date", lookup_expr="lte")

    class Meta:
        model = Project
        fields = {
            'status': ['exact'],
        }

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    filter_backends=[DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ["title", "description"]
    ordering_fields = ["start_date"]
    pagination_class = SetPagination

class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    search_fields = ["name"]


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = DocumentType.objects.all()
    def get_serializer(self, *args, **kwargs):
        pass


class CorrespondentViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Correspondent.objects.all()
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
        
        user = request.user
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
        
class DocumentFilter(FilterSet):
    created_min = DateFilter(field_name="created", lookup_expr="gte")
    created_max = DateFilter(field_name="created", lookup_expr="lte")

    tags = ModelMultipleChoiceFilter(
        field_name="tags__id",
        to_field_name="id",
        queryset=Tag.objects.all(),
        conjoined=True 
    )
    
    class Meta:
        model = Document
        fields = {
            'project': ['exact'],
            'document_type': ['exact'],
        }


class DocumentDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Document.objects.all()
    filter_backends=[DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentFilter
    ordering_fields = ["created", "added", "project"]
    pagination_class = SetPagination
    search_fields=["title"]


    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer
        elif self.action == "create" :
            return PostDocumentSerializer
        else:
            return DocumentDetailSerializer


    def create(self, request, *args, **kwargs):
        print(request.data)
        tags_raw = request.data.get('tags')
        if isinstance(tags_raw, str):
            try:
                request.data._mutable = True
                request.data['tags'] = json.loads(tags_raw)[0]
            except Exception:
                pass
 
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) 

        doc_info = serializer.validated_data.get("document")
        doc_name = doc_info["name"]
        doc_data = doc_info["data"]
        mime_type = doc_info["mime_type"]
        checksum = doc_info["checksum"]

        correspondent_id = serializer.validated_data.get("correspondent")
        document_type_id = serializer.validated_data.get("document_type")
        tag_ids = serializer.validated_data.get("tags")
        title = serializer.validated_data.get("title")
        created = serializer.validated_data.get("created")

        project = serializer.validated_data.get("project")

        existing_document = Document.objects.filter(checksum=checksum).first()
        if existing_document:
            return Response(
                {
                    "status": "duplicate", 
                    "message": "This document already exists in the system", 
                    "id": existing_document.id
                },
                status=status.HTTP_200_OK
            )

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
            project=project,
            mime_type=mime_type,
            storage_type=Document.STORAGE_TYPE_UNENCRYPTED,
            checksum=checksum
        )

        if tag_ids:
            document.tags.set(tag_ids)

        
        process_document.delay(document.id)

        return Response(
            {"status": "success", "id": document.id}, 
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        
        tags_raw = request.data.get('tags')
        if isinstance(tags_raw, str):
            try:
                request.data._mutable = True
                request.data['tags'] = json.loads(tags_raw)[0]
            except Exception:
                pass
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        if 'correspondent' in serializer.validated_data:
            instance.correspondent_id = serializer.validated_data.get('correspondent')
        if 'document_type' in serializer.validated_data:
            instance.document_type_id = serializer.validated_data.get('document_type')
        if 'title' in serializer.validated_data:
            instance.title = serializer.validated_data.get('title')
        if 'created' in serializer.validated_data:
            instance.created = serializer.validated_data.get('created')
        if 'project' in serializer.validated_data:
            instance.project = serializer.validated_data.get('project')
        
        if 'tags' in serializer.validated_data:
            tag_ids = serializer.validated_data.get('tags')
            instance.tags.set(tag_ids)
        
        instance.save()
        
        return Response(
            DocumentDetailSerializer(instance).data,
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
        
    @extend_schema(
        description="Download the document's archive file",
        responses={
            200: OpenApiTypes.BINARY,
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
    )
    @action(detail=True, methods=['get'], url_path='download-archive')
    def download_archive(self, request, pk=None):
        document = self.get_object()
        if document.archive_file:
            response = FileResponse(document.archive_file)
            response['Content-Disposition'] = f'attachment; filename="{document.original_filename or "document"}"'
            return response
        return Response({"detail": "No archive file available"}, status=404)
    

    @extend_schema(
        description="Download the document's original file",
        responses={
            200: OpenApiTypes.BINARY
        },
    )
    @action(detail=True, methods=['get'], url_path='download-original')
    def download_original(self, request, pk=None):
        document = self.get_object()
        response = FileResponse(document.source_file)
        response['Content-Disposition'] = f'attachment; filename="{document.original_filename or "document"}"'
        return response

    @extend_schema(
        description="Get statistics about documents, projects, tags, and document types",
        responses={
            200: {"type": "object", "properties": {
                "total_projects": {"type": "integer"},
                "total_documents": {"type": "integer"},
                "total_tags": {"type": "integer"},
                "total_document_types": {"type": "integer"},
                "project_documents": {"type": "object", "additionalProperties": {"type": "integer"}}
            }}
        },
        parameters=[
            OpenApiParameter(name="project_id", description="Optional project ID to get document count for a specific project", required=False, type=int)
        ]
    )
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        # Count total projects, documents, tags, and document types
        total_projects = Project.objects.count()
        total_documents = Document.objects.count()
        total_tags = Tag.objects.count()
        total_document_types = DocumentType.objects.count()
        
        # Get project documents count
        project_documents = {}
        
        # If project_id is provided, get count for that specific project
        project_id = request.query_params.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                doc_count = Document.objects.filter(project=project).count()
                project_documents[project.title] = doc_count
            except Project.DoesNotExist:
                return Response({"detail": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get count for all projects
            projects = Project.objects.all()
            for project in projects:
                doc_count = Document.objects.filter(project=project).count()
                project_documents[project.id] = doc_count
        
        return Response({
            "total_projects": total_projects,
            "total_documents": total_documents,
            "total_tags": total_tags,
            "total_document_types": total_document_types,
            "project_documents": project_documents
        })


    