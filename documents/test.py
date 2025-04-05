import os
import pytest
import hashlib
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from your_app.models import Document, Correspondent, DocumentType, Tag
from your_app.serializers import PostDocumentSerializer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_correspondent():
    return Correspondent.objects.create(name="Test Correspondent")


@pytest.fixture
def sample_document_type():
    return DocumentType.objects.create(name="Test Document Type")


@pytest.fixture
def sample_tag():
    return Tag.objects.create(name="Test Tag")


@pytest.fixture
def sample_document_data():
    content = b"This is a test document content"
    doc = SimpleUploadedFile(
        name="test_document.pdf",
        content=content,
        content_type="application/pdf"
    )
    return {
        "document": doc,
        "title": "Test Document",
        "created": "2025-04-05",
    }


@pytest.mark.django_db
class TestPostDocumentView:
    def test_create_document_success(
        self, api_client, sample_correspondent, sample_document_type, 
        sample_tag, sample_document_data, settings
    ):
        # Setup
        url = reverse("documents-upload")  # Adjust to your actual URL name
        
        # Update sample data with foreign keys
        sample_document_data["correspondent"] = sample_correspondent.id
        sample_document_data["document_type"] = sample_document_type.id
        sample_document_data["tags"] = [sample_tag.id]
        
        # Mock the magic module to return a predictable mime type
        with patch("magic.from_buffer", return_value="application/pdf"), \
             patch("pathlib.Path.exists", return_value=False), \
             patch("builtins.open", create=True) as mock_open:
            
            # Mock file open
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Execute
            response = api_client.post(url, sample_document_data, format="multipart")
            
            # Assert response
            assert response.status_code == status.HTTP_201_CREATED
            assert "id" in response.data
            assert response.data["status"] == "success"
            
            # Verify document was created in the database
            document = Document.objects.get(id=response.data["id"])
            assert document.title == sample_document_data["title"]
            assert document.correspondent_id == sample_correspondent.id
            assert document.document_type_id == sample_document_type.id
            assert sample_tag.id in document.tag_ids
            
            # Verify the checksum calculation and file handling
            expected_content = sample_document_data["document"].read()
            expected_checksum = hashlib.md5(expected_content).hexdigest()
            assert document.checksum == expected_checksum
            assert document.original_filename == "test_document.pdf"
            assert document.mime_type == "application/pdf"
            
            # Verify file write operation
            mock_file.write.assert_called_once_with(expected_content)
    
    def test_create_document_invalid_data(self, api_client):
        # Test with missing required fields
        url = reverse("documents-upload")  # Adjust to your actual URL name
        
        # Empty data
        response = api_client.post(url, {}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_file_already_exists(
        self, api_client, sample_correspondent, sample_document_type, 
        sample_document_data, settings
    ):
        # Test case when file already exists
        url = reverse("documents-upload")
        
        sample_document_data["correspondent"] = sample_correspondent.id
        sample_document_data["document_type"] = sample_document_type.id
        
        with patch("magic.from_buffer", return_value="application/pdf"), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", create=True) as mock_open:
            
            response = api_client.post(url, sample_document_data, format="multipart")
            
            assert response.status_code == status.HTTP_201_CREATED
            # Verify file wasn't written
            mock_open.assert_not_called()