"""
Tests for file service functionality.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from io import BytesIO

from app.services.file_service import FileService
from app.services.text_extraction_service import TextExtractionService
from app.core.config import settings


class TestFileService:
    """Test file service operations."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def file_service(self, mock_db):
        """Create file service instance."""
        return FileService(mock_db)
    
    @pytest.fixture
    def sample_file_content(self):
        """Sample file content for testing."""
        return b"This is sample text content for testing file operations."
    
    @pytest.fixture
    def sample_upload_file(self, sample_file_content):
        """Create a mock upload file."""
        file_obj = BytesIO(sample_file_content)
        upload_file = UploadFile(
            filename="test.txt",
            file=file_obj,
            size=len(sample_file_content)
        )
        return upload_file
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_success(self, file_service, sample_upload_file):
        """Test successful file validation."""
        organization_id = uuid.uuid4()
        
        is_valid, error_message, metadata = await file_service.validate_upload_file(
            sample_upload_file, organization_id
        )
        
        assert is_valid is True
        assert error_message == ""
        assert "mime_type" in metadata
        assert "size_bytes" in metadata
        assert metadata["organization_id"] == str(organization_id)
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_too_large(self, file_service):
        """Test file validation with oversized file."""
        # Create a large file content
        large_content = b"x" * (settings.MAX_FILE_SIZE + 1)
        file_obj = BytesIO(large_content)
        upload_file = UploadFile(
            filename="large.txt",
            file=file_obj,
            size=len(large_content)
        )
        
        organization_id = uuid.uuid4()
        
        is_valid, error_message, metadata = await file_service.validate_upload_file(
            upload_file, organization_id
        )
        
        assert is_valid is False
        assert "exceeds maximum allowed size" in error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_unsupported_type(self, file_service):
        """Test file validation with unsupported file type."""
        # Create a file with unsupported content
        content = b"executable content"
        file_obj = BytesIO(content)
        upload_file = UploadFile(
            filename="test.exe",
            file=file_obj,
            size=len(content)
        )
        
        organization_id = uuid.uuid4()
        
        is_valid, error_message, metadata = await file_service.validate_upload_file(
            upload_file, organization_id
        )
        
        assert is_valid is False
        assert "not allowed" in error_message or "suspicious" in error_message
    
    @patch('app.services.file_service.boto3.client')
    @pytest.mark.asyncio
    async def test_upload_to_s3_success(self, mock_boto_client, file_service, sample_file_content):
        """Test successful S3 upload."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        file_service.s3_client = mock_s3
        
        organization_id = uuid.uuid4()
        style_profile_id = uuid.uuid4()
        
        success, message, s3_key = await file_service.upload_to_s3(
            sample_file_content, "test.txt", organization_id, style_profile_id
        )
        
        assert success is True
        assert "uploaded successfully" in message
        assert s3_key is not None
        assert str(organization_id) in s3_key
        assert str(style_profile_id) in s3_key
        
        # Verify S3 put_object was called
        mock_s3.put_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_to_s3_no_client(self, file_service, sample_file_content):
        """Test S3 upload when client is not configured."""
        file_service.s3_client = None
        
        organization_id = uuid.uuid4()
        
        success, message, s3_key = await file_service.upload_to_s3(
            sample_file_content, "test.txt", organization_id
        )
        
        assert success is False
        assert "S3 not configured" in message
        assert s3_key is None
    
    @patch('app.services.file_service.boto3.client')
    @pytest.mark.asyncio
    async def test_delete_from_s3_success(self, mock_boto_client, file_service):
        """Test successful S3 deletion."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        file_service.s3_client = mock_s3
        
        s3_key = "test/path/file.txt"
        
        success, message = await file_service.delete_from_s3(s3_key)
        
        assert success is True
        assert "deleted successfully" in message
        
        # Verify S3 delete_object was called
        mock_s3.delete_object.assert_called_once_with(
            Bucket=settings.AWS_S3_BUCKET,
            Key=s3_key
        )
    
    @patch('app.services.file_service.boto3.client')
    @pytest.mark.asyncio
    async def test_get_s3_presigned_url_success(self, mock_boto_client, file_service):
        """Test successful presigned URL generation."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = "https://example.com/presigned-url"
        mock_boto_client.return_value = mock_s3
        file_service.s3_client = mock_s3
        
        s3_key = "test/path/file.txt"
        
        success, message, presigned_url = await file_service.get_s3_presigned_url(s3_key)
        
        assert success is True
        assert "generated" in message
        assert presigned_url == "https://example.com/presigned-url"
        
        # Verify generate_presigned_url was called
        mock_s3.generate_presigned_url.assert_called_once()
    
    @patch('app.services.file_service.boto3.client')
    @pytest.mark.asyncio
    async def test_check_s3_file_exists_true(self, mock_boto_client, file_service):
        """Test checking if S3 file exists (exists)."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        file_service.s3_client = mock_s3
        
        s3_key = "test/path/file.txt"
        
        exists = await file_service.check_s3_file_exists(s3_key)
        
        assert exists is True
        
        # Verify head_object was called
        mock_s3.head_object.assert_called_once_with(
            Bucket=settings.AWS_S3_BUCKET,
            Key=s3_key
        )
    
    @patch('app.services.file_service.boto3.client')
    @pytest.mark.asyncio
    async def test_check_s3_file_exists_false(self, mock_boto_client, file_service):
        """Test checking if S3 file exists (doesn't exist)."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.head_object.side_effect = Exception("Not found")
        mock_boto_client.return_value = mock_s3
        file_service.s3_client = mock_s3
        
        s3_key = "test/path/file.txt"
        
        exists = await file_service.check_s3_file_exists(s3_key)
        
        assert exists is False


class TestTextExtractionService:
    """Test text extraction service operations."""
    
    @pytest.fixture
    def text_extraction_service(self):
        """Create text extraction service instance."""
        return TextExtractionService()
    
    @pytest.mark.asyncio
    async def test_extract_text_plain_success(self, text_extraction_service):
        """Test successful plain text extraction."""
        content = b"This is plain text content for testing."
        mime_type = "text/plain"
        
        success, message, extracted_text, metadata = await text_extraction_service.extract_text(
            content, mime_type, "test.txt"
        )
        
        assert success is True
        assert "extracted successfully" in message
        assert extracted_text == "This is plain text content for testing."
        assert "encoding" in metadata
        assert "extraction_method" in metadata
    
    @pytest.mark.asyncio
    async def test_extract_text_unsupported_format(self, text_extraction_service):
        """Test extraction with unsupported format."""
        content = b"Some content"
        mime_type = "application/unsupported"
        
        success, message, extracted_text, metadata = await text_extraction_service.extract_text(
            content, mime_type, "test.unsupported"
        )
        
        assert success is False
        assert "Unsupported file format" in message
        assert extracted_text is None
        assert metadata is None
    
    @pytest.mark.asyncio
    async def test_extract_text_empty_content(self, text_extraction_service):
        """Test extraction with empty content."""
        content = b""
        mime_type = "text/plain"
        
        success, message, extracted_text, metadata = await text_extraction_service.extract_text(
            content, mime_type, "empty.txt"
        )
        
        assert success is True
        assert extracted_text == ""
        assert metadata is not None
    
    @pytest.mark.asyncio
    async def test_extract_text_with_fallback(self, text_extraction_service):
        """Test text extraction with fallback methods."""
        content = b"This is test content for fallback testing."
        mime_type = "text/plain"
        
        success, message, extracted_text, metadata = await text_extraction_service.extract_text_with_fallback(
            content, mime_type, "test.txt"
        )
        
        assert success is True
        assert extracted_text is not None
        assert metadata is not None
    
    def test_post_process_text(self, text_extraction_service):
        """Test text post-processing."""
        # Test with excessive whitespace
        text = "This is   a   test\n\n\n\nwith   multiple   spaces   and\n\n\nnewlines."
        processed = text_extraction_service._post_process_text(text)
        
        # Should clean up whitespace
        assert "   " not in processed  # No multiple spaces
        assert "\n\n\n" not in processed  # No multiple newlines
        assert processed.strip() == processed  # No leading/trailing whitespace
    
    def test_get_text_metadata(self, text_extraction_service):
        """Test text metadata extraction."""
        text = "This is a test sentence. This is another sentence with more words."
        metadata = text_extraction_service._get_text_metadata(text)
        
        assert "character_count" in metadata
        assert "word_count" in metadata
        assert "line_count" in metadata
        assert "sentence_count" in metadata
        assert metadata["word_count"] > 0
        assert metadata["sentence_count"] > 0


class TestFileUtils:
    """Test file utility functions."""
    
    def test_validate_file_type_allowed(self):
        """Test file type validation with allowed types."""
        from app.utils.file_utils import validate_file_type
        
        allowed_types = ["text/plain", "application/pdf"]
        
        # Test allowed types
        assert validate_file_type("test.txt", "text/plain", allowed_types) is True
        assert validate_file_type("test.pdf", "application/pdf", allowed_types) is True
    
    def test_validate_file_type_not_allowed(self):
        """Test file type validation with not allowed types."""
        from app.utils.file_utils import validate_file_type
        
        allowed_types = ["text/plain", "application/pdf"]
        
        # Test not allowed types
        assert validate_file_type("test.exe", "application/octet-stream", allowed_types) is False
        assert validate_file_type("test.jpg", "image/jpeg", allowed_types) is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from app.utils.file_utils import sanitize_filename
        
        # Test dangerous characters
        dangerous_filename = "test<>:\"/\\|?*.txt"
        sanitized = sanitize_filename(dangerous_filename)
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert "|" not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized
    
    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        from app.utils.file_utils import calculate_file_hash
        
        content = b"test content"
        
        # Test SHA256
        sha256_hash = calculate_file_hash(content, "sha256")
        assert len(sha256_hash) == 64  # SHA256 hex length
        
        # Test MD5
        md5_hash = calculate_file_hash(content, "md5")
        assert len(md5_hash) == 32  # MD5 hex length
        
        # Test that same content produces same hash
        sha256_hash2 = calculate_file_hash(content, "sha256")
        assert sha256_hash == sha256_hash2
    
    def test_get_file_size_human_readable(self):
        """Test human readable file size conversion."""
        from app.utils.file_utils import get_file_size_human_readable
        
        # Test bytes
        assert get_file_size_human_readable(0) == "0 B"
        assert get_file_size_human_readable(1023) == "1023.0 B"
        
        # Test KB
        assert get_file_size_human_readable(1024) == "1.0 KB"
        assert get_file_size_human_readable(1536) == "1.5 KB"
        
        # Test MB
        assert get_file_size_human_readable(1024 * 1024) == "1.0 MB"
        assert get_file_size_human_readable(1024 * 1024 * 1.5) == "1.5 MB"
    
    def test_is_safe_file(self):
        """Test file safety checking."""
        from app.utils.file_utils import is_safe_file
        
        # Test safe file
        is_safe, reason = is_safe_file("test.txt", b"safe content")
        assert is_safe is True
        assert reason == "File is safe"
        
        # Test empty file
        is_safe, reason = is_safe_file("empty.txt", b"")
        assert is_safe is False
        assert "empty" in reason
        
        # Test suspicious extension
        is_safe, reason = is_safe_file("test.exe", b"executable content")
        assert is_safe is False
        assert "suspicious" in reason
