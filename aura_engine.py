"""Helpers for contacting generative models with fallback and backoff.

Provides a small helper for trying several candidate models and returning
the first successful response text.
"""

# Temporarily disable trailing-newlines warning where editors/OS line endings
# may introduce extra blank lines at EOF on Windows.
# pylint: disable=trailing-newlines

import os
import time
from typing import Any

from dotenv import load_dotenv
import google.generativeai as genai  # type: ignore[reportPrivateImportUsage]
from google.api_core import exceptions as api_exceptions

# Load configuration from .env and configure the SDK if an API key exists.
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Candidate model resource names in preferred order.
model_candidates = [
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-flash-latest",
    "models/gemini-flash-lite",
]


def _make_model(name: str) -> Any:
    """Return a GenerativeModel instance for the given resource name."""
    return genai.GenerativeModel(name)  # type: ignore[reportPrivateImportUsage]


def get_aura_response(user_input: str, mode: str = "Ukáž mi") -> str:
    """Try candidate models in order and return the first successful text.

    If no model succeeds the function raises a helpful RuntimeError.
    """
    full_prompt = f"{mode}: {user_input}"
    last_exc = None
    for idx, candidate in enumerate(model_candidates):
        try:
            m = _make_model(candidate)
            response = m.generate_content(full_prompt)
            return response.text
        except api_exceptions.NotFound as nf:
            last_exc = nf
            continue
        except api_exceptions.ResourceExhausted as rex:
            last_exc = rex
            backoff = min(2 ** idx, 8)
            time.sleep(backoff)
            continue
        except Exception as e:  # pylint: disable=broad-except
            last_exc = e
            continue

    # If we reach here, no candidate produced a response.
    if isinstance(last_exc, api_exceptions.ResourceExhausted):
        raise RuntimeError(
            "Kvóta pre modely je vyčerpaná. Skontroluj fakturáciu alebo kvóty "
            "v Google Cloud Console."
        ) from last_exc
    if isinstance(last_exc, api_exceptions.NotFound):
        raise RuntimeError(
            "Požadované modely nie sú dostupné pre tvoje API/verziu. "
            "Spusti list_models a vyber dostupný model."
        ) from last_exc
    if last_exc is not None:
        raise last_exc

    raise RuntimeError("Neočakávaná chyba pri volaní generatívneho modelu.")


# End of module. Test runner removed.

