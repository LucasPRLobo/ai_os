"""
Ollama Vision Provider
Uses LLaVA model for image analysis via Ollama.
"""

import base64
import json
import requests
from pathlib import Path
from typing import Optional, Dict


class OllamaVisionProvider:
    """
    Vision provider using Ollama's LLaVA model.

    Analyzes images and extracts:
    - Scene description
    - Objects detected
    - People count
    - Indoor/outdoor classification
    - Activities
    """

    def __init__(
        self,
        model: str = "llava:7b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120
    ):
        """
        Initialize vision provider.

        Args:
            model: Vision model name (default: llava:7b)
            base_url: Ollama API base URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.timeout = timeout

    def is_available(self) -> bool:
        """
        Check if Ollama is running and LLaVA model is available.

        Returns:
            True if vision analysis is available
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code != 200:
                return False

            # Check if llava model is installed
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            # Check for our model or any llava variant
            for name in model_names:
                if "llava" in name.lower():
                    return True

            return False

        except Exception:
            return False

    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze an image using LLaVA.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with analysis results:
            {
                'description': str,
                'objects': List[str],
                'scene': str,
                'people_count': int or None,
                'indoor_outdoor': str or None,
                'activities': List[str] or None
            }
        """
        # Default result
        result = {
            'description': '',
            'objects': [],
            'scene': None,
            'people_count': None,
            'indoor_outdoor': None,
            'activities': None
        }

        try:
            # Read and encode image
            image_data = self._encode_image(image_path)
            if not image_data:
                result['description'] = f"Could not read image: {Path(image_path).name}"
                return result

            # Build prompt
            prompt = self._build_vision_prompt()

            # Call Ollama
            response = self._call_ollama(prompt, image_data)

            # Parse response
            parsed = self._parse_response(response)
            result.update(parsed)

        except Exception as e:
            result['description'] = f"Analysis error: {str(e)}"

        return result

    def _encode_image(self, image_path: str) -> Optional[str]:
        """
        Encode image to base64.

        Args:
            image_path: Path to image

        Returns:
            Base64 encoded string or None
        """
        try:
            path = Path(image_path)

            # Handle HEIC files (convert to JPEG first)
            if path.suffix.lower() in ['.heic', '.heif']:
                return self._convert_heic_to_base64(path)

            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            return None

    def _convert_heic_to_base64(self, path: Path) -> Optional[str]:
        """
        Convert HEIC image to base64 JPEG.

        Args:
            path: Path to HEIC file

        Returns:
            Base64 encoded JPEG or None
        """
        try:
            from PIL import Image
            import pillow_heif
            import io

            # Register HEIF opener
            pillow_heif.register_heif_opener()

            # Open and convert
            img = Image.open(path)

            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            return base64.b64encode(buffer.read()).decode('utf-8')

        except ImportError:
            # pillow_heif not installed
            return None
        except Exception:
            return None

    def _build_vision_prompt(self) -> str:
        """Build the prompt for vision analysis."""
        return """Analyze this image carefully and respond with a JSON object.

REQUIRED FIELDS:
- description: Detailed description of what you see
- objects: Array of main objects/things visible
- scene: MUST be one of these categories:
    "selfie", "portrait", "group-photo", "beach", "pool", "nature",
    "city-street", "restaurant", "bar", "home-indoor", "office",
    "event", "travel", "sports", "music", "art", "food", "pet", "other"
- people_count: Number of people (0, 1, 2, 3, etc. or null if unclear)
- indoor_outdoor: "indoor" or "outdoor"
- activities: Array of activities happening, or null

Choose the BEST scene category that matches. Examples:
- Person taking selfie in bathroom -> "selfie"
- Person at beach/pool with swimwear -> "beach" or "pool"
- People on city street at night -> "city-street"
- Person playing guitar -> "music"
- Person doing yoga/exercise -> "sports"
- Standing in front of mural/art -> "art"

JSON format:
{
  "description": "...",
  "objects": ["..."],
  "scene": "one-of-the-categories-above",
  "people_count": 1,
  "indoor_outdoor": "outdoor",
  "activities": ["..."] or null
}

Respond ONLY with valid JSON, no other text."""

    def _call_ollama(self, prompt: str, image_base64: str) -> str:
        """
        Call Ollama API with image.

        Args:
            prompt: Text prompt
            image_base64: Base64 encoded image

        Returns:
            Response text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500
            }
        }

        response = requests.post(
            self.api_url,
            json=payload,
            timeout=self.timeout
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        result = response.json()
        return result.get("response", "")

    def _parse_response(self, response: str) -> Dict:
        """
        Parse LLaVA response into structured data.

        Args:
            response: Raw response text

        Returns:
            Parsed dictionary
        """
        result = {
            'description': '',
            'objects': [],
            'scene': None,
            'people_count': None,
            'indoor_outdoor': None,
            'activities': None
        }

        # Clean up response
        text = response.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            data = json.loads(text)

            result['description'] = data.get('description', '')
            result['objects'] = data.get('objects', [])
            result['scene'] = data.get('scene')
            result['people_count'] = data.get('people_count')
            result['indoor_outdoor'] = data.get('indoor_outdoor')
            result['activities'] = data.get('activities')

        except json.JSONDecodeError:
            # If JSON parsing fails, use the raw text as description
            result['description'] = text[:500] if text else "No description available"

        return result
