import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
if not api_key:
    raise SystemExit("GOOGLE_API_KEY (or API_KEY) not found in .env")

import google.generativeai.client as gen_client
import google.generativeai as genai

# configure
genai.configure(api_key=api_key)

try:
    client = gen_client.get_default_generative_client()
    # Some client versions don't expose list_models on this object; try and fall back.
    try:
        resp = client.list_models()
        print("Available models (via client):")
        for m in resp.models:
            name = getattr(m, "name", None)
            methods = getattr(m, "supported_methods", None)
            print(name, methods)
    except AttributeError:
        # Fallback: call REST endpoint directly using requests
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        print("Available models (via REST):")
        for item in data.get("models", []):
            print(item.get("name"), item.get("supportedMethods") or item.get("supported_methods"))
except Exception as e:
    print("Error while listing models:", e)
    raise
