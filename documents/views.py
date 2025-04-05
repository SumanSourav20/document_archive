from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from pathlib import Path
from django.conf import settings

from documents.serializers import (
    TagSerializer,
    CorrespondentSerializer,
    DocumentTypeSerializer,
    DocumentDetailSerializer,
    PostDocumentSerializer,
    ProjectSerializer,
)

from documents.serializers import (
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
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    def get_serializer(self, *args, **kwargs):
        pass


class CorrespondentViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = CorrespondentSerializer


class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    

class DocumentDetailViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer


class PostDocumentView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = PostDocumentSerializer
    queryset = Document.objects.all()
    permission_classes=[AllowAny]

    def get_serializer(self, data):
        return self.serializer_class(data=data)

    def post(self, request, *args, **kwargs):
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