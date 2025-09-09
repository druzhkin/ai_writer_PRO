"""
Utility functions for file handling and validation.
"""

import os
import hashlib
import mimetypes
from typing import Optional, List, Tuple
from pathlib import Path
import magic


def validate_file_type(filename: str, mime_type: str, allowed_types: List[str]) -> bool:
    """
    Validate if a file type is allowed.
    
    Args:
        filename: Name of the file
        mime_type: MIME type of the file
        allowed_types: List of allowed MIME types
        
    Returns:
        True if file type is allowed, False otherwise
    """
    # Check MIME type
    if mime_type not in allowed_types:
        return False
    
    # Check file extension
    file_ext = Path(filename).suffix.lower()
    allowed_extensions = {
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.rtf': 'application/rtf'
    }
    
    if file_ext in allowed_extensions:
        expected_mime = allowed_extensions[file_ext]
        if mime_type != expected_mime:
            return False
    
    return True


def get_file_mime_type(file_path: str) -> Optional[str]:
    """
    Get MIME type of a file using python-magic.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type or None if cannot determine
    """
    try:
        mime = magic.from_file(file_path, mime=True)
        return mime
    except Exception:
        # Fallback to mimetypes module
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type


def get_file_mime_type_from_content(content: bytes) -> Optional[str]:
    """
    Get MIME type from file content.
    
    Args:
        content: File content as bytes
        
    Returns:
        MIME type or None if cannot determine
    """
    try:
        mime = magic.from_buffer(content, mime=True)
        return mime
    except Exception:
        return None


def calculate_file_hash(content: bytes, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file content.
    
    Args:
        content: File content as bytes
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
    """
    if algorithm == 'sha256':
        return hashlib.sha256(content).hexdigest()
    elif algorithm == 'md5':
        return hashlib.md5(content).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(content).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed_file'
    
    return filename


def is_safe_file(filename: str, content: bytes) -> Tuple[bool, str]:
    """
    Check if a file is safe to process.
    
    Args:
        filename: Name of the file
        content: File content as bytes
        
    Returns:
        Tuple of (is_safe, reason)
    """
    # Check file size
    if len(content) == 0:
        return False, "File is empty"
    
    # Check for suspicious file extensions
    suspicious_extensions = {'.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar'}
    file_ext = Path(filename).suffix.lower()
    if file_ext in suspicious_extensions:
        return False, f"Suspicious file extension: {file_ext}"
    
    # Check MIME type consistency
    detected_mime = get_file_mime_type_from_content(content)
    if detected_mime:
        # Check if detected MIME type matches expected types
        allowed_mimes = {
            'text/plain',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'application/rtf'
        }
        if detected_mime not in allowed_mimes:
            return False, f"Unsupported MIME type: {detected_mime}"
    
    # Check for embedded scripts or executables in content
    if b'<script' in content.lower() or b'javascript:' in content.lower():
        return False, "File contains embedded scripts"
    
    return True, "File is safe"


def get_file_size_human_readable(size_bytes: int) -> str:
    """
    Convert file size to human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_file_size(content: bytes, max_size: int) -> Tuple[bool, str]:
    """
    Validate file size against maximum allowed size.
    
    Args:
        content: File content as bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        Tuple of (is_valid, message)
    """
    file_size = len(content)
    if file_size > max_size:
        max_size_human = get_file_size_human_readable(max_size)
        file_size_human = get_file_size_human_readable(file_size)
        return False, f"File size ({file_size_human}) exceeds maximum allowed size ({max_size_human})"
    
    return True, "File size is valid"


def extract_file_metadata(filename: str, content: bytes) -> dict:
    """
    Extract metadata from file.
    
    Args:
        filename: Name of the file
        content: File content as bytes
        
    Returns:
        Dictionary of file metadata
    """
    metadata = {
        "filename": filename,
        "size_bytes": len(content),
        "size_human": get_file_size_human_readable(len(content)),
        "mime_type": get_file_mime_type_from_content(content),
        "file_hash": calculate_file_hash(content),
        "extension": Path(filename).suffix.lower(),
        "basename": Path(filename).stem
    }
    
    return metadata


def is_text_file(mime_type: str) -> bool:
    """
    Check if a file is a text-based file.
    
    Args:
        mime_type: MIME type of the file
        
    Returns:
        True if file is text-based
    """
    text_mimes = {
        'text/plain',
        'text/html',
        'text/css',
        'text/javascript',
        'application/json',
        'application/xml',
        'text/xml'
    }
    
    return mime_type in text_mimes


def is_document_file(mime_type: str) -> bool:
    """
    Check if a file is a document file.
    
    Args:
        mime_type: MIME type of the file
        
    Returns:
        True if file is a document
    """
    document_mimes = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'application/rtf',
        'text/plain'
    }
    
    return mime_type in document_mimes


def get_safe_temp_filename(original_filename: str, prefix: str = "temp_") -> str:
    """
    Generate a safe temporary filename.
    
    Args:
        original_filename: Original filename
        prefix: Prefix for temporary filename
        
    Returns:
        Safe temporary filename
    """
    # Get file extension
    ext = Path(original_filename).suffix
    
    # Generate unique filename
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{prefix}{unique_id}{ext}"
