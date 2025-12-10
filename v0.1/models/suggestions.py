"""
Suggestion Models
Pydantic models for organization suggestions and folder structures.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class FolderNode(BaseModel):
    """
    Represents a single folder in the organization structure.
    
    Contains folder name and the files that should go into it.
    """
    
    name: str = Field(
        ...,
        description="Folder name (without path)",
        examples=["Invoices", "Receipts", "2025-November"]
    )
    
    files: list[str] = Field(
        default_factory=list,
        description="List of file names that should go in this folder",
        examples=[["invoice1.pdf", "invoice2.pdf"]]
    )
    
    subfolders: Optional[list['FolderNode']] = Field(
        None,
        description="Optional nested subfolders for deeper organization"
    )
    
    @field_validator('name')
    @classmethod
    def validate_folder_name(cls, v: str) -> str:
        """Ensure folder name is valid (no slashes, no leading/trailing spaces)."""
        # Remove leading/trailing whitespace
        v = v.strip()
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', '\0']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"Folder name cannot contain '{char}'")
        
        return v
    
    def get_total_files(self) -> int:
        """Get total number of files including subfolders."""
        total = len(self.files)
        if self.subfolders:
            for subfolder in self.subfolders:
                total += subfolder.get_total_files()
        return total
    
    def get_all_files_flat(self) -> list[str]:
        """Get all files in this folder and subfolders as a flat list."""
        all_files = self.files.copy()
        if self.subfolders:
            for subfolder in self.subfolders:
                all_files.extend(subfolder.get_all_files_flat())
        return all_files
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "Finance",
                "files": ["summary.txt"],
                "subfolders": [
                    {
                        "name": "Invoices",
                        "files": ["invoice1.pdf", "invoice2.pdf"],
                        "subfolders": None
                    },
                    {
                        "name": "Receipts",
                        "files": ["receipt1.jpg", "receipt2.jpg"],
                        "subfolders": None
                    }
                ]
            }
        }


class FolderStructure(BaseModel):
    """
    Complete folder organization structure for a suggestion.
    
    Represents how files should be organized with a base path and folder hierarchy.
    """
    
    base_path: str = Field(
        ...,
        description="Base destination path for this organization (relative to home or absolute)",
        examples=["Documents/Finance/2025", "Photos/Travel/Barcelona", "Projects/AI-OS"]
    )
    
    folders: list[FolderNode] = Field(
        default_factory=list,
        description="Folder structure with files. Empty list means all files go directly in base_path"
    )
    
    @field_validator('base_path')
    @classmethod
    def validate_base_path(cls, v: str) -> str:
        """Ensure base_path is clean (no leading/trailing slashes)."""
        return v.strip().strip('/')
    
    def get_total_files(self) -> int:
        """Get total number of files in this structure."""
        return sum(folder.get_total_files() for folder in self.folders)
    
    def get_all_files(self) -> list[str]:
        """Get all files in this structure as a flat list."""
        all_files = []
        for folder in self.folders:
            all_files.extend(folder.get_all_files_flat())
        return all_files
    
    def get_full_path(self, folder_node: FolderNode, parent_path: str = "") -> str:
        """
        Get full path for a folder node.
        
        Args:
            folder_node: The folder node to get path for
            parent_path: Parent folder path (for recursion)
            
        Returns:
            Full path string
        """
        if parent_path:
            return f"{self.base_path}/{parent_path}/{folder_node.name}"
        return f"{self.base_path}/{folder_node.name}"
    
    def is_flat_structure(self) -> bool:
        """Check if this is a flat structure (all files in base_path, no subfolders)."""
        return len(self.folders) == 0
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "base_path": "Documents/Finance/2025-November",
                "folders": [
                    {
                        "name": "Invoices",
                        "files": ["invoice1.pdf", "invoice2.pdf"],
                        "subfolders": None
                    },
                    {
                        "name": "Receipts",
                        "files": ["receipt1.jpg", "receipt2.jpg"],
                        "subfolders": None
                    }
                ]
            }
        }


class Suggestion(BaseModel):
    """
    A single organization suggestion with confidence and reasoning.
    """
    
    folder_structure: FolderStructure = Field(
        ...,
        description="The proposed folder organization structure"
    )
    
    confidence: float = Field(
        ...,
        description="Confidence score for this suggestion (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    reasoning: str = Field(
        ...,
        description="Explanation of why this organization makes sense",
        examples=[
            "Financial documents from November 2025, organized by document type",
            "Travel photos from Barcelona trip, grouped by date"
        ]
    )
    
    suggested_rank: Optional[int] = Field(
        None,
        description="Suggested ranking (1-5) where 1 is best",
        ge=1,
        le=5
    )
    
    estimated_conflicts: Optional[int] = Field(
        None,
        description="Number of existing folders/files that might conflict",
        ge=0
    )
    
    @field_validator('confidence')
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """Round confidence to 2 decimal places."""
        return round(v, 2)
    
    def get_confidence_label(self) -> str:
        """
        Get human-readable confidence label.
        
        Returns:
            "high", "medium", or "low"
        """
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "folder_structure": {
                    "base_path": "Documents/Finance/2025-November",
                    "folders": [
                        {
                            "name": "Invoices",
                            "files": ["invoice1.pdf", "invoice2.pdf"]
                        }
                    ]
                },
                "confidence": 0.92,
                "reasoning": "Financial documents from November 2025, organized by type",
                "suggested_rank": 1,
                "estimated_conflicts": 0
            }
        }


class SuggestionResponse(BaseModel):
    """
    Complete response containing multiple organization suggestions.
    
    This is what the LLM should return after analyzing files.
    """
    
    suggestions: list[Suggestion] = Field(
        ...,
        description="List of organization suggestions, ordered by confidence (top 5)",
        max_length=5
    )
    
    analysis_summary: Optional[str] = Field(
        None,
        description="Overall analysis of the files",
        examples=[
            "Mix of financial documents and receipts from November 2025",
            "Personal photos from Barcelona vacation, taken Nov 10-15, 2025"
        ]
    )
    
    file_count: int = Field(
        ...,
        description="Total number of files analyzed",
        ge=0
    )
    
    warnings: Optional[list[str]] = Field(
        None,
        description="Warnings or issues encountered during analysis",
        examples=[["Some files could not be read", "3 duplicate files found"]]
    )
    
    @field_validator('suggestions')
    @classmethod
    def validate_suggestions_count(cls, v: list[Suggestion]) -> list[Suggestion]:
        """Ensure we have at most 5 suggestions."""
        if len(v) > 5:
            raise ValueError("Maximum 5 suggestions allowed")
        return v
    
    @field_validator('suggestions')
    @classmethod
    def auto_rank_suggestions(cls, v: list[Suggestion]) -> list[Suggestion]:
        """Automatically assign ranks if not set."""
        for i, suggestion in enumerate(v, start=1):
            if suggestion.suggested_rank is None:
                suggestion.suggested_rank = i
        return v
    
    def get_best_suggestion(self) -> Optional[Suggestion]:
        """Get the highest confidence suggestion."""
        if not self.suggestions:
            return None
        return max(self.suggestions, key=lambda s: s.confidence)
    
    def get_suggestions_by_confidence(self) -> list[Suggestion]:
        """Get suggestions sorted by confidence (highest first)."""
        return sorted(self.suggestions, key=lambda s: s.confidence, reverse=True)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "folder_structure": {
                            "base_path": "Documents/Finance/2025-November",
                            "folders": [
                                {"name": "Invoices", "files": ["invoice1.pdf"]}
                            ]
                        },
                        "confidence": 0.92,
                        "reasoning": "Financial documents from November 2025",
                        "suggested_rank": 1
                    }
                ],
                "analysis_summary": "Mix of financial documents from November 2025",
                "file_count": 5,
                "warnings": None
            }
        }