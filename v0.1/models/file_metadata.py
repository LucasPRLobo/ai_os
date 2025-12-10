"""
File Metadata Models
Pydantic models for representing file information and metadata.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from pathlib import Path
from typing import Optional


class FileMetadata(BaseModel):
    """
    Metadata for a single file.
    
    Contains basic file information, content preview, and optional metadata.
    """
    
    # Basic file information
    name: str = Field(
        ..., 
        description="File name with extension",
        examples=["invoice_2025.pdf", "vacation_photo.jpg"]
    )
    
    path: str = Field(
        ..., 
        description="Absolute path to the file",
        examples=["/home/user/Documents/invoice_2025.pdf"]
    )
    
    extension: str = Field(
        ..., 
        description="File extension including the dot",
        examples=[".pdf", ".jpg", ".txt"]
    )
    
    size: int = Field(
        ..., 
        description="File size in bytes",
        ge=0
    )
    
    modified_date: datetime = Field(
        ..., 
        description="Last modified timestamp"
    )
    
    created_date: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    
    # Content information
    content_preview: Optional[str] = Field(
        None,
        description="Preview of file content (first ~1000 chars for text files)",
        max_length=2000
    )
    
    content_type: str = Field(
        ...,
        description="Type of content",
        examples=["text", "image", "document", "video", "audio", "archive", "code", "unknown"]
    )
    
    # Optional metadata
    mime_type: Optional[str] = Field(
        None,
        description="MIME type of the file",
        examples=["application/pdf", "image/jpeg", "text/plain"]
    )
    
    parent_directory: str = Field(
        ...,
        description="Name of the parent directory",
        examples=["Documents", "Downloads", "Desktop"]
    )
    
    hash: Optional[str] = Field(
        None,
        description="File hash for deduplication (MD5 or SHA256)",
        examples=["5d41402abc4b2a76b9719d911017c592"]
    )
    
    @field_validator('extension')
    @classmethod
    def validate_extension(cls, v: str) -> str:
        """Ensure extension starts with a dot."""
        if v and not v.startswith('.'):
            return f'.{v}'
        return v
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Ensure content_type is lowercase."""
        return v.lower()
    
    def get_size_human(self) -> str:
        """
        Get human-readable file size.
        
        Returns:
            Formatted size string (e.g., "1.5 MB", "340 KB")
        """
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def is_text_file(self) -> bool:
        """Check if file is a text-based file."""
        text_types = {'text', 'code'}
        return self.content_type in text_types
    
    def is_media_file(self) -> bool:
        """Check if file is a media file (image, video, audio)."""
        media_types = {'image', 'video', 'audio'}
        return self.content_type in media_types
    
    def get_relative_path(self, base_path: str) -> str:
        """
        Get path relative to a base path.
        
        Args:
            base_path: Base directory path
            
        Returns:
            Relative path string
        """
        try:
            return str(Path(self.path).relative_to(base_path))
        except ValueError:
            return self.path
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "invoice_2025.pdf",
                "path": "/home/user/Documents/invoice_2025.pdf",
                "extension": ".pdf",
                "size": 245760,
                "modified_date": "2025-11-15T10:30:00",
                "created_date": "2025-11-15T10:30:00",
                "content_preview": "Invoice #12345\nDate: November 15, 2025...",
                "content_type": "document",
                "mime_type": "application/pdf",
                "parent_directory": "Documents",
                "hash": "5d41402abc4b2a76b9719d911017c592"
            }
        }


class BatchMetadata(BaseModel):
    """
    Metadata for a batch of files (e.g., a directory).
    
    Aggregates information about multiple files.
    """
    
    files: list[FileMetadata] = Field(
        ...,
        description="List of file metadata objects"
    )
    
    total_files: int = Field(
        ...,
        description="Total number of files in the batch",
        ge=0
    )
    
    total_size: int = Field(
        ...,
        description="Total size of all files in bytes",
        ge=0
    )
    
    source_path: Optional[str] = Field(
        None,
        description="Source directory path if batch came from a directory"
    )
    
    scanned_at: datetime = Field(
        default_factory=datetime.now,
        description="When the batch was scanned"
    )
    
    def get_total_size_human(self) -> str:
        """Get human-readable total size."""
        size = self.total_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def get_content_type_distribution(self) -> dict[str, int]:
        """
        Get distribution of content types.
        
        Returns:
            Dictionary mapping content_type to count
        """
        distribution: dict[str, int] = {}
        for file in self.files:
            content_type = file.content_type
            distribution[content_type] = distribution.get(content_type, 0) + 1
        return distribution
    
    def get_extension_distribution(self) -> dict[str, int]:
        """
        Get distribution of file extensions.
        
        Returns:
            Dictionary mapping extension to count
        """
        distribution: dict[str, int] = {}
        for file in self.files:
            ext = file.extension
            distribution[ext] = distribution.get(ext, 0) + 1
        return distribution
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "files": [],
                "total_files": 10,
                "total_size": 5242880,
                "source_path": "/home/user/Documents/project",
                "scanned_at": "2025-11-17T14:30:00"
            }
        }