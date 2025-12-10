"""
Ollama LLM Provider
Local LLM provider using Ollama for file organization analysis.

Ollama runs models locally for privacy and no API costs.
Default model: llama3.2:3b (fast, good quality)
"""

import json
import requests
from typing import Optional, List
from models.file_metadata import FileMetadata
from models.suggestions import SuggestionResponse
from providers.base import (
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
    
    Attributes:
        model: Ollama model name (e.g., "llama3.2:3b")
        base_url: Ollama API URL (default: http://localhost:11434)
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self,
        model: str = "llava:7b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (default: llava:7b for best results)
            base_url: Ollama API base URL
            timeout: Request timeout (120s handles large file batches)
        """
        super().__init__(model=model)
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.timeout = timeout
    
    def is_available(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Attempts to connect to Ollama's tags endpoint to verify
        the service is running.
        
        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except (requests.RequestException, Exception):
            return False
    
    def get_model_name(self) -> str:
        """
        Get the current Ollama model name.
        
        Returns:
            Model name string
        """
        return self.model or "llama3.2:3b"
    
    def analyze(self, files: List[FileMetadata], analysis_context: dict = None) -> SuggestionResponse:
        """
        Analyze files using Ollama and return organization suggestions.
        
        Process:
        1. Check Ollama is available
        2. Build prompt with file information AND content analysis
        3. Call Ollama API
        4. Parse JSON response
        5. Validate and return SuggestionResponse
        
        Args:
            files: List of FileMetadata objects to analyze
            analysis_context: Dict with image_analysis, text_analysis, patterns, etc.
            
        Returns:
            SuggestionResponse with organization suggestions
            
        Raises:
            ProviderNotAvailableError: Ollama not running
            ProviderAPIError: API call failed
            ProviderParseError: Response parsing failed
        """
        # Verify Ollama is available
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
        """
        Make API call to Ollama with structured output.
        
        Uses Ollama's JSON schema feature to enforce the response format.
        
        Args:
            prompt: Complete prompt to send
            
        Returns:
            Raw text response from Ollama
            
        Raises:
            Exception: If API call fails
        """
        from models.suggestions import SuggestionResponse
        
        # Get JSON schema from Pydantic model
        schema = SuggestionResponse.model_json_schema()
        
        # Prepare request payload with format enforcement
        payload = {
            "model": self.get_model_name(),
            "prompt": prompt,
            "stream": False,  # Get complete response at once
            "format": schema,  # THIS IS THE KEY: Ollama will enforce the schema!
            "options": {
                "temperature": 0.5,  # Slightly higher for more diverse suggestions
                "num_predict": 6000,  # Max tokens (increased for multiple suggestions)
                "num_ctx": 8192,  # Context window size
            }
        }
        
        # Make request
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
        
        # Check response status
        if response.status_code != 200:
            raise Exception(
                f"Ollama API error (status {response.status_code}): "
                f"{response.text}"
            )
        
        # Parse Ollama response
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON from Ollama: {response.text[:200]}")
        
        # Extract response text
        if "response" not in result:
            raise Exception(f"Unexpected Ollama format: {result}")
        
        return result["response"]
    
    def _parse_json_response(
        self,
        raw_response: str,
        files: List[FileMetadata]
    ) -> SuggestionResponse:
        """
        Parse raw Ollama response into SuggestionResponse.
        
        Since we're using schema enforcement, the response should already
        be valid JSON matching our SuggestionResponse model.
        
        Args:
            raw_response: Raw text from Ollama
            files: Original file list (for validation)
            
        Returns:
            Parsed and validated SuggestionResponse
            
        Raises:
            Exception: If JSON is invalid or doesn't match schema
        """
        from models.suggestions import SuggestionResponse
        
        # Clean up response text
        response_text = raw_response.strip()
        
        # Parse JSON (should already be valid thanks to schema enforcement)
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Invalid JSON in response (schema enforcement failed?): {e}\n"
                f"Response: {response_text[:500]}"
            )
        
        # Add file_count if missing
        if "file_count" not in data:
            data["file_count"] = len(files)
        
        # Convert to Pydantic model (validates structure)
        try:
            suggestion_response = SuggestionResponse(**data)
        except Exception as e:
            raise Exception(
                f"Response doesn't match SuggestionResponse schema: {e}\n"
                f"This shouldn't happen with schema enforcement.\n"
                f"Data: {json.dumps(data, indent=2)[:500]}"
            )
        
        return suggestion_response
    
    def _build_system_prompt(self) -> str:
        """Override to add Ollama-specific emphasis."""
        base_prompt = super()._build_system_prompt()
        
        ollama_note = """

CRITICAL: 
- Output ONLY valid JSON (no other text)
- Generate 2-3 DIFFERENT suggestions with different strategies
- Include ALL files in EACH suggestion
- Each suggestion should organize files differently"""
        
        return base_prompt + ollama_note


# Example usage
if __name__ == "__main__":
    """
    Test the Ollama provider with a sample file.
    
    Run: python -m providers.ollama
    """
    from models.file_metadata import FileMetadata
    from datetime import datetime
    
    # Create provider
    provider = OllamaProvider(model="llama3.2:3b")
    
    print(f"Ollama Provider Test")
    print(f"=" * 50)
    
    # Check availability
    if provider.is_available():
        print(f"✓ Ollama is running")
        print(f"✓ Using model: {provider.get_model_name()}")
    else:
        print(f"✗ Ollama is NOT running")
        print(f"  Start with: ollama serve")
        print(f"  Install model: ollama pull {provider.get_model_name()}")
        exit(1)
    
    # Create test file
    test_file = FileMetadata(
        name="invoice_2025.pdf",
        path="/tmp/invoice_2025.pdf",
        extension=".pdf",
        size=245760,
        modified_date=datetime.now(),
        created_date=datetime.now(),
        content_preview="Invoice #12345\nDate: November 15, 2025\nAmount: $500",
        content_type="document",
        parent_directory="Downloads"
    )
    
    print(f"\nAnalyzing test file: {test_file.name}")
    print(f"=" * 50)
    
    # Analyze
    try:
        result = provider.analyze([test_file])
        
        print(f"\n✓ Got {len(result.suggestions)} suggestions:\n")
        for i, sugg in enumerate(result.suggestions, 1):
            print(f"{i}. {sugg.folder_structure.base_path}")
            print(f"   Confidence: {sugg.confidence}")
            print(f"   Reasoning: {sugg.reasoning}")
            print()
    except Exception as e:
        print(f"\n✗ Error: {e}")