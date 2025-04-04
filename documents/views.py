from rest_framework import viewsets

from documents.serializers import (
    TagSerializer,
    CorrespondentSerializer,
    DocumentTypeSerializer,
    DocumentDetailSerializer,
)

from documents.serializers import (
    Document,
    Project,
    Tag,
    DocumentType,
    Note,
    Correspondent,
)


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