"""Aura Streamlit frontend: upload/analyze PDFs and images using Gemini.

Provides a small UI with two modes: document analysis and text advice.
"""

import os
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai  # type: ignore[reportPrivateImportUsage]
from PIL import Image
from typing import Any


# Load configuration
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")

if not API_KEY:
    st.set_page_config(page_title="Aura AI - Ochranár", page_icon="🛡️", layout="wide")
    st.error("❌ Chýba API kľúč v súbore .env! Prosím, pridaj ho.")
    st.stop()

genai.configure(api_key=API_KEY)

# Page config
st.set_page_config(page_title="Aura AI - Ochranár", page_icon="🛡️", layout="wide")

# Session state
if 'history' not in st.session_state:
    st.session_state['history'] = []


def _select_model_name(fallback: str = "models/gemini-1.5-flash") -> str:
    try:
        models = genai.list_models()
        names = []
        for m in models:
            name = getattr(m, 'name', None)
            if name:
                names.append(name)
        if not names:
            return fallback
        # prefer any model containing 'flash' then 'gemini', else first
        for n in names:
            if 'flash' in n:
                return n
        for n in names:
            if 'gemini' in n:
                return n
        return names[0]
    except Exception:  # pylint: disable=broad-except
        return fallback


# Sidebar
with st.sidebar:
    st.title("👤 Profil používateľa")
    u_name = st.text_input("Meno", value="Používateľ")
    u_email = st.text_input("E-mail", placeholder="email@priklad.sk")
    st.divider()
    st.subheader("📜 História analýz")
    if st.session_state['history']:
        for entry in reversed(st.session_state['history']):
            st.info(entry)
        if st.button("Vymazať históriu"):
            st.session_state['history'] = []
            getattr(st, "experimental_rerun", lambda: None)()
    else:
        st.write("Zatiaľ žiadna aktivita.")


# Main
st.title("🛡️ Aura")
st.subheader(f"Vitaj, {u_name}. Čo dnes skontrolujeme?")


with st.expander("👁️ Režim: Ukáž mi (Nahrať dokument)", expanded=True):
    uploaded_file = st.file_uploader(
        "Vlož fotku (JPG, PNG) alebo PDF",
        type=['jpg', 'jpeg', 'png', 'pdf'],
    )
    if uploaded_file:
        if st.button("Analyzovať dokument"):
            with st.spinner("Aura analyzuje dokument..."):
                try:
                    model_name = _select_model_name()
                    model = genai.GenerativeModel(model_name)

                    ANALYSIS_PROMPT = (
                        "Si Aura, expert na ochranu spotrebiteľa. Analyzuj tento súbor. "
                        "Identifikuj: 1. Typ dokumentu, 2. RIZIKÁ. "
                        "3. KĽÚČOVÉ FAKTY. 4. ODPORÚČANÁ AKCIA. "
                        "Odpovedaj jasne v slovenčine."
                    )

                    content: Any = [ANALYSIS_PROMPT]
                    if uploaded_file.type == "application/pdf":
                        pdf_bytes = uploaded_file.read()
                        content.append({"mime_type": "application/pdf", "data": pdf_bytes})
                    else:
                        img = Image.open(uploaded_file)
                        content.append(img)

                    response = model.generate_content(content)
                    st.markdown("### 📊 Výsledok analýzy")
                    st.write(response.text)
                    st.session_state['history'].append(f"Analyzované: {uploaded_file.name}")
                except Exception as e:  # pylint: disable=broad-except
                    st.error(f"Nastala chyba pri analýze: {e}")


with st.expander("💬 Režim: Pomôž mi (Text)"):
    user_input = st.text_area("Popíš svoju situáciu (napr. 'E-shop mi nechce vrátiť peniaze'):")
    if st.button("Získať radu"):
        if user_input:
            with st.spinner("Hľadám najlepšie riešenie..."):
                try:
                    model_name = _select_model_name()
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(f"Si Aura, poraď s týmto: {user_input}")
                    st.markdown("### 💡 Odporúčanie Aury")
                    st.write(response.text)
                    st.session_state['history'].append(f"Otázka: {user_input[:30]}...")
                except Exception as e:  # pylint: disable=broad-except
                    st.error(f"Chyba: {e}")
