"""DataForge Content Crew - Google Gemini API Service Adapter
Phase 3: LLM Integration and Provider Adapter
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env in project root
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger("gemini_service")

# Global mock provider for testing and offline environments
_mock_responder = None

# Reliable fallback models in case primary model hits rate limit or quota exhaustion (429)
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]


def get_gemini_config() -> Dict[str, Any]:
    """Retrieves Gemini configuration from environment variables."""
    # Ensure any newly created or modified .env file is loaded
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=False)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    # Default model: gemini-2.5-flash or gemini-1.5-flash
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

    placeholder_keys = {
        "your_gemini_api_key_here",
        "your-gemini-api -key",
        "your-gemini-api-key",
        "<your-api-key>",
        ""
    }
    is_configured = bool(api_key and api_key.lower() not in placeholder_keys and not api_key.startswith("<"))

    return {
        "api_key": api_key,
        "model": model,
        "is_configured": is_configured
    }


def set_mock_responder(responder_func):
    """Sets a mock responder for unit testing without paid API credentials."""
    global _mock_responder
    _mock_responder = responder_func


def get_gemini_client():
    """Initializes the official google.genai Client using environment credentials."""
    config = get_gemini_config()
    if not config["is_configured"]:
        return None

    try:
        from google import genai
        return genai.Client(api_key=config["api_key"])
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI client: {e}")
        return None


def test_gemini_connection() -> Tuple[bool, str, Dict[str, Any]]:
    """Makes a lightweight test request only when credentials are fully configured.
    
    Returns (success, message, metadata).
    """
    config = get_gemini_config()
    if not config["is_configured"]:
        return False, "Gemini API key is not configured. Add GEMINI_API_KEY to your .env file.", {
            "configured": False,
            "model": config["model"]
        }

    # If mock responder is active (e.g. in test suite)
    if _mock_responder:
        return True, "Mock Gemini connection verified.", {"configured": True, "model": config["model"], "mocked": True}

    client = get_gemini_client()
    if not client:
        return False, "Could not initialize Gemini SDK client.", {"configured": True, "model": config["model"]}

    # Candidate models to try: configured model first, followed by fallbacks
    models_to_try = [config["model"]] + [m for m in FALLBACK_MODELS if m != config["model"]]
    last_err = ""

    for model_name in models_to_try:
        try:
            # Minimal single-token verification prompt
            response = client.models.generate_content(
                model=model_name,
                contents="ping",
            )
            if response and response.text:
                return True, f"Successfully connected to Gemini API using model {model_name}.", {
                    "configured": True,
                    "model": model_name,
                    "status": "active"
                }
        except Exception as e:
            err_str = str(e)
            last_err = err_str
            logger.warning(f"Connection test with model {model_name} failed: {err_str[:90]}")
            # If API key is fundamentally invalid, do not try other models
            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                return False, "Configured GEMINI_API_KEY was rejected by Google AI Studio.", {
                    "configured": True,
                    "model": model_name,
                    "error": "Invalid API Key"
                }
            # Otherwise continue to next fallback model
            continue

    if "RESOURCE_EXHAUSTED" in last_err or "429" in last_err:
        msg = "Gemini API quota or rate limit exceeded on available models."
    elif "DEADLINE_EXCEEDED" in last_err or "timeout" in last_err.lower():
        msg = "Gemini API connection timed out."
    else:
        msg = f"Gemini API connection error: {last_err[:100]}"
    return False, msg, {"configured": True, "model": config["model"], "error": msg}


def generate_content(
    prompt: str,
    system_instruction: Optional[str] = None,
    json_mode: bool = False,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """Generates text or structured JSON using the configured Gemini model.
    
    If credentials are not available, produces a transparent, deterministic fallback.
    """
    config = get_gemini_config()

    # 1. Check for registered test mock
    if _mock_responder:
        res = _mock_responder(prompt, system_instruction, json_mode)
        return {
            "status": "success",
            "text": res if isinstance(res, str) else json.dumps(res),
            "model": f"{config['model']}-mock",
            "is_live_ai": False
        }

    # 2. Check if live credentials exist
    if not config["is_configured"]:
        return {
            "status": "unconfigured",
            "text": "",
            "error": "GEMINI_API_KEY is not configured.",
            "is_live_ai": False
        }

    # 3. Live call via google.genai with intelligent fallback
    client = get_gemini_client()
    if not client:
        return {
            "status": "error",
            "text": "",
            "error": "Failed to initialize Gemini client.",
            "is_live_ai": False
        }

    import re
    from google.genai import types

    config_params = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction
    )
    if json_mode:
        config_params.response_mime_type = "application/json"

    models_to_try = [config["model"]] + [m for m in FALLBACK_MODELS if m != config["model"]]
    last_err_msg = ""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config_params
            )

            generated_text = ""
            if response:
                try:
                    generated_text = response.text or ""
                except Exception:
                    generated_text = ""

            if generated_text:
                return {
                    "status": "success",
                    "text": generated_text,
                    "model": model_name,
                    "is_live_ai": True
                }

            last_err_msg = f"Model {model_name} returned empty text."
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Gemini generation error on model {model_name}: {err_str[:90]}")
            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                return {
                    "status": "error",
                    "text": "",
                    "error": "Invalid Gemini API key provided.",
                    "is_live_ai": False
                }
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "NOT_FOUND" in err_str:
                last_err_msg = f"Quota exceeded for {model_name}; trying fallback model..."
                continue
            last_err_msg = f"Gemini provider error: {err_str[:100]}"
            break

    return {
        "status": "error",
        "text": "",
        "error": last_err_msg or "All Gemini models were unavailable or exceeded rate limits.",
        "is_live_ai": False
    }
