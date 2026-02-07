"""
Learning Package
Tracks user preferences and applies them to future suggestions.
"""

from learning.preference_store import PreferenceStore
from learning.preference_applier import apply_preferences

__all__ = [
    "PreferenceStore",
    "apply_preferences",
]