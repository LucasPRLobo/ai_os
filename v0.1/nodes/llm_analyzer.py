"""
LLM Analyzer Node
Analyzes files using LLM provider and generates organization suggestions.

This node receives all analysis results (images, text, documents) and 
passes them to the LLM for intelligent organization suggestions.
"""
from learning.preference_applier import apply_preferences
from models.state import OrganizerState
from providers.base import (
    ProviderNotAvailableError,
    ProviderAPIError,
    ProviderParseError
)
from providers.ollama import OllamaProvider
from utils.progress import update_progress, show_summary


def analyze_with_llm(state: OrganizerState) -> OrganizerState:
    """
    Analyze files using configured LLM provider.
    
    Collects all analysis results (file metadata, image analysis, text analysis)
    and passes them to the LLM for organization suggestions.
    
    Args:
        state: Current graph state with files and analysis results
        
    Returns:
        Updated state with suggestions (SuggestionResponse)
    """
    update_progress("analyze_with_llm", "running")
    
    files = state.get("files") or []
    image_analysis = state.get("image_analysis") or []
    text_analysis = state.get("text_analysis") or []
    document_analysis = state.get("document_analysis") or []
    aggregated = state.get("aggregated_analysis") or {}
    
    llm_provider = state.get("llm_provider", "ollama")
    llm_model = state.get("llm_model")
    errors = state.get("errors", []).copy()
    warnings = state.get("warnings", []).copy()
    
    # Check if we have files to analyze
    if not files:
        errors.append("No files to analyze")
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
        return state
    
    # Create provider
    try:
        provider = _create_provider(llm_provider, llm_model)
    except Exception as e:
        errors.append(f"Failed to create LLM provider: {str(e)}")
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
        return state
    
    # Check if provider is available
    if not provider.is_available():
        error_msg = _get_provider_unavailable_message(llm_provider, llm_model)
        errors.append(error_msg)
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
        return state
    
    # Build enriched analysis context
    analysis_context = {
        "image_analysis": image_analysis,
        "text_analysis": text_analysis,
        "document_analysis": document_analysis,
        "patterns": aggregated.get("image_patterns", {}),
        "dominant_type": aggregated.get("dominant_type", "mixed"),
    }
    
    # Analyze files with full context
    try:
        suggestion_response = provider.analyze(files, analysis_context)
        state["suggestions"] = suggestion_response
        update_progress("analyze_with_llm", "complete")
    except ProviderNotAvailableError as e:
        errors.append(f"Provider not available: {str(e)}")
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
    except ProviderAPIError as e:
        errors.append(f"Provider API error: {str(e)}")
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
    except ProviderParseError as e:
        errors.append(f"Failed to parse provider response: {str(e)}")
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
    except Exception as e:
        errors.append(f"Unexpected error during LLM analysis: {str(e)}")
        state["errors"] = errors
        update_progress("analyze_with_llm", "error")
    
    state["errors"] = errors
    state["warnings"] = warnings
    
    show_summary(state)

    try:
        state["suggestions"] = apply_preferences(state["suggestions"])
    except Exception as e:
        # Don't fail if preferences can't be applied
        warnings.append(f"Could not apply preferences: {str(e)}")
        state["warnings"] = warnings

    return state


def _create_provider(provider_type: str, model: str = None):
    """
    Create the appropriate LLM provider.
    
    Args:
        provider_type: "ollama" or "api"
        model: Optional model name
        
    Returns:
        Provider instance
        
    Raises:
        ValueError: If provider_type is invalid
    """
    if provider_type == "ollama":
        return OllamaProvider(model=model or "llama3.2:3b")
    else:
        raise ValueError(f"Invalid provider type: {provider_type}. Must be 'ollama' or 'api'")


def _get_provider_unavailable_message(provider_type: str, model: str = None) -> str:
    """
    Get helpful error message for unavailable provider.
    """
    if provider_type == "ollama":
        model_name = model or "llama3.2:3b"
        return (
            f"Ollama is not running or model '{model_name}' is not installed.\n"
            f"Please ensure Ollama is running and the model is installed:\n"
            f"  1. Start Ollama: ollama serve\n"
            f"  2. Install model: ollama pull {model_name}"
        )
    elif provider_type == "api":
        return (
            "Anthropic API key not configured.\n"
            "Please set the ANTHROPIC_API_KEY environment variable."
        )
    else:
        return f"Unknown provider type: {provider_type}"