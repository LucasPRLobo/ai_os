"""
Analysis Models
Pydantic models for file content analysis (images, text, etc.)
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


class ImageAnalysis(BaseModel):
    """
    Analysis results for an image file.

    Captures What/When/Where information from both visual content
    and metadata (EXIF) to enable intelligent organization.
    """

    # ===== FILE REFERENCE =====
    file_path: str = Field(
        ...,
        description="Absolute path to the image file"
    )

    file_name: str = Field(
        ...,
        description="Image file name"
    )

    # ===== WHAT (Visual Content) =====
    description: str = Field(
        ...,
        description="Natural language description from vision LLM",
        examples=["A group of three people on a sandy beach at sunset"]
    )

    objects: List[str] = Field(
        default_factory=list,
        description="Objects detected in the image",
        examples=[["person", "beach", "palm tree", "sunset"]]
    )

    people_count: Optional[int] = Field(
        None,
        description="Number of people detected in the image",
        ge=0
    )

    activities: Optional[List[str]] = Field(
        None,
        description="Activities or actions detected",
        examples=[["swimming", "relaxing", "walking"]]
    )

    scene_type: Optional[str] = Field(
        None,
        description="Type of scene or setting",
        examples=["beach", "office", "indoor-home", "nature-forest", "city-street"]
    )

    text_in_image: Optional[str] = Field(
        None,
        description="Text extracted from image via OCR"
    )

    # ===== WHEN (Temporal Information) =====
    date_taken: Optional[datetime] = Field(
        None,
        description="Date/time when photo was taken (from EXIF)"
    )

    date_modified: datetime = Field(
        ...,
        description="File last modified date"
    )

    time_of_day: Optional[str] = Field(
        None,
        description="Time of day detected from visual content",
        examples=["morning", "afternoon", "evening", "night", "golden-hour"]
    )

    season_hint: Optional[str] = Field(
        None,
        description="Season hint if detectable from visual content",
        examples=["summer", "winter", "spring", "fall"]
    )

    # ===== WHERE (Location Information) =====
    location_from_exif: Optional[str] = Field(
        None,
        description="Location from EXIF GPS data or metadata",
        examples=["Barcelona, Spain", "40.7128N, 74.0060W"]
    )

    location_from_content: Optional[str] = Field(
        None,
        description="Location/setting detected from visual content",
        examples=["beach", "mountains", "city", "office", "home"]
    )

    indoor_outdoor: Optional[str] = Field(
        None,
        description="Whether scene is indoor or outdoor",
        examples=["indoor", "outdoor"]
    )

    # ===== METADATA =====
    camera_make: Optional[str] = Field(
        None,
        description="Camera manufacturer from EXIF",
        examples=["Apple", "Canon", "Sony"]
    )

    camera_model: Optional[str] = Field(
        None,
        description="Camera model from EXIF",
        examples=["iPhone 15 Pro", "Canon EOS R5"]
    )

    image_dimensions: Optional[str] = Field(
        None,
        description="Image dimensions (width x height)",
        examples=["1920x1080", "4032x3024"]
    )

    # ===== ORGANIZATIONAL =====
    suggested_tags: List[str] = Field(
        default_factory=list,
        description="Tags suggested for organization (combines content + metadata)",
        examples=[["vacation", "beach", "2025", "family", "travel"]]
    )

    confidence: Optional[float] = Field(
        None,
        description="Overall confidence in the analysis (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

    @field_validator('indoor_outdoor')
    @classmethod
    def validate_indoor_outdoor(cls, v: Optional[str]) -> Optional[str]:
        """Validate indoor_outdoor is one of the expected values."""
        if v is not None and v not in ['indoor', 'outdoor']:
            raise ValueError("indoor_outdoor must be 'indoor' or 'outdoor'")
        return v

    @field_validator('confidence')
    @classmethod
    def round_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Round confidence to 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v

    def get_primary_location(self) -> Optional[str]:
        """
        Get the best available location information.
        Prefers EXIF location over content-based location.

        Returns:
            Location string or None
        """
        return self.location_from_exif or self.location_from_content

    def get_primary_date(self) -> datetime:
        """
        Get the best available date.
        Prefers date_taken (EXIF) over date_modified.

        Returns:
            datetime object
        """
        return self.date_taken or self.date_modified

    def has_exif_data(self) -> bool:
        """
        Check if image has EXIF metadata.

        Returns:
            True if any EXIF data is present
        """
        return any([
            self.date_taken,
            self.location_from_exif,
            self.camera_make,
            self.camera_model
        ])

    def get_organizational_summary(self) -> str:
        """
        Get a human-readable summary for organization purposes.

        Returns:
            Summary string combining key information
        """
        parts = []

        # Add what
        if self.scene_type:
            parts.append(self.scene_type)

        # Add when
        date = self.get_primary_date()
        parts.append(date.strftime("%Y-%m"))

        # Add where
        location = self.get_primary_location()
        if location:
            parts.append(location)

        return " / ".join(parts)

    def to_short_summary(self) -> str:
        """
        Get a brief one-line summary.

        Returns:
            Short summary string
        """
        date_str = self.get_primary_date().strftime("%Y-%m-%d")
        location_str = self.get_primary_location() or "unknown location"
        return f"{date_str} - {self.scene_type or 'image'} at {location_str}"

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "file_path": "/home/user/Photos/vacation.jpg",
                "file_name": "vacation.jpg",
                "description": "Three people enjoying sunset on a tropical beach",
                "objects": ["person", "beach", "sunset", "palm tree", "ocean"],
                "people_count": 3,
                "activities": ["relaxing", "watching sunset"],
                "scene_type": "beach",
                "text_in_image": None,
                "date_taken": "2025-11-10T18:30:00",
                "date_modified": "2025-11-10T18:30:00",
                "time_of_day": "golden-hour",
                "season_hint": "summer",
                "location_from_exif": "Barcelona, Spain",
                "location_from_content": "beach",
                "indoor_outdoor": "outdoor",
                "camera_make": "Apple",
                "camera_model": "iPhone 15 Pro",
                "image_dimensions": "4032x3024",
                "suggested_tags": ["vacation", "beach", "travel", "2025", "barcelona", "family"],
                "confidence": 0.92
            }
        }
