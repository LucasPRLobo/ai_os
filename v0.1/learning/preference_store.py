"""
Preference Store
Persistent storage for learned user preferences.

Stores:
- Preferred organization strategies
- Folder name mappings
- Historical choices for confidence adjustment
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter


DEFAULT_PREFERENCES_PATH = Path.home() / ".ai_os" / "preferences.json"


class PreferenceStore:
    """
    Manages persistent storage of user preferences.
    
    Preferences are stored as JSON and loaded/saved automatically.
    """
    
    def __init__(self, path: Optional[Path] = None):
        """
        Initialize preference store.
        
        Args:
            path: Custom path for preferences file (default: ~/.ai_os/preferences.json)
        """
        self.path = path or DEFAULT_PREFERENCES_PATH
        self.preferences = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load preferences from disk."""
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._default_preferences()
        return self._default_preferences()
    
    def _default_preferences(self) -> Dict[str, Any]:
        """Return default preferences structure."""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            
            # Strategy preferences (learned from choices)
            "strategy_scores": {
                "by_content": 0,
                "by_activity": 0,
                "by_setting": 0,
            },
            
            # Folder name preferences (scene_type -> preferred_name)
            "folder_names": {
                # e.g., "selfie": "Self Portraits"
            },
            
            # Historical choices for learning
            "history": [],
            
            # Statistics
            "stats": {
                "total_organizations": 0,
                "total_files_organized": 0,
                "suggestions_accepted": 0,
                "suggestions_modified": 0,
            }
        }
    
    def save(self):
        """Save preferences to disk."""
        self.preferences["updated_at"] = datetime.now().isoformat()
        
        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.path, "w") as f:
            json.dump(self.preferences, f, indent=2)
    
    def record_choice(
        self,
        strategy: str,
        suggestion_index: int,
        total_suggestions: int,
        files_organized: int,
        folder_structure: Dict[str, Any],
        was_modified: bool = False
    ):
        """
        Record a user's organization choice for learning.
        
        Args:
            strategy: The strategy type chosen (by_content, by_activity, etc.)
            suggestion_index: Which suggestion was chosen (0-based)
            total_suggestions: Total suggestions offered
            files_organized: Number of files organized
            folder_structure: The folder structure that was applied
            was_modified: Whether user modified the suggestion
        """
        # Update strategy scores
        if strategy in self.preferences["strategy_scores"]:
            # First choice gets more weight
            weight = total_suggestions - suggestion_index
            self.preferences["strategy_scores"][strategy] += weight
        
        # Record in history (keep last 100)
        self.preferences["history"].append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "suggestion_index": suggestion_index,
            "files_organized": files_organized,
            "was_modified": was_modified,
        })
        self.preferences["history"] = self.preferences["history"][-100:]
        
        # Update stats
        self.preferences["stats"]["total_organizations"] += 1
        self.preferences["stats"]["total_files_organized"] += files_organized
        if was_modified:
            self.preferences["stats"]["suggestions_modified"] += 1
        else:
            self.preferences["stats"]["suggestions_accepted"] += 1
        
        self.save()
    
    def learn_folder_name(self, scene_type: str, preferred_name: str):
        """
        Learn a user's preferred folder name for a scene type.
        
        Args:
            scene_type: The scene type (e.g., "selfie")
            preferred_name: User's preferred folder name (e.g., "Self Portraits")
        """
        self.preferences["folder_names"][scene_type] = preferred_name
        self.save()
    
    def get_preferred_folder_name(self, scene_type: str, default: str) -> str:
        """
        Get the user's preferred folder name for a scene type.
        
        Args:
            scene_type: The scene type
            default: Default name if no preference exists
            
        Returns:
            Preferred folder name
        """
        return self.preferences["folder_names"].get(scene_type, default)
    
    def get_strategy_ranking(self) -> List[str]:
        """
        Get strategies ranked by user preference.
        
        Returns:
            List of strategy names, highest preference first
        """
        scores = self.preferences["strategy_scores"]
        return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    def get_preferred_strategy(self) -> Optional[str]:
        """
        Get the user's most preferred strategy.
        
        Returns:
            Strategy name or None if no clear preference
        """
        ranking = self.get_strategy_ranking()
        scores = self.preferences["strategy_scores"]
        
        # Only return if there's a clear preference (score > 0)
        if ranking and scores[ranking[0]] > 0:
            return ranking[0]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self.preferences["stats"].copy()
    
    def reset(self):
        """Reset all preferences to defaults."""
        self.preferences = self._default_preferences()
        self.save()