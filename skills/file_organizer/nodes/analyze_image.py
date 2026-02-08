"""
Analyze Image Node
Analyzes images using vision LLM and EXIF metadata extraction.
"""

from shared.models.state import OrganizerState
from shared.models.analysis import ImageAnalysis
from shared.providers.vision import OllamaVisionProvider
from shared.utils.exif_extractor import extract_exif_data
from datetime import datetime
from typing import List, Optional


def analyze_images(state: OrganizerState) -> OrganizerState:
    """
    Analyze all image files using vision LLM and EXIF extraction.

    For each image:
    1. Extract EXIF metadata (date, location, camera info)
    2. Analyze visual content with vision LLM
    3. Combine into ImageAnalysis object

    Args:
        state: Current graph state with image_files

    Returns:
        Updated state with image_analysis results
    """
    image_files = state.get("image_files", [])
    warnings = state.get("warnings", []).copy()
    errors = state.get("errors", []).copy()

    # If no images, skip
    if not image_files:
        state["image_analysis"] = []
        return state

    # Create vision provider
    try:
        vision_provider = OllamaVisionProvider()

        # Check if vision model is available
        if not vision_provider.is_available():
            warnings.append(
                "Vision model not available. Install with: ollama pull llava:7b\n"
                "Skipping image analysis."
            )
            state["image_analysis"] = []
            state["warnings"] = warnings
            return state
    except Exception as e:
        warnings.append(f"Could not initialize vision provider: {e}")
        state["image_analysis"] = []
        state["warnings"] = warnings
        return state

    # Analyze each image
    image_analysis_results = []

    for image_file in image_files:
        try:
            # Extract EXIF metadata
            exif_data = extract_exif_data(image_file.path)

            # Analyze visual content with vision LLM
            vision_result = vision_provider.analyze_image(image_file.path)

            # Combine into ImageAnalysis
            image_analysis = _create_image_analysis(
                image_file=image_file,
                exif_data=exif_data,
                vision_result=vision_result
            )

            image_analysis_results.append(image_analysis)

        except Exception as e:
            warnings.append(f"Failed to analyze image {image_file.name}: {str(e)}")

    # Store results
    state["image_analysis"] = image_analysis_results
    state["warnings"] = warnings
    state["errors"] = errors

    # Add summary
    if image_analysis_results:
        warnings.append(f"Successfully analyzed {len(image_analysis_results)} images")

    return state


def _create_image_analysis(
    image_file,
    exif_data: dict,
    vision_result: dict
) -> ImageAnalysis:
    """
    Create ImageAnalysis object from file, EXIF, and vision data.

    Args:
        image_file: FileMetadata object
        exif_data: Dictionary from extract_exif_data()
        vision_result: Dictionary from vision provider

    Returns:
        ImageAnalysis object
    """
    # Extract EXIF fields
    date_taken = exif_data.get("datetime")
    location = exif_data.get("gps_location")
    camera_make = exif_data.get("make")
    camera_model = exif_data.get("model")
    dimensions = exif_data.get("dimensions")

    # Extract vision analysis fields
    description = vision_result.get("description", "")
    objects = vision_result.get("objects", [])
    scene_type = vision_result.get("scene", None)
    people_count = vision_result.get("people_count", None)
    indoor_outdoor = vision_result.get("indoor_outdoor", None)

    # Create ImageAnalysis
    return ImageAnalysis(
        # File reference
        file_path=image_file.path,
        file_name=image_file.name,

        # Visual content (from vision LLM)
        description=description or f"Image file: {image_file.name}",
        objects=objects,
        people_count=people_count,
        activities=None,
        scene_type=scene_type,
        text_in_image=None,

        # Temporal information
        date_taken=date_taken,
        date_modified=image_file.modified_date,
        time_of_day=None,
        season_hint=None,

        # Location information
        location_from_exif=location,
        location_from_content=scene_type,
        indoor_outdoor=indoor_outdoor,

        # Metadata
        camera_make=camera_make,
        camera_model=camera_model,
        image_dimensions=dimensions,

        # Organizational
        suggested_tags=[],
        confidence=0.8
    )
