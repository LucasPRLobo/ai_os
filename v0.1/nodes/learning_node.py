"""
Learning Node
Records user choices after organization execution.

This is the "learn" step in the flow:
extract intent → suggest → confirm → act → LEARN
"""

from models.state import OrganizerState
from learning.preference_store import PreferenceStore
from typing import Optional


def learn_from_choice(state: OrganizerState) -> OrganizerState:
    """
    Learn from the user's organization choice.
    
    Records:
    - Which strategy was chosen
    - Which suggestion index was selected
    - Whether the suggestion was modified
    - Folder names used
    
    Args:
        state: Current graph state after execution
        
    Returns:
        Updated state (unchanged, learning is side-effect)
    """
    # Skip if cancelled or no execution
    if state.get("user_cancelled"):
        return state
    
    execution_result = state.get("execution_result", {})
    if not execution_result or execution_result.get("status") not in ("success", "partial"):
        return state
    
    selected = state.get("selected_suggestion")
    if not selected:
        return state
    
    # Initialize preference store
    store = PreferenceStore()
    
    # Determine strategy from base_path
    strategy = _detect_strategy(selected.folder_structure.base_path)
    
    # Find which suggestion index was chosen
    suggestions = state.get("suggestions")
    suggestion_index = 0
    if suggestions:
        for i, sugg in enumerate(suggestions.suggestions):
            if sugg.folder_structure.base_path == selected.folder_structure.base_path:
                suggestion_index = i
                break
    
    # Count files organized
    files_organized = sum(
        folder.get_total_files() 
        for folder in selected.folder_structure.folders
    )
    
    # Record the choice
    store.record_choice(
        strategy=strategy,
        suggestion_index=suggestion_index,
        total_suggestions=len(suggestions.suggestions) if suggestions else 1,
        files_organized=files_organized,
        folder_structure=selected.folder_structure.model_dump(),
        was_modified=False  # TODO: Track modifications
    )
    
    # Learn folder names
    for folder in selected.folder_structure.folders:
        # Try to detect scene type from folder contents
        scene_type = _detect_scene_from_folder(folder, state)
        if scene_type:
            store.learn_folder_name(scene_type, folder.name)
    
    return state


def _detect_strategy(base_path: str) -> str:
    """Detect strategy type from base path."""
    base_lower = base_path.lower()
    
    if "content" in base_lower or "type" in base_lower:
        return "by_content"
    elif "activity" in base_lower or "event" in base_lower:
        return "by_activity"
    elif "setting" in base_lower or "location" in base_lower:
        return "by_setting"
    else:
        return "by_content"  # Default


def _detect_scene_from_folder(folder, state: OrganizerState) -> Optional[str]:
    """
    Try to detect the dominant scene type for files in a folder.
    
    Args:
        folder: FolderSuggestion with files
        state: Current state with image analysis
        
    Returns:
        Scene type or None
    """
    image_analysis = state.get("image_analysis") or []
    
    # Build filename -> scene_type map
    scene_map = {}
    for img in image_analysis:
        if img.scene_type:
            scene_map[img.file_name] = img.scene_type
    
    # Find scenes for files in this folder
    scenes = []
    for filename in folder.files:
        if filename in scene_map:
            scenes.append(scene_map[filename])
    
    # Return most common scene
    if scenes:
        from collections import Counter
        most_common = Counter(scenes).most_common(1)
        if most_common:
            return most_common[0][0]
    
    return None