import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
from fpdf import FPDF
import io

# 1. NASTAVENIA
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Chýba API kľúč v .env!")
    st.stop()

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Aura AI - Ochranár", page_icon="🛡️", layout="wide")

# Pomocná funkcia pre PDF (vylepšená stabilita textu)
def create_pdf(text_content, user_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Aura AI - Protokol o analyze", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Pripravene pre: {user_name}", ln=True)
    pdf.ln(10)
    
    # Vyčistenie textu pre PDF (FPDF1/2 Helvetica nepodporuje všetky SK znaky bez externých fontov)
    clean_text = text_content.replace('č', 'c').replace('š', 's').replace('ž', 'z').replace('ť', 't').replace('ľ', 'l').replace('ý', 'y').replace('á', 'a').replace('í', 'i').replace('é', 'e').replace('ú', 'u').replace('ä', 'a').replace('ň', 'n').replace('ô', 'o')
    
    pdf.multi_cell(0, 7, clean_text)
    return pdf.output()

def get_best_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return next((m for m in available_models if "flash" in m), available_models[0])
    except:
        return "models/gemini-1.5-flash"

if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Profil")
    u_name = st.text_input("Meno", value="Pouzivatel")
    st.divider()
    st.subheader("📜 Historia")
    for entry in reversed(st.session_state['history']):
        st.info(entry)

# --- HLAVNA CAST ---
st.title("🛡️ Aura AI")
st.markdown("Identifikujem háčiky v zmluvách a chránim tvoje práva.")

# 👁️ REŽIM: UKÁŽ MI (Analýza podľa tvojho zadania)
with st.expander("👁️ Režim: Analýza dokumentov", expanded=True):
    uploaded_files = st.file_uploader("Nahraj súbor(y) (PDF/Obrázky)", type=['jpg', 'png', 'pdf'], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("🚀 Spustiť analýzu"):
            with st.spinner("Aura preveruje dokumenty..."):
                try:
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name)
                    
                    content = []
                    
                    # HLAVNÝ PROMPT PODĽA TVOJHO ZADANIA
                    base_prompt = """
                    Si Aura, nekompromisný expert na ochranu spotrebiteľa. 
                    Tvojou úlohou je analyzovať priložené dokumenty a odpovedať striktne v tomto formáte:

                    🚩 RIZIKO: (Identifikuj háčik, skrytý poplatok alebo právny problém)
                    ✅ FAKT: (Zhrnutie reality v maximálne 2 vetách)
                    🚀 AKCIA: (Krok za krokom, čo má používateľ urobiť - stručne a jasne)

                    Odpovedaj v slovenčine. Ak sú dokumenty dva, porovnaj ich v rámci tohto formátu.
                    """
                    
                    content.append(base_prompt)
                    
                    for f in uploaded_files:
                        if f.type == "application/pdf":
                            content.append({'mime_type': 'application/pdf', 'data': f.read()})
                        else:
                            content.append(Image.open(f))
                    
                    response = model.generate_content(content)
                    
                    # Zobrazenie
                    st.markdown("### 📊 Výsledok od Aury")
                    st.info(response.text)
                    
                    # Príprava PDF
                    pdf_data = create_pdf(response.text, u_name)
                    st.download_button(
                        label="📥 Stiahnuť protokol (PDF)",
                        data=pdf_data,
                        file_name="Aura_Protokol.pdf",
                        mime="application/pdf"
                    )
                    
                    st.session_state['history'].append(f"Analyza: {uploaded_files[0].name}")
                    
                except Exception as e:
                    st.error(f"Chyba: {e}")

# 💬 REŽIM: POMÔŽ MI
with st.expander("💬 Režim: Rýchla rada"):
    user_q = st.text_area("V čom máš problém?")
    if st.button("Dostať radu"):
        if user_q:
            model = genai.GenerativeModel(get_best_model())
            # Aj tu držíme tón Aury
            resp = model.generate_content(f"Si Aura, expert na spotrebiteľov. Stručne poraď používateľovi s týmto: {user_q}")
            st.success(resp.text)