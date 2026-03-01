import os
import time
from dotenv import load_dotenv
import google.generativeai as genai  # type: ignore[reportPrivateImportUsage]
from google.api_core import exceptions as api_exceptions
from typing import Any

# 1. NASTAVENIE (Tu vložíš svoj API kľúč neskôr)
# Načítaj .env a použij fallback: najprv GOOGLE_API_KEY, potom API_KEY
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
if api_key:
    genai.configure(api_key=api_key)
# Ak nie je API kľúč, necháme to na volajúcej aplikácii alebo testovacom behu

# Zoznam modelov podľa priority (prvý je preferovaný)
model_candidates = [
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-flash-latest",
    "models/gemini-flash-lite",
]

# Helper: create a model instance for a given model resource name
def _make_model(name) -> Any:
    return genai.GenerativeModel(name)  # type: ignore[reportPrivateImportUsage]

def get_aura_response(user_input, mode="Ukáž mi"):
    full_prompt = f"{mode}: {user_input}"
    last_exc = None
    for idx, candidate in enumerate(model_candidates):
        try:
            m = _make_model(candidate)
            response = m.generate_content(full_prompt)
            return response.text
        except api_exceptions.NotFound as nf:
            # model nie je dostupný pre túto verziu/účt
            last_exc = nf
            continue
        except api_exceptions.ResourceExhausted as rex:
            # kvóta vyčerpaná pre tento model — skús ďalší model po krátkom backoffe
            last_exc = rex
            backoff = min(2 ** idx, 8)
            time.sleep(backoff)
            continue
        except Exception as e:
            # iné chyby — zapamätaj a pokračuj skúsiť ďalší model
            last_exc = e
            continue

    # Ak sme sa sem dostali, nepodarilo sa získať odpoveď z žiadneho modelu
    if isinstance(last_exc, api_exceptions.ResourceExhausted):
        raise RuntimeError(
            "Kvóta pre modely je vyčerpaná. Skontroluj fakturáciu / kvóty v Google Cloud Console."
        ) from last_exc
    if isinstance(last_exc, api_exceptions.NotFound):
        raise RuntimeError(
            "Požadované modely nie sú dostupné pre tvoje API/verziu. Spusti ListModels a vyber dostupný model."
        ) from last_exc
    # Iný posledný výnimok
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Neočakovaná chyba pri volaní generatívneho modelu.")

# --- TESTOVACÍ BEH (spustí sa len pri priamej exekúcii) ---
test_vstup = "Reklamácia topánok zamietnutá po 3 mesiacoch. Dôvod: nesprávne používanie. Bez posudku."

if __name__ == "__main__":
    print(get_aura_response(test_vstup))

