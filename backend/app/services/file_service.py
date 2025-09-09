"""
File service for handling file uploads, storage, and management.
"""

import os
import uuid
from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.utils.file_utils import (
    validate_file_type, get_file_mime_type_from_content, calculate_file_hash,
    sanitize_filename, is_safe_file, validate_file_size, extract_file_metadata
)


class FileService:
    """Service for file operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3_client = None
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client if credentials are available."""
        if all([
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
            settings.AWS_S3_BUCKET
        ]):
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
            except Exception as e:
                print(f"Failed to initialize S3 client: {e}")
                self.s3_client = None
    
    async def validate_upload_file(
        self, 
        file: UploadFile, 
        organization_id: uuid.UUID
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file
            organization_id: Organization ID
            
        Returns:
            Tuple of (is_valid, error_message, metadata)
        """
        try:
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Validate file size
            is_valid_size, size_message = validate_file_size(content, settings.MAX_FILE_SIZE)
            if not is_valid_size:
                return False, size_message, {}
            
            # Check if file is safe
            is_safe, safety_message = is_safe_file(file.filename or "unknown", content)
            if not is_safe:
                return False, safety_message, {}
            
            # Get MIME type
            mime_type = get_file_mime_type_from_content(content)
            if not mime_type:
                return False, "Cannot determine file type", {}
            
            # Validate file type
            if not validate_file_type(file.filename or "unknown", mime_type, settings.ALLOWED_FILE_TYPES):
                return False, f"File type {mime_type} is not allowed", {}
            
            # Extract metadata
            metadata = extract_file_metadata(file.filename or "unknown", content)
            metadata.update({
                "organization_id": str(organization_id),
                "upload_timestamp": str(uuid.uuid4()),
                "original_filename": file.filename
            })
            
            return True, "", metadata
            
        except Exception as e:
            return False, f"File validation failed: {str(e)}", {}
    
    async def upload_to_s3(
        self, 
        content: bytes, 
        filename: str, 
        organization_id: uuid.UUID,
        style_profile_id: Optional[uuid.UUID] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload file to S3.
        
        Args:
            content: File content
            filename: Filename
            organization_id: Organization ID
            style_profile_id: Optional style profile ID
            
        Returns:
            Tuple of (success, message, s3_key)
        """
        if not self.s3_client:
            return False, "S3 not configured", None
        
        try:
            # Generate S3 key
            sanitized_filename = sanitize_filename(filename)
            file_hash = calculate_file_hash(content)
            
            # Create S3 key with organization and style profile structure
            s3_key_parts = [settings.S3_STYLES_PREFIX, str(organization_id)]
            if style_profile_id:
                s3_key_parts.append(str(style_profile_id))
            s3_key_parts.append(f"{file_hash[:8]}_{sanitized_filename}")
            
            s3_key = "/".join(s3_key_parts)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Body=content,
                ContentType=self._get_content_type(filename),
                Metadata={
                    'organization_id': str(organization_id),
                    'file_hash': file_hash,
                    'original_filename': filename
                }
            )
            
            return True, "File uploaded successfully", s3_key
            
        except NoCredentialsError:
            return False, "AWS credentials not found", None
        except ClientError as e:
            return False, f"S3 upload failed: {str(e)}", None
        except Exception as e:
            return False, f"Upload failed: {str(e)}", None
    
    async def delete_from_s3(self, s3_key: str) -> Tuple[bool, str]:
        """
        Delete file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Tuple of (success, message)
        """
        if not self.s3_client:
            return False, "S3 not configured"
        
        try:
            self.s3_client.delete_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key
            )
            return True, "File deleted successfully"
            
        except ClientError as e:
            return False, f"S3 delete failed: {str(e)}"
        except Exception as e:
            return False, f"Delete failed: {str(e)}"
    
    async def get_s3_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate presigned URL for S3 object.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Tuple of (success, message, presigned_url)
        """
        if not self.s3_client:
            return False, "S3 not configured", None
        
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_S3_BUCKET, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return True, "Presigned URL generated", presigned_url
            
        except ClientError as e:
            return False, f"Failed to generate presigned URL: {str(e)}", None
        except Exception as e:
            return False, f"URL generation failed: {str(e)}", None
    
    async def check_s3_file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key
            )
            return True
            
        except ClientError:
            return False
        except Exception:
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get content type for filename.
        
        Args:
            filename: Filename
            
        Returns:
            Content type
        """
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    async def get_file_info(self, s3_key: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get file information from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Tuple of (success, message, file_info)
        """
        if not self.s3_client:
            return False, "S3 not configured", None
        
        try:
            response = self.s3_client.head_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key
            )
            
            file_info = {
                "size": response.get('ContentLength', 0),
                "content_type": response.get('ContentType', ''),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag', '').strip('"'),
                "metadata": response.get('Metadata', {})
            }
            
            return True, "File info retrieved", file_info
            
        except ClientError as e:
            return False, f"Failed to get file info: {str(e)}", None
        except Exception as e:
            return False, f"File info retrieval failed: {str(e)}", None
    
    async def list_organization_files(
        self, 
        organization_id: uuid.UUID,
        prefix: Optional[str] = None
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        List files for an organization.
        
        Args:
            organization_id: Organization ID
            prefix: Optional prefix filter
            
        Returns:
            Tuple of (success, message, file_list)
        """
        if not self.s3_client:
            return False, "S3 not configured", []
        
        try:
            # Build prefix
            search_prefix = f"{settings.S3_STYLES_PREFIX}/{organization_id}"
            if prefix:
                search_prefix += f"/{prefix}"
            
            response = self.s3_client.list_objects_v2(
                Bucket=settings.AWS_S3_BUCKET,
                Prefix=search_prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                file_info = {
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'],
                    "etag": obj['ETag'].strip('"')
                }
                files.append(file_info)
            
            return True, "Files listed successfully", files
            
        except ClientError as e:
            return False, f"Failed to list files: {str(e)}", []
        except Exception as e:
            return False, f"File listing failed: {str(e)}", []
