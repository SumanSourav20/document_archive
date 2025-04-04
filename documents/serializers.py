from django.utils import timezone
from rest_framework import serializers

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


class DocumentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ["id", "name"]
        read_only_fileds = ["id"]


class ProjectSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "title", "descpription", "status", "status_display", "start_date"]
        read_only_fileds = ["id"]

    def get_status_display(self, obj):
        return obj.get_status_display()

class ProjectListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ["id", "title", "description"]
        read_only_fileds = ["id"]

class ProjectDocumentSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "title", "description", "status", "start_date", "documents"]
        read_only_fileds = ["id"]

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
        fields = ["id", "name",]
        read_only_fileds = ["id",]


class DocumentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ["id", "title", "tags", "created_date", "page_count", "thumbnail_file"]


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
    
    class Meta:
        model = Note
        fields = ["id", "created", "note",]
        ordering = ["-created"]

    
class DocumentDetailSerializer(serializers.ModelSerializer):
    project = ProjectField(allow_null=True)
    correspondent = CorrespondentField(allow_null=True)
    tags = TagsField(many=True)
    document_type = DocumentTypeField(allow_null=True)
    notes = NotesSerializer(many=True, required=False, read_only=True)
    # storage_path = StoragePathField(allow_null=True)
    added_date = serializers.SerializerMethodField()
    modified_date = serializers.SerializerMethodField()
    project_display = ProjectListSerializer(read_only=True)

    class Meta:
        model = Document
        fields = ["id", "title", "tags", "created_date", "page_count", "correspondent", "added_date", "modified_date", "project", "project_display", "document_type", "notes"]
        read_only_fields = ["page_count"]

    def get_added_date(self, obj):
        return timezone.localdate(obj.added)
    
    def get_modified_date(self, obj):
        return timezone.localdate(obj.modified)
        
