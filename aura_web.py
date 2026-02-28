import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import io
try:
    import PyPDF2
except Exception:
    PyPDF2 = None
try:
    import pytesseract
except Exception:
    pytesseract = None
import time
from google.api_core import exceptions as api_exceptions

# 1. NASTAVENIA A PAMÄŤ
load_dotenv()
# fallback: najprv GOOGLE_API_KEY, potom API_KEY
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Chýba API kľúč! Nastav GOOGLE_API_KEY alebo API_KEY v .env")

# Poradie modelov (fallback pri kvótach / NotFound)
model_candidates = [
    "models/text-bison-001",           # text-focused model (commonly available)
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-flash-latest",
    "models/gemini-flash-lite",
]

st.set_page_config(page_title="Aura AI", page_icon="🛡️", layout="wide")

# Inicializácia histórie (Session State)
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- BOČNÝ PANEL (PROFIL A HISTÓRIA) ---
with st.sidebar:
    st.title("👤 Profil používateľa")
    # Tu sú polia, ktoré si chcel doplniť
    user_name = st.text_input("Meno", placeholder="Tvoje meno")
    user_email = st.text_input("E-mail", placeholder="priklad@mail.sk")
    user_age = st.number_input("Vek", min_value=0, max_value=120, value=25)
    
    st.divider()
    st.subheader("📜 Moja história")
    if st.session_state['history']:
        for i, item in enumerate(reversed(st.session_state['history'])):
            st.write(f"{len(st.session_state['history'])-i}. {item}")
        
        if st.button("Vymazať všetko"):
            st.session_state['history'] = []
            st.rerun()
    else:
        st.info("Zatiaľ žiadna aktivita.")

# --- HLAVNÁ ČASŤ APLIKÁCIE ---
st.title(f"🛡️ Aura")
if 'user_name' in locals() and user_name:
    st.write(f"Vitaj, **{user_name}**. Som pripravená ťa chrániť.")
else:
    st.write("Som tvoj inteligentný ochranár. Povedz mi, čo sa deje.")

# SEKCIA: UKÁŽ MI (FOTO aj PDF)
st.header("👁️ Režim: Ukáž mi")

# 1. Tu sme pridali 'pdf' do zoznamu povolených formátov
upload = st.file_uploader("Odfoť alebo nahraj dokument (JPG, PNG, PDF)", type=['jpg', 'png', 'jpeg', 'pdf'])

if upload:
    # Kontrola, či ide o PDF alebo obrázok pre zobrazenie náhľadu
    if upload.type == "application/pdf":
        st.write("📄 Súbor PDF bol úspešne nahraný.")
    else:
        img = Image.open(upload)
        st.image(img, caption="Náhľad dokumentu", width=400)
    
    if st.button("Analyzuj dokument"):
        with st.spinner("Aura číta dokument (môže to trvať chvíľu)..."):
            prompt = "Si Aura, ochranársky asistent. Analyzuj tento dokument. Čo to je? Nájdi 🚩 RIZIKO, ✅ FAKT a 🚀 AKCIA."

            # Pokúsime sa najprv extrahovať text lokálne (PDF alebo OCR z obrázka)
            extracted_text = None
            if upload.type == "application/pdf":
                pdf_data = upload.read()
                if PyPDF2 is not None:
                    try:
                        reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
                        pages = [p.extract_text() or "" for p in reader.pages]
                        extracted_text = "\n".join(pages).strip()
                    except Exception:
                        extracted_text = None
                else:
                    extracted_text = None
            else:
                # obrázok
                img_obj = Image.open(upload)
                if pytesseract is not None:
                    try:
                        extracted_text = pytesseract.image_to_string(img_obj).strip()
                    except Exception:
                        extracted_text = None

            response = None
            last_exc = None
            for idx, candidate in enumerate(model_candidates):
                try:
                    model = genai.GenerativeModel(candidate)
                    # prefer text model when we have extracted text
                    if candidate.startswith("models/text"):
                        if extracted_text:
                            combined = f"{prompt}\n\nExtrahovaný text:\n{extracted_text}"
                            response = model.generate_content(combined)
                            break
                        else:
                            continue
                    else:
                        # multimodálne modely: poslať pôvodné dáta
                        if upload.type == "application/pdf":
                            response = model.generate_content([
                                prompt,
                                {'mime_type': 'application/pdf', 'data': pdf_data}
                            ])
                        else:
                            response = model.generate_content([prompt, img_obj])
                        break
                except api_exceptions.ResourceExhausted as rex:
                    last_exc = rex
                    backoff = min(2 ** idx, 8)
                    time.sleep(backoff)
                    continue
                except api_exceptions.NotFound as nf:
                    last_exc = nf
                    continue
                except Exception as e:
                    last_exc = e
                    continue

            if response is None:
                if isinstance(last_exc, api_exceptions.ResourceExhausted):
                    st.error("Kvóta vyčerpaná pre použité modely. Skontroluj fakturáciu / kvóty.")
                elif isinstance(last_exc, api_exceptions.NotFound):
                    st.error("Požadované modely nie sú dostupné pre tvoje API/verziu.")
                else:
                    st.error(f"Chyba pri volaní modelu: {last_exc}")
            else:
                st.session_state['history'].append(f"Dokument: {response.text[:40]}...")
                st.subheader("Výsledok analýzy:")
                st.write(response.text)

st.divider()

# SEKCIA: POMÔŽ MI (TEXT)
st.header("💬 Režim: Pomôž mi")
problem = st.text_area("Popíš svoju situáciu:")

if st.button("Vyrieš to"):
    if problem:
        with st.spinner("Hľadám riešenie..."):
            response = None
            last_exc = None
            for idx, candidate in enumerate(model_candidates):
                try:
                    model = genai.GenerativeModel(candidate)
                    response = model.generate_content(f"Si Aura, ochranár. Vyrieš toto: {problem}")
                    break
                except api_exceptions.ResourceExhausted as rex:
                    last_exc = rex
                    backoff = min(2 ** idx, 8)
                    time.sleep(backoff)
                    continue
                except api_exceptions.NotFound as nf:
                    last_exc = nf
                    continue
                except Exception as e:
                    last_exc = e
                    continue

            if response is None:
                if isinstance(last_exc, api_exceptions.ResourceExhausted):
                    st.error("Kvóta vyčerpaná pre použité modely. Skontroluj fakturáciu / kvóty.")
                elif isinstance(last_exc, api_exceptions.NotFound):
                    st.error("Požadované modely nie sú dostupné pre tvoje API/verziu.")
                else:
                    st.error(f"Chyba pri volaní modelu: {last_exc}")
            else:
                st.session_state['history'].append(f"Text: {problem[:40]}...")
                st.write(response.text)