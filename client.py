import requests
import argparse
import os
import sys
from datetime import datetime


class DocumentApiClient:
    """Client for testing the Document Upload API endpoint."""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.upload_endpoint = f"{self.base_url}/api/document/"  # Adjust the path as needed
    
    def upload_document(self, file_path, title=None, correspondent_id=None, 
                       document_type_id=None, tag_ids=None, created=None):
        """
        Upload a document to the API endpoint.
        
        Args:
            file_path (str): Path to the file to upload
            title (str, optional): Title for the document
            correspondent_id (int, optional): ID of correspondent
            document_type_id (int, optional): ID of document type
            tag_ids (list, optional): List of tag IDs
            created (str, optional): Created date in YYYY-MM-DD format
            
        Returns:
            dict: API response data
        """
        # Validate file exists
        if not os.path.isfile(file_path):
            print(f"Error: File {file_path} not found")
            return None
            
        # Prepare file for upload
        filename = os.path.basename(file_path)
        
        # Prepare form data
        data = {}
        files = {'document': (filename, open(file_path, 'rb'))}
        
        # Add optional parameters if provided
        if title:
            data['title'] = title
        if correspondent_id:
            data['correspondent'] = correspondent_id
        if document_type_id:
            data['document_type'] = document_type_id
        if tag_ids:
            # Handle multiple tags if provided
            for tag_id in tag_ids:
                data.setdefault('tags', []).append(tag_id)
        if created:
            data['created'] = created
        else:
            # Use current date as default
            data['created'] = datetime.now().strftime('%Y-%m-%d')
            
        try:
            # Make the POST request
            response = requests.post(
                self.upload_endpoint,
                data=data,
                files=files
            )
            
            # Close the file
            files['document'][1].close()
            
            # Process response
            if response.status_code == 201:
                print(f"Document uploaded successfully! Document ID: {response.json()['id']}")
                return response.json()
            else:
                print(f"Error uploading document. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Upload a document to the API')
    parser.add_argument('--url', required=True, help='Base URL of the API')
    parser.add_argument('--file', required=True, help='Path to the file to upload')
    parser.add_argument('--title', help='Title for the document')
    parser.add_argument('--correspondent', type=int, help='Correspondent ID')
    parser.add_argument('--document-type', type=int, help='Document Type ID')
    parser.add_argument('--tags', type=int, nargs='+', help='Tag IDs')
    parser.add_argument('--created', help='Created date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    client = DocumentApiClient(args.url)
    result = client.upload_document(
        args.file,
        title=args.title,
        correspondent_id=args.correspondent,
        document_type_id=args.document_type,
        tag_ids=args.tags,
        created=args.created
    )
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()