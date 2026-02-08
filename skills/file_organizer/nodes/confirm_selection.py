"""
Confirm Selection Node
Interactive confirmation of organization suggestions.
"""

from shared.models.state import OrganizerState
from shared.models.suggestions import Suggestion, SuggestionResponse
from typing import Optional
import sys


def confirm_selection(state: OrganizerState) -> OrganizerState:
    """
    Present suggestions to user and get confirmation.

    Args:
        state: Current graph state with suggestions

    Returns:
        Updated state with selected_suggestion
    """
    suggestions_response = state.get("suggestions")
    errors = state.get("errors", []).copy()

    if not suggestions_response or not suggestions_response.suggestions:
        errors.append("No suggestions to confirm")
        state["errors"] = errors
        state["selected_suggestion"] = None
        return state

    suggestions = suggestions_response.suggestions

    # Display suggestions
    print("\n" + "=" * 60)
    print("  ORGANIZATION OPTIONS")
    print("=" * 60)

    for i, sugg in enumerate(suggestions, 1):
        _display_suggestion(i, sugg)

    # Get user choice
    selected = _get_user_choice(len(suggestions))

    if selected is None:
        print("\n  Operation cancelled.")
        state["selected_suggestion"] = None
        state["user_cancelled"] = True
    else:
        chosen = suggestions[selected - 1]
        print(f"\n  Selected option {selected}: {chosen.folder_structure.base_path}")
        state["selected_suggestion"] = chosen
        state["user_cancelled"] = False

    return state


def _display_suggestion(index: int, suggestion: Suggestion):
    """Display a single suggestion with details."""
    fs = suggestion.folder_structure
    confidence = suggestion.confidence

    # Confidence indicator
    if confidence >= 0.8:
        conf_label = "[HIGH]"
    elif confidence >= 0.5:
        conf_label = "[MED]"
    else:
        conf_label = "[LOW]"

    print(f"\n  {conf_label} Option {index}: {fs.base_path}")
    print(f"   Confidence: {confidence:.0%}")
    print(f"   Reasoning: {suggestion.reasoning}")

    # Count total files
    total_files = sum(folder.get_total_files() for folder in fs.folders)
    print(f"   Folders: {len(fs.folders)} | Files: {total_files}")

    # Show folder preview
    print(f"\n   Structure:")
    for folder in fs.folders:
        file_count = folder.get_total_files()
        print(f"     {folder.name}/ ({file_count} files)")

        # Show first few files
        for f in folder.files[:3]:
            print(f"       - {f}")
        if len(folder.files) > 3:
            print(f"       ... and {len(folder.files) - 3} more")

        # Show subfolders if any
        if folder.subfolders:
            for sub in folder.subfolders[:2]:
                print(f"       {sub.name}/ ({sub.get_total_files()} files)")


def _get_user_choice(num_options: int) -> Optional[int]:
    """Get user's choice interactively."""
    print("\n" + "-" * 60)
    print("Choose an option:")
    print(f"  [1-{num_options}] Select that option")
    print("  [p] Preview file movements for option 1")
    print("  [c] Cancel")
    print("-" * 60)

    while True:
        try:
            choice = input("\nYour choice: ").strip().lower()

            if choice == 'c':
                return None

            if choice == 'p':
                print("\n  Preview mode - showing what would happen for Option 1")
                print("   (Full preview will be shown before actual move)")
                continue

            num = int(choice)
            if 1 <= num <= num_options:
                return num
            else:
                print(f"Please enter a number between 1 and {num_options}")

        except ValueError:
            print("Invalid input. Enter a number or 'c' to cancel.")
        except KeyboardInterrupt:
            print("\n")
            return None
        except EOFError:
            # Non-interactive mode - auto-select first option
            print("\nNon-interactive mode: auto-selecting option 1")
            return 1


def auto_confirm_first(state: OrganizerState) -> OrganizerState:
    """
    Automatically confirm the first (best) suggestion.
    Useful for non-interactive/scripted usage.

    Args:
        state: Current graph state with suggestions

    Returns:
        Updated state with selected_suggestion
    """
    suggestions_response = state.get("suggestions")

    if suggestions_response and suggestions_response.suggestions:
        state["selected_suggestion"] = suggestions_response.suggestions[0]
        state["user_cancelled"] = False
    else:
        state["selected_suggestion"] = None
        state["user_cancelled"] = True

    return state
