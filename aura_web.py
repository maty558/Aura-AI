"""Streamlit front-end pre Aura AI — nahrávanie, analýza a stiahnutie.

Poskytuje režimy analýzy dokumentov a jednoduché poradenstvo.
"""

import os
from typing import List

from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF

# 1. NASTAVENIA
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Chýba API kľúč v .env!")
    st.stop()

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Aura AI - Ochranár", page_icon="🛡️", layout="wide")


# Funkcia na tvorbu PDF
def create_pdf(text_content: str, user_name: str) -> bytes:
    """Vytvorí jednoduché PDF z textu a vráti ho ako `bytes`."""
    pdf = FPDF()
    pdf.add_page()
    # Pridanie fontu (štandardné fonty v FPDF nemusia vedieť slovenské diakritiku,
    # preto pre jednoduchosť použijeme 'Helvetica'; odporúča sa neskôr pridať Unicode font)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(40, 10, "Aura AI - Protokol o analyze")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(40, 10, f"Pripravene pre: {user_name}")
    pdf.ln(15)

    # Rozdelenie textu na riadky pre PDF
    pdf.multi_cell(0, 5, text_content.encode("latin-1", "replace").decode("latin-1"))

    # Získať output ako reťazec alebo bytes a zabezpečiť návrat typu `bytes`.
    out = pdf.output()
    if isinstance(out, str):
        return out.encode("latin-1")
    if isinstance(out, bytearray):
        return bytes(out)
    return out


def get_best_model() -> str:
    """Vyberie najvhodnejší model zo zoznamu dostupných modelov.

    Preferuje modely obsahujúce text "flash", inak vráti prvý dostupný
    alebo predvolený fallback.
    """
    try:
        available_models: List[str] = []
        for m in genai.list_models():
            if hasattr(m, "supported_generation_methods") and (
                "generateContent" in m.supported_generation_methods
            ) and hasattr(m, "name"):
                available_models.append(m.name)

        if not available_models:
            return "models/gemini-1.5-flash"

        return next((m for m in available_models if "flash" in m), available_models[0])
    except Exception:  # pylint: disable=broad-except
        return "models/gemini-1.5-flash"


if "history" not in st.session_state:
    st.session_state["history"] = []


# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Profil")
    u_name = st.text_input("Meno", value="Pouzivatel")
    st.divider()
    st.subheader("📜 Historia")
    for entry in reversed(st.session_state["history"]):
        st.info(entry)


# --- HLAVNA CAST ---
st.title("🛡️ Aura AI - Expert na zmluvy")


# 👁️ REŽIM: UKÁŽ MI (Súbory / Porovnávanie)
with st.expander("👁️ Režim: Analýza a Porovnávanie", expanded=True):
    uploaded_files = st.file_uploader(
        "Nahraj jeden alebo dva súbory (PDF/Obrázky)",
        type=["jpg", "png", "pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("🚀 Spustiť analýzu"):
            with st.spinner("Aura pracuje..."):
                try:
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name)

                    content = []
                    if len(uploaded_files) == 1:
                        PROMPT = (
                            "Analyzuj tento dokument. Identifikuj riziká a kľúčové fakty "
                            "v slovenčine."
                        )
                        f = uploaded_files[0]
                        if f.type == "application/pdf":
                            content.append({"mime_type": "application/pdf", "data": f.read()})
                        else:
                            content.append(Image.open(f))
                    else:
                        PROMPT = (
                            "Porovnaj tieto DVA dokumenty. Nájdi rozdiely, upozorni na zmeny "
                            "v neprospech spotrebiteľa a napíš, ktorý je výhodnejší. "
                            "Odpovedaj v slovenčine."
                        )
                        for f in uploaded_files:
                            if f.type == "application/pdf":
                                content.append({"mime_type": "application/pdf", "data": f.read()})
                            else:
                                content.append(Image.open(f))

                    content.insert(0, PROMPT)
                    response = model.generate_content(content)

                    # ZOBRAZENIE VÝSLEDKU
                    st.markdown("### 📊 Výsledok od Aury")
                    analysis_text = response.text  # pylint: disable=invalid-name
                    st.write(analysis_text)

                    # TLAČIDLO NA STIAHNUTIE PDF
                    pdf_data = create_pdf(analysis_text, u_name)
                    st.download_button(
                        label="📥 Stiahnuť analýzu (PDF)",
                        data=pdf_data,
                        file_name="Aura_Analyza.pdf",
                        mime="application/pdf",
                    )

                    st.session_state["history"].append(f"Analyza: {len(uploaded_files)} subor(ov)")

                except Exception as e:  # pylint: disable=broad-except
                    st.error(f"Chyba: {e}")


# 💬 REŽIM: POMÔŽ MI
with st.expander("💬 Režim: Rýchla rada"):
    user_q = st.text_area("Otázka:")
    if st.button("Poraď"):
        model = genai.GenerativeModel(get_best_model())
        resp = model.generate_content(user_q)
        st.write(resp.text)
