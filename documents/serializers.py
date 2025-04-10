from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from documents.models import (
    Document,
    Project,
    DocumentType,
    Tag,
    Correspondent,
    Note,
    StoragePath,
)

from documents.validators import hex_color_validator

import magic
import hashlib

User = get_user_model()

class DocumentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DocumentType
        fields = ["id", "name"]
        read_only_fileds = ["id"]


class ProjectSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "title", "description", "status", "status_display", "start_date"]
        read_only_fileds = ["id"]

    def get_status_display(self, obj):
        return obj.get_status_display()

class ProjectListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ["id", "title", "description",]
        read_only_fileds = ["id"]

class ProjectDocumentSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "title", "description", "status", "start_date", "documents"]
        read_only_fields = ["id"]

    def get_documents(self, obj):
        documents = obj.documents.all()
        serializer = DocumentListSerializer(documents, many=True)
        return serializer.data


class CorrespondentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Correspondent
        fields = ["id", "name"]
        read_only_fileds = ["id"]


class TagSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        max_length=7,
        validators=[hex_color_validator],
    )

    class Meta:
        model = Tag
        fields = ["id", "name", "color"]
        read_only_fileds = ["id",]


class DocumentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ["id", "title", "tags", "created_date", "page_count", "thumbnail_str"]


class CorrespondentField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Correspondent.objects.all()


class TagsField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Tag.objects.all()
    

class DocumentTypeField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return DocumentType.objects.all()


class StoragePathField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return StoragePath.objects.all()
    

class ProjectField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Project.objects.all()
    
class NotesSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(),
        label="Document",
        write_only=True,
    )
    
    class Meta:
        model = Note
        fields = ["id", "created", "note", "document", "user",]
        ordering = ["-created"]
        read_only_fields = ["id","created", "user"]

    
class DocumentDetailSerializer(serializers.ModelSerializer):
    project = ProjectField(allow_null=True)
    correspondent = CorrespondentField(allow_null=True)
    tags = TagsField(many=True)
    document_type = DocumentTypeField(allow_null=True)
    notes = NotesSerializer(many=True, required=False, read_only=True)
    added_date = serializers.SerializerMethodField()
    modified_date = serializers.SerializerMethodField()
    project_display = ProjectListSerializer(read_only=True)

    class Meta:
        model = Document
        fields = ["id", "title", "tags", "created_date", "page_count", "correspondent", "added_date", "modified_date", "project", "project_display", "document_type", "notes",]
        read_only_fields = ["page_count"]

    def get_added_date(self, obj):
        return timezone.localdate(obj.added)
    
    def get_modified_date(self, obj):
        return timezone.localdate(obj.modified)
        
class PostDocumentSerializer(serializers.Serializer):
    created = serializers.DateTimeField(
        label="Created",
        allow_null=True,
        write_only=True,
        required=False,
    )

    document = serializers.FileField(
        label="Document",
        write_only=True,
    )

    title = serializers.CharField(
        label="Title",
        write_only=True,
        required=False,
    )

    correspondent = serializers.PrimaryKeyRelatedField(
        queryset=Correspondent.objects.all(),
        label="Correspondent",
        allow_null=True,
        write_only=True,
        required=False,
    )

    document_type = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.all(),
        label="Document type",
        allow_null=True,
        write_only=True,
        required=False,
    )

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        label="Tags",
        write_only=True,
        required=False,
    )

    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        label="Project",
        write_only=True,
        required=False,
    )

    SUPPORTED_MIME_TYPES = [
        # PDF
        'application/pdf',
        # Office documents
        'application/msword',
        'application/vnd.ms-excel',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet',
        'application/vnd.oasis.opendocument.presentation',
        # Images
        'image/jpeg',
        'image/png',
        'image/tiff',
        'image/gif',
        'image/webp',
        'image/svg+xml',
    ]
    
    def validate_document(self, document):
        document_data = document.file.read()
        
        mime_type = magic.from_buffer(document_data, mime=True)
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            raise serializers.ValidationError(
                f"Unsupported file type: {mime_type}. Only office documents, PDFs, and images are supported."
            )
            
        checksum = hashlib.md5(document_data).hexdigest()
            
        return {
            "name": document.name,
            "data": document_data,
            "mime_type": mime_type,
            "checksum": checksum
        }

    def validate_correspondent(self, correspondent):
        if correspondent:
            return correspondent.id
        else:
            return None

    def validate_document_type(self, document_type):
        if document_type:
            return document_type.id
        else:
            return None

    def validate_tags(self, tags):
        if tags: 
            return [tag.id for tag in tags]
        else:
            return None
        
