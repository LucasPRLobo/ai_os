"""
Aggregate Results Node
Combines analysis results from all file types into a unified format.
"""

from models.state import OrganizerState
from typing import Dict, List, Any


def aggregate_results(state: OrganizerState) -> OrganizerState:
    """
    Aggregate analysis results from all file type processors.
    
    Combines results from:
    - Image analysis (ImageAnalysis objects)
    - Text analysis (TextAnalysis objects)
    - Document analysis
    - Other file metadata
    
    Creates a unified view for the organization LLM to process.
    
    Args:
        state: Current graph state with analysis results
        
    Returns:
        Updated state with aggregated_analysis dictionary
    """
    warnings = state.get("warnings", []).copy()
    
    # Gather all analysis results
    image_analysis = state.get("image_analysis") or []
    text_analysis = state.get("text_analysis") or []
    document_analysis = state.get("document_analysis") or []
    other_files = state.get("other_files") or []
    
    # Create aggregated summary
    aggregated = {
        # Counts
        "total_files": len(state.get("files", [])),
        "total_images": len(image_analysis),
        "total_text": len(text_analysis),
        "total_documents": len(document_analysis),
        "total_other": len(other_files),
        
        # Analysis results
        "images": image_analysis,
        "texts": text_analysis,
        "documents": document_analysis,
        "other": other_files,
        
        # Summary statistics
        "has_images": len(image_analysis) > 0,
        "has_text": len(text_analysis) > 0,
        "has_documents": len(document_analysis) > 0,
        "dominant_type": _determine_dominant_type(
            len(image_analysis),
            len(text_analysis),
            len(document_analysis),
            len(other_files)
        ),
    }
    
    # Extract common patterns for organization hints
    if len(image_analysis) > 0:
        aggregated["image_patterns"] = _extract_image_patterns(image_analysis)
    
    if len(text_analysis) > 0:
        aggregated["text_patterns"] = _extract_text_patterns(text_analysis)
    
    # Store in state
    state["aggregated_analysis"] = aggregated
    
    # Add summary to warnings/info
    summary = (
        f"Aggregated analysis: {aggregated['total_files']} files total - "
        f"dominant type: {aggregated['dominant_type']}"
    )
    warnings.append(summary)
    state["warnings"] = warnings
    
    return state


def _determine_dominant_type(
    num_images: int,
    num_text: int,
    num_documents: int,
    num_other: int
) -> str:
    """
    Determine which file type is dominant in the batch.
    
    Args:
        num_images: Number of image files
        num_text: Number of text files
        num_documents: Number of document files
        num_other: Number of other files
        
    Returns:
        Dominant type: "images", "text", "documents", "other", or "mixed"
    """
    counts = {
        "images": num_images,
        "text": num_text,
        "documents": num_documents,
        "other": num_other
    }
    
    total = sum(counts.values())
    if total == 0:
        return "none"
    
    # Find the dominant type
    max_type = max(counts, key=counts.get)
    max_count = counts[max_type]
    
    # If dominant type is >50% of total, return it
    if max_count / total > 0.5:
        return max_type
    else:
        return "mixed"


def _extract_image_patterns(image_analysis: List[Any]) -> Dict:
    """
    Extract common patterns from image analysis results.
    
    Looks for common themes like:
    - Common locations
    - Date ranges
    - Scene types
    - Activities
    
    Args:
        image_analysis: List of ImageAnalysis objects
        
    Returns:
        Dictionary with pattern information
    """
    from collections import Counter
    
    patterns = {
        "common_locations": [],
        "date_range": None,
        "common_scenes": [],
        "common_activities": [],
        "has_people": False,
        "indoor_outdoor_ratio": {"indoor": 0, "outdoor": 0}
    }
    
    if not image_analysis:
        return patterns
    
    # Extract locations
    locations = []
    for img in image_analysis:
        loc = img.get_primary_location()
        if loc:
            locations.append(loc)
    
    if locations:
        location_counts = Counter(locations)
        patterns["common_locations"] = [loc for loc, _ in location_counts.most_common(3)]
    
    # Extract date range
    dates = [img.get_primary_date() for img in image_analysis]
    if dates:
        patterns["date_range"] = {
            "earliest": min(dates).isoformat(),
            "latest": max(dates).isoformat()
        }
    
    # Extract scene types
    scenes = [img.scene_type for img in image_analysis if img.scene_type]
    if scenes:
        scene_counts = Counter(scenes)
        patterns["common_scenes"] = [scene for scene, _ in scene_counts.most_common(3)]
    
    # Extract activities
    all_activities = []
    for img in image_analysis:
        if img.activities:
            all_activities.extend(img.activities)
    if all_activities:
        activity_counts = Counter(all_activities)
        patterns["common_activities"] = [act for act, _ in activity_counts.most_common(3)]
    
    # Check if any images have people
    patterns["has_people"] = any(
        img.people_count and img.people_count > 0 
        for img in image_analysis
    )
    
    # Indoor/outdoor ratio
    for img in image_analysis:
        if img.indoor_outdoor == "indoor":
            patterns["indoor_outdoor_ratio"]["indoor"] += 1
        elif img.indoor_outdoor == "outdoor":
            patterns["indoor_outdoor_ratio"]["outdoor"] += 1
    
    return patterns


def _extract_text_patterns(text_analysis: List[Any]) -> Dict:
    """
    Extract common patterns from text analysis results.

    Args:
        text_analysis: List of text analysis dicts (from analyze_text node)

    Returns:
        Dictionary with pattern information
    """
    from collections import Counter

    patterns = {
        "common_topics": [],
        "document_types": [],
        "has_code": False,
        "languages": []
    }

    if not text_analysis:
        return patterns

    # Collect topics across all text files
    all_topics = []
    for entry in text_analysis:
        topics = entry.get("topics") or []
        all_topics.extend(topics)

    if all_topics:
        topic_counts = Counter(all_topics)
        patterns["common_topics"] = [t for t, _ in topic_counts.most_common(5)]

    # Collect document types and their counts
    doc_types = [entry.get("document_type", "other") for entry in text_analysis]
    if doc_types:
        type_counts = Counter(doc_types)
        patterns["document_types"] = [
            {"type": t, "count": c} for t, c in type_counts.most_common()
        ]

    # Detect code files and languages
    languages = []
    for entry in text_analysis:
        lang = entry.get("language")
        if lang:
            languages.append(lang)

    if languages:
        patterns["has_code"] = True
        lang_counts = Counter(languages)
        patterns["languages"] = [l for l, _ in lang_counts.most_common(5)]

    return patterns


# Example usage (commented out)
"""
from models.state import create_initial_state
from models.analysis import ImageAnalysis
from datetime import datetime

# Create test state with image analysis results
state = create_initial_state(input_paths=[])
state["files"] = [...]  # Some files
state["image_analysis"] = [
    ImageAnalysis(
        file_path="/tmp/photo1.jpg",
        file_name="photo1.jpg",
        description="Beach scene",
        objects=["beach", "person"],
        scene_type="beach",
        date_modified=datetime.now(),
        indoor_outdoor="outdoor"
    ),
    # More images...
]

# Aggregate results
state = aggregate_results(state)

print(f"Aggregated analysis:")
print(f"  Total files: {state['aggregated_analysis']['total_files']}")
print(f"  Dominant type: {state['aggregated_analysis']['dominant_type']}")
if 'image_patterns' in state['aggregated_analysis']:
    print(f"  Image patterns: {state['aggregated_analysis']['image_patterns']}")
"""