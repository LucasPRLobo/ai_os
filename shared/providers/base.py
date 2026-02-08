"""
Base LLM Provider
Abstract base class for all LLM providers (Ollama, Anthropic, etc.)

This provider builds prompts that include rich content analysis
(image descriptions, text content, etc.) for intelligent organization.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from shared.models.file_metadata import FileMetadata


class ProviderNotAvailableError(Exception):
    """Raised when the LLM provider is not accessible."""
    pass


class ProviderAPIError(Exception):
    """Raised when the LLM API call fails."""
    pass


class ProviderParseError(Exception):
    """Raised when the LLM response cannot be parsed."""
    pass


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement:
    - is_available(): Check if provider is accessible
    - analyze(): Analyze files and return suggestions
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize base provider.

        Args:
            model: Model name/identifier
        """
        self.model = model

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used."""
        pass

    @abstractmethod
    def analyze(self, files: List[FileMetadata], analysis_context: Dict[str, Any] = None):
        """
        Analyze files and return organization suggestions.

        Args:
            files: List of FileMetadata objects
            analysis_context: Optional dict with image_analysis, text_analysis, etc.

        Returns:
            SuggestionResponse object
        """
        pass

    def build_prompt(
        self,
        files: List[FileMetadata],
        analysis_context: Dict[str, Any] = None,
        system_prompt: str = None
    ) -> str:
        """
        Build the analysis prompt for the LLM.

        Args:
            files: List of files to analyze
            analysis_context: Dict with image_analysis, text_analysis, patterns
            system_prompt: Optional custom system prompt (overrides default)

        Returns:
            Complete prompt string
        """
        prompt = system_prompt or self._build_system_prompt()
        file_info = self._format_files_with_analysis(files, analysis_context or {})

        return f"{prompt}\n\n{file_info}"

    def _build_system_prompt(self) -> str:
        """Build the system/instruction portion of the prompt."""
        return ""

    def _format_files_with_analysis(
        self,
        files: List[FileMetadata],
        analysis_context: Dict[str, Any]
    ) -> str:
        """
        Format files with their rich analysis for the prompt.

        Args:
            files: List of FileMetadata
            analysis_context: Dict with image_analysis, text_analysis, etc.
        """
        image_analysis = analysis_context.get("image_analysis", [])
        text_analysis = analysis_context.get("text_analysis", [])
        document_analysis = analysis_context.get("document_analysis", [])

        # Create lookup maps by file path
        image_map = {img.file_path: img for img in image_analysis}
        text_map = {t.get("file_path", ""): t for t in text_analysis}
        doc_map = {d.get("file_path", ""): d for d in document_analysis}

        lines = []
        lines.append("=" * 60)
        lines.append(f"ORGANIZE THESE {len(files)} FILES")
        lines.append("=" * 60)
        lines.append("")

        # Detailed per-file analysis
        lines.append("DETAILED FILE ANALYSIS:")
        lines.append("-" * 40)

        for i, file in enumerate(files, 1):
            if file.path in image_map:
                img = image_map[file.path]
                desc = img.description or "no description"
                scene = img.scene_type or "unknown"
                setting = img.indoor_outdoor or "unknown"
                objects = ", ".join(img.objects[:5]) if img.objects else "none detected"
                activities = ", ".join(img.activities[:3]) if img.activities else "none"
                people = img.people_count if img.people_count else 0
                location = img.get_primary_location() or "unknown"

                lines.append(f"  {i}. {file.name} [IMAGE]")
                lines.append(f"     Description: {desc}")
                lines.append(f"     Scene: {scene} | Setting: {setting} | People: {people}")
                lines.append(f"     Objects: {objects}")
                if activities != "none":
                    lines.append(f"     Activities: {activities}")
                if location != "unknown":
                    lines.append(f"     Location: {location}")

            elif file.path in text_map:
                t = text_map[file.path]
                doc_type = t.get("document_type", "unknown")
                language = t.get("language")
                topics = ", ".join(t.get("topics", [])) if t.get("topics") else None
                summary = t.get("summary")

                lines.append(f"  {i}. {file.name} [TEXT -- {doc_type}]")
                if language:
                    lines.append(f"     Language: {language}")
                if summary:
                    lines.append(f"     Summary: {summary}")
                elif file.content_preview:
                    preview = file.content_preview[:150].replace("\n", " ")
                    lines.append(f"     Preview: {preview}")
                if topics:
                    lines.append(f"     Topics: {topics}")

            elif file.path in doc_map:
                d = doc_map[file.path]
                detailed_type = d.get("detailed_type", file.content_type)
                size_cat = d.get("size_category", "unknown")
                lines.append(f"  {i}. {file.name} [DOCUMENT -- {detailed_type}, {size_cat}]")
            else:
                lines.append(f"  {i}. {file.name} [{file.content_type or 'unknown'}]")

            lines.append("")

        # Summary counts
        n_images = len([f for f in files if f.path in image_map])
        n_text = len([f for f in files if f.path in text_map])
        n_docs = len([f for f in files if f.path in doc_map])
        n_other = len(files) - n_images - n_text - n_docs

        lines.append("=" * 60)
        lines.append(f"SUMMARY: {len(files)} files total")
        parts = []
        if n_images: parts.append(f"{n_images} images")
        if n_text: parts.append(f"{n_text} text/code")
        if n_docs: parts.append(f"{n_docs} documents")
        if n_other: parts.append(f"{n_other} other")
        lines.append(f"  {', '.join(parts)}")
        lines.append("")

        # File name checklist
        lines.append("ALL FILES (every one must appear in every suggestion):")
        for file in files:
            lines.append(f"  - {file.name}")

        lines.append("")
        lines.append("=" * 60)
        lines.append(f"Generate 2-3 DIFFERENT organization schemes. Be SPECIFIC with folder names.")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _scene_to_folder(self, scene: str) -> str:
        """Map scene type to folder name."""
        mapping = {
            "selfie": "Selfies",
            "portrait": "Portraits",
            "group-photo": "Group Photos",
            "beach": "Beach & Pool",
            "pool": "Beach & Pool",
            "city-street": "City & Travel",
            "travel": "City & Travel",
            "music": "Music & Events",
            "event": "Music & Events",
            "art": "Art & Culture",
            "sports": "Sports & Fitness",
            "home-indoor": "Home",
            "nature": "Nature",
            "food": "Food",
            "pet": "Pets",
        }
        return mapping.get(scene, scene.title())

    def validate_response(self, response) -> bool:
        """
        Validate the suggestion response.

        Args:
            response: SuggestionResponse object

        Returns:
            True if valid

        Raises:
            ProviderParseError if invalid
        """
        if not response.suggestions:
            raise ProviderParseError("No suggestions in response")

        for suggestion in response.suggestions:
            if not suggestion.folder_structure:
                raise ProviderParseError("Suggestion missing folder_structure")
            if suggestion.confidence < 0 or suggestion.confidence > 1:
                raise ProviderParseError(f"Invalid confidence: {suggestion.confidence}")

        return True
