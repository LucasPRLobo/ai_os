"""
Ollama LLM Provider
Local LLM provider using Ollama for file organization analysis.

Ollama runs models locally for privacy and no API costs.
Default model: llava:7b (fast, good quality)
"""

import json
import requests
from typing import Optional, List
from shared.models.file_metadata import FileMetadata
from shared.models.suggestions import SuggestionResponse
from shared.providers.base import (
    BaseLLMProvider,
    ProviderNotAvailableError,
    ProviderAPIError,
    ProviderParseError
)


class OllamaProvider(BaseLLMProvider):
    """
    LLM provider for local Ollama models.

    Connects to Ollama running on localhost and uses the specified
    model for intelligent file organization analysis.
    """

    def __init__(
        self,
        model: str = "llava:7b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120
    ):
        super().__init__(model=model)
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except (requests.RequestException, Exception):
            return False

    def get_model_name(self) -> str:
        return self.model or "llama3.2:3b"

    def analyze(self, files: List[FileMetadata], analysis_context: dict = None) -> SuggestionResponse:
        """Analyze files using Ollama and return organization suggestions."""
        if not self.is_available():
            raise ProviderNotAvailableError(
                f"Ollama is not running. Please start Ollama:\n"
                f"  1. Run: ollama serve\n"
                f"  2. Or start Ollama app\n"
                f"  3. Verify model installed: ollama pull {self.get_model_name()}"
            )

        # Build the prompt with full analysis context
        prompt = self.build_prompt(files, analysis_context or {})

        # Call Ollama
        try:
            raw_response = self._call_ollama_api(prompt)
        except Exception as e:
            raise ProviderAPIError(f"Ollama API call failed: {str(e)}")

        # Parse response to SuggestionResponse
        try:
            suggestion_response = self._parse_json_response(raw_response, files)
        except Exception as e:
            raise ProviderParseError(
                f"Failed to parse Ollama response: {str(e)}\n"
                f"Raw response (first 500 chars): {raw_response[:500]}"
            )

        # Validate the response
        self.validate_response(suggestion_response)

        return suggestion_response

    def _call_ollama_api(self, prompt: str) -> str:
        """Make API call to Ollama with structured output."""
        # Get JSON schema from Pydantic model
        schema = SuggestionResponse.model_json_schema()

        payload = {
            "model": self.get_model_name(),
            "prompt": prompt,
            "stream": False,
            "format": schema,
            "options": {
                "temperature": 0.5,
                "num_predict": 6000,
                "num_ctx": 8192,
            }
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
        except requests.Timeout:
            raise Exception(
                f"Ollama request timed out after {self.timeout}s. "
                f"Try with fewer files or increase timeout."
            )
        except requests.RequestException as e:
            raise Exception(f"Ollama connection error: {str(e)}")

        if response.status_code != 200:
            raise Exception(
                f"Ollama API error (status {response.status_code}): "
                f"{response.text}"
            )

        try:
            result = response.json()
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON from Ollama: {response.text[:200]}")

        if "response" not in result:
            raise Exception(f"Unexpected Ollama format: {result}")

        return result["response"]

    def _parse_json_response(
        self,
        raw_response: str,
        files: List[FileMetadata]
    ) -> SuggestionResponse:
        """Parse raw Ollama response into SuggestionResponse."""
        response_text = raw_response.strip()

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Invalid JSON in response (schema enforcement failed?): {e}\n"
                f"Response: {response_text[:500]}"
            )

        if "file_count" not in data:
            data["file_count"] = len(files)

        # Sanitize folder names
        self._sanitize_folder_names(data)

        # Fix missing/duplicate files before validation
        all_filenames = [f.name for f in files]
        self._fix_file_assignments(data, all_filenames)

        try:
            suggestion_response = SuggestionResponse(**data)
        except Exception as e:
            raise Exception(
                f"Response doesn't match SuggestionResponse schema: {e}\n"
                f"Data: {json.dumps(data, indent=2)[:500]}"
            )

        return suggestion_response

    @staticmethod
    def _fix_file_assignments(data: dict, all_filenames: list):
        """Ensure every file appears exactly once in each suggestion."""
        filename_set = set(all_filenames)

        for suggestion in data.get("suggestions", []):
            folders = (
                suggestion
                .get("folder_structure", {})
                .get("folders", [])
            )

            # Pass 1: Remove hallucinated files + deduplicate
            seen = set()
            for folder in folders:
                cleaned = []
                for fname in folder.get("files", []):
                    if fname in filename_set and fname not in seen:
                        cleaned.append(fname)
                        seen.add(fname)
                folder["files"] = cleaned

            # Remove folders that ended up empty after cleaning
            folders[:] = [f for f in folders if f.get("files")]

            # Pass 2: Find missing files and add to "Other" folder
            missing = [f for f in all_filenames if f not in seen]
            if missing:
                folders.append({
                    "name": "Other",
                    "files": missing,
                })

    @staticmethod
    def _sanitize_folder_names(data: dict):
        """Clean up folder names that would fail validation."""
        for suggestion in data.get("suggestions", []):
            folders = (
                suggestion
                .get("folder_structure", {})
                .get("folders", [])
            )
            for folder in folders:
                name = folder.get("name", "")
                if "/" in name or "\\" in name:
                    folder["name"] = name.replace("/", " - ").replace("\\", " - ")

    def _build_system_prompt(self) -> str:
        """Override to add Ollama-specific emphasis."""
        base_prompt = super()._build_system_prompt()

        return """You are an intelligent file organizer. You analyze files deeply and create detailed, specific organization schemes.

TASK: Generate 2-3 DIFFERENT ways to organize the given files. Each suggestion MUST use a fundamentally different strategy.

STRATEGY TYPES (pick 2-3 that best fit the files):

1. BY CONTENT/TOPIC - Group by what the file IS ABOUT.
   - Images: specific scenes (beach sunset, city nightlife, pet portrait, concert, hiking trail)
   - Code: by project, language, or purpose (web frontend, data scripts, configs, tests)
   - Documents: by topic (meeting notes, project plans, research, personal)
   - Use SPECIFIC names, not generic ones. "Beach Sunset Photos" not just "Beach". "Python Data Scripts" not just "Code".

2. BY PURPOSE/WORKFLOW - Group by HOW the user would use or access these files.
   - "Work Projects", "Personal Creative", "Reference & Config", "Social Media"
   - Think about WHY someone has these files together

3. BY TYPE & FORMAT - Group primarily by file type with subcategories.
   - "Photos/Outdoor", "Photos/People", "Source Code/Python", "Source Code/JavaScript", "Config Files"

CRITICAL RULES:
- EVERY file in the list MUST appear in EXACTLY ONE folder in EACH suggestion. No file may be missing.
- Be SPECIFIC with folder names - "Jazz Night Photography" is better than "Creative Hobbies"
- Create 3-6 folders per suggestion (not too few, not too many)
- For code/text files: use their content analysis (topics, language, summary) to place them meaningfully
- Never use filenames or UUIDs as folder names
- Folder names MUST NOT contain "/" or "\\" - use " - " or " & " instead

OUTPUT FORMAT (respond with ONLY this JSON, no other text):
{
  "suggestions": [
    {
      "folder_structure": {
        "base_path": "Organized/By Content",
        "folders": [
          {"name": "Beach & Outdoor Adventures", "files": ["photo1.jpg", "photo2.jpg"]},
          {"name": "Python Data Analysis", "files": ["analysis.py", "data_utils.py"]},
          {"name": "Project Configuration", "files": ["config.yaml", ".env"]}
        ]
      },
      "confidence": 0.90,
      "reasoning": "Groups files by their specific content and subject matter"
    }
  ],
  "file_count": 5,
  "analysis_summary": "Generated N organization options"
}

CRITICAL:
- Output ONLY valid JSON (no other text)
- Generate 2-3 DIFFERENT suggestions with different strategies
- Include ALL files in EACH suggestion
- Each suggestion should organize files differently"""
