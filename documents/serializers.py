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

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'name']
        read_only_fileds = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'descpription', 'status', 'status_display', 'start_date']
        read_only_fileds = ['id']

    def get_status_display(self, obj):
        return obj.get_status_display()

class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title',]
        read_only_fileds = ['id']

class ProjectDocumentSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'status', 'start_date',]
        read_only_fileds = ['id']

    def get_documents(self, obj):
        documents = obj.documents.all()
        serializer = DocumentSeralizer(documents, many=True)
        return serializer.data


class CorrespondentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Correspondent
        fields = ['id', 'name']
        read_only_fileds = ['id']


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fileds = ['id']




class DocumentSeralizer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'document_type', 'tags', 'correspondent']
        read_only_fileds = ['id']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'note',]
        read_only_fileds = ['id']