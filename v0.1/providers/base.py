"""
Base LLM Provider
Abstract base class for all LLM providers (Ollama, Anthropic, etc.)

This provider builds prompts that include rich content analysis 
(image descriptions, text content, etc.) for intelligent organization.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.file_metadata import FileMetadata


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
        analysis_context: Dict[str, Any] = None
    ) -> str:
        """
        Build the analysis prompt for the LLM.
        
        Args:
            files: List of files to analyze
            analysis_context: Dict with image_analysis, text_analysis, patterns
            
        Returns:
            Complete prompt string
        """
        system_prompt = self._build_system_prompt()
        file_info = self._format_files_with_analysis(files, analysis_context or {})
        
        return f"{system_prompt}\n\n{file_info}"
    
    def _build_system_prompt(self) -> str:
        """Build the system/instruction portion of the prompt."""
        return """You are a file organizer. Create MULTIPLE different organization schemes for the same files.

TASK: Generate 2 DIFFERENT ways to organize the files. Each suggestion should use a different strategy.

STRATEGY 1 - BY SCENE/CONTENT TYPE:
Group by what's in the image (selfies, beach, music, art, sports, etc.)
Folder examples: "Selfies", "Beach & Pool", "Music & Events", "Art & Culture"

STRATEGY 2 - BY ACTIVITY/CONTEXT:
Group by what the person was doing or the occasion
Folder examples: "Night Out", "Outdoor Activities", "Creative Hobbies", "Fitness"

IMPORTANT RULES:
- Each suggestion MUST include ALL files
- Each suggestion should use a DIFFERENT organization logic
- Use descriptive folder names (not filenames or UUIDs)

OUTPUT FORMAT (JSON only):
{
  "suggestions": [
    {
      "folder_structure": {
        "base_path": "Photos/By Content",
        "folders": [
          {"name": "Selfies", "files": ["file1.jpg", "file2.jpg"]},
          {"name": "Beach", "files": ["file3.jpg"]}
        ]
      },
      "confidence": 0.90,
      "reasoning": "Organized by scene type - groups similar content together"
    },
    {
      "folder_structure": {
        "base_path": "Photos/By Activity",
        "folders": [
          {"name": "Night Out", "files": ["file1.jpg", "file4.jpg"]},
          {"name": "Relaxation", "files": ["file2.jpg", "file3.jpg"]}
        ]
      },
      "confidence": 0.85,
      "reasoning": "Organized by activity - groups by what you were doing"
    }
  ],
  "file_count": 4,
  "analysis_summary": "Generated 2 organization options"
}"""
    
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
        
        # Group files by scene for easy reference
        scene_groups = {}
        setting_groups = {}  # indoor/outdoor
        
        for file in files:
            if file.path in image_map:
                img = image_map[file.path]
                scene = img.scene_type or "other"
                setting = img.indoor_outdoor or "unknown"
            else:
                scene = file.content_type or "other"
                setting = "unknown"
            
            if scene not in scene_groups:
                scene_groups[scene] = []
            scene_groups[scene].append(file.name)
            
            if setting not in setting_groups:
                setting_groups[setting] = []
            setting_groups[setting].append(file.name)
        
        # Show grouped summary - this helps LLM generate different strategies
        lines.append("=" * 60)
        lines.append(f"ORGANIZE THESE {len(files)} FILES")
        lines.append("=" * 60)
        lines.append("")
        
        # Strategy 1 hint: By scene/content
        lines.append("📷 BY SCENE TYPE (Strategy 1):")
        for scene, filenames in sorted(scene_groups.items()):
            folder_name = self._scene_to_folder(scene)
            lines.append(f"   {scene} ({len(filenames)} files) → \"{folder_name}\"")
            for fn in filenames:
                lines.append(f"      - {fn}")
        lines.append("")
        
        # Strategy 2 hint: By setting
        lines.append("🏠 BY SETTING (Strategy 2):")
        for setting, filenames in sorted(setting_groups.items()):
            lines.append(f"   {setting} ({len(filenames)} files)")
            for fn in filenames[:5]:
                lines.append(f"      - {fn}")
            if len(filenames) > 5:
                lines.append(f"      ... and {len(filenames) - 5} more")
        lines.append("")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"COMPLETE FILE LIST ({len(files)} files):")
        lines.append("=" * 60)
        for i, file in enumerate(files, 1):
            if file.path in image_map:
                img = image_map[file.path]
                scene = img.scene_type or "other"
                setting = img.indoor_outdoor or "?"
                lines.append(f"  {i}. {file.name} [scene={scene}, {setting}]")
            else:
                lines.append(f"  {i}. {file.name} [type={file.content_type}]")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"CREATE 2-3 DIFFERENT ORGANIZATION SCHEMES FOR ALL {len(files)} FILES.")
        lines.append("Each scheme should use a different strategy (by content, by activity, by setting).")
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