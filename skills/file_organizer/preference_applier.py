"""
Preference Applier
Applies learned preferences to organization suggestions.

Adjusts:
- Suggestion ordering (preferred strategies first)
- Folder names (use learned preferences)
- Confidence scores (boost preferred strategies)
"""

from typing import List, Optional
from shared.models.suggestions import SuggestionResponse, Suggestion
from shared.learning.preference_store import PreferenceStore


def apply_preferences(
    suggestions: SuggestionResponse,
    store: Optional[PreferenceStore] = None
) -> SuggestionResponse:
    """
    Apply learned preferences to suggestions.

    - Reorders suggestions by strategy preference
    - Updates folder names to user preferences
    - Adjusts confidence based on historical acceptance

    Args:
        suggestions: Original suggestions from LLM
        store: Preference store (creates new if None)

    Returns:
        Modified suggestions with preferences applied
    """
    if store is None:
        store = PreferenceStore()

    # Get strategy ranking
    strategy_ranking = store.get_strategy_ranking()

    # Score and sort suggestions
    scored_suggestions = []
    for sugg in suggestions.suggestions:
        strategy = _detect_strategy(sugg.folder_structure.base_path)

        # Calculate preference boost
        if strategy in strategy_ranking:
            rank = strategy_ranking.index(strategy)
            preference_boost = (len(strategy_ranking) - rank) * 0.05
        else:
            preference_boost = 0

        # Apply folder name preferences
        sugg = _apply_folder_names(sugg, store)

        # Adjust confidence
        new_confidence = min(1.0, sugg.confidence + preference_boost)

        scored_suggestions.append((
            new_confidence,
            strategy_ranking.index(strategy) if strategy in strategy_ranking else 99,
            sugg,
            new_confidence
        ))

    # Sort by preference rank, then confidence
    scored_suggestions.sort(key=lambda x: (x[1], -x[0]))

    # Update confidence scores and rebuild list
    updated_suggestions = []
    for _, _, sugg, new_conf in scored_suggestions:
        updated = Suggestion(
            folder_structure=sugg.folder_structure,
            confidence=new_conf,
            reasoning=sugg.reasoning
        )
        updated_suggestions.append(updated)

    return SuggestionResponse(
        suggestions=updated_suggestions,
        file_count=suggestions.file_count,
        analysis_summary=suggestions.analysis_summary
    )


def _detect_strategy(base_path: str) -> str:
    """Detect strategy type from base path."""
    base_lower = base_path.lower()

    if "content" in base_lower:
        return "by_content"
    elif "activity" in base_lower:
        return "by_activity"
    elif "setting" in base_lower:
        return "by_setting"
    else:
        return "by_content"


def _apply_folder_names(sugg: Suggestion, store: PreferenceStore) -> Suggestion:
    """Apply user's preferred folder names."""
    default_to_scene = {
        "selfies": "selfie",
        "beach & pool": "beach",
        "city & travel": "city-street",
        "music & events": "music",
        "art & culture": "art",
        "sports & fitness": "sports",
        "portraits": "portrait",
        "home": "home-indoor",
    }

    for folder in sugg.folder_structure.folders:
        folder_lower = folder.name.lower()

        for default_name, scene_type in default_to_scene.items():
            if default_name in folder_lower or folder_lower in default_name:
                preferred = store.get_preferred_folder_name(scene_type, folder.name)
                folder.name = preferred
                break

    return sugg
