import os
import subprocess
from pathlib import Path
from PIL import Image
import magic
from celery import shared_task
from django.conf import settings
import logging
from documents.models import Document
import hashlib

logger = logging.getLogger(__name__)

@shared_task
def process_document(document_id):
    """
    Main task that processes a document after upload:
    1. Generate PDF/A archive
    2. Generate thumbnail
    """
    
    try:
        document = Document.objects.get(pk=document_id)
        
        # Generate PDF/A first
        success = generate_pdf_archive(document)
        if success:
            # Then generate thumbnail from the PDF/A
            generate_thumbnail(document)
        
        return {"status": "success", "document_id": document_id}
    except Document.DoesNotExist:
        logger.error(f"Document with ID {document_id} not found")
        return {"status": "error", "message": f"Document with ID {document_id} not found"}
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def generate_pdf_archive(document):
    """
    Convert document to PDF/A format using LibreOffice and GhostScript
    """
    
    if isinstance(document, int):
        document = Document.objects.get(pk=document)
    
    source_path = document.source_path
    source_mime = document.mime_type
    
    # Create output directory if it doesn't exist
    os.makedirs(settings.ARCHIVE_DIR, exist_ok=True)
    
    # Base filename for the archive (without extension)
    archive_base = f"{document.checksum}_archive"
    final_output_path = Path(settings.ARCHIVE_DIR) / f"{archive_base}.pdf"
    
    try:
        # If source is already PDF, convert directly with GhostScript
        if source_mime == 'application/pdf':
            pdf_path = source_path
        else:
            # Convert to PDF with LibreOffice first
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', str(settings.ARCHIVE_DIR),
                str(source_path)
            ], check=True)
            
            # LibreOffice output filename
            lo_output = Path(settings.ARCHIVE_DIR) / f"{Path(source_path).stem}.pdf"
            pdf_path = lo_output
        
        # Convert to PDF/A using GhostScript
        subprocess.run([
            'gs', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dSAFER',
            '-sDEVICE=pdfwrite',
            '-sColorConversionStrategy=UseDeviceIndependentColor',
            '-dPDFACompatibilityPolicy=1',
            f'-sOutputFile={str(final_output_path)}',
            str(pdf_path)
        ], check=True)
        
        # Clean up temporary PDF if it was created
        if source_mime != 'application/pdf' and pdf_path != source_path:
            os.remove(pdf_path)
        
        # Update document model with archive information
        with open(final_output_path, 'rb') as f:
            archive_data = f.read()
            archive_checksum = document.archive_checksum = hashlib.md5(archive_data).hexdigest()
        
        document.archive_filename = f"{archive_base}.pdf"
        document.archive_checksum = archive_checksum
        document.save(update_fields=['archive_filename', 'archive_checksum'])
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to generate PDF/A for document {document.id}: {str(e)}")
        return False

@shared_task
def generate_thumbnail(document):
    """
    Generate thumbnail from the first page of the PDF/A archive
    """
    
    if isinstance(document, int):
        document = Document.objects.get(pk=document)
    
    # Ensure archive exists
    if not document.has_archive_version:
        logger.error(f"Cannot generate thumbnail: Document {document.id} has no archive version")
        return False
    
    try:
        # Create thumbnail directory if it doesn't exist
        os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
        
        # Use the archive file to generate the thumbnail
        archive_path = document.archive_path
        thumbnail_path = document.thumbnail_path
        
        # Convert first page of PDF to image using GhostScript
        temp_png = Path(settings.THUMBNAIL_DIR) / f"{document.pk:07}_temp.png"
        subprocess.run([
            'gs', '-dNOPAUSE', '-dBATCH', '-dSAFER',
            '-sDEVICE=png16m',
            '-dFirstPage=1', '-dLastPage=1',
            '-r150',
            f'-sOutputFile={str(temp_png)}',
            str(archive_path)
        ], check=True)
        
        # Resize and convert to WebP format
        with Image.open(temp_png) as img:
            img.thumbnail((500, 500))  # Resize to thumbnail size
            img.save(str(thumbnail_path), 'WEBP', quality=75)
        
        # Clean up temporary PNG
        os.remove(temp_png)
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for document {document.id}: {str(e)}")
        return False