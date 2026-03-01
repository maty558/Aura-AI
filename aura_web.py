import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
from fpdf import FPDF
import io
from typing import Any, cast

# 1. NASTAVENIA A KONFIGURÁCIA
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Chýba API kľúč v .env!")
    st.stop()

genai.configure(api_key=API_KEY)

# Nastavenie vzhľadu stránky (Aura Identita)
st.set_page_config(page_title="Aura AI - Ochranca v mobile", page_icon="🛡️", layout="wide")

# POMOCNÁ FUNKCIA PRE GENEROVANIE PDF (Protokoly a dokumenty)
def create_pdf(text_content, user_name, title="Aura AI - Dokument"):
    pdf = FPDF()
    pdf.add_page()
    font_path = "DejaVuSans.ttf" # Uisti sa, že máš tento súbor v priečinku
    font_loaded = False
    
    if os.path.exists(font_path):
        try:
            pdf.add_font('SlovakFont', '', font_path)
            pdf.set_font('SlovakFont', '', 12)
            font_loaded = True
        except:
            pdf.set_font("Helvetica", "", 12)
    else:
        pdf.set_font("Helvetica", "", 12)

    if font_loaded:
        pdf.set_font('SlovakFont', '', 16)
        pdf.cell(0, 10, title, ln='DEPRECATED')
        pdf.set_font('SlovakFont', '', 10)
        pdf.cell(0, 10, f"Vytvorené pre: {user_name} | Dátum: 2026", ln='DEPRECATED')
    else:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, title + " (Bez diakritiky)", ln='DEPRECATED')
    
    pdf.ln(10)
    if font_loaded:
        pdf.set_font('SlovakFont', '', 11)
        pdf.multi_cell(0, 7, text_content)
    else:
        clean_text = text_content.encode('ascii', 'ignore').decode('ascii')
        pdf.multi_cell(0, 7, clean_text)
        
    out = cast(Any, pdf).output("", "S")
    if isinstance(out, str):
        out = out.encode("utf-8")
    elif isinstance(out, bytearray):
        out = bytes(out)
    return out

def get_best_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return next((m for m in available_models if "flash" in m), available_models[0])
    except:
        return "models/gemini-1.5-flash"

# Inicializácia pamäte relácie
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- BOČNÝ PANEL (Profil a História) ---
with st.sidebar:
    st.title("🛡️ Aura Profil")
    u_name = st.text_input("Používateľ", value="Majo")
    st.divider()
    st.subheader("📜 Archív aktivít")
    if st.session_state['history']:
        for entry in reversed(st.session_state['history']):
            st.info(entry)
    else:
        st.write("Zatiaľ žiadne záznamy.")

# --- HLAVNÉ MENU PROJEKTU AURA ---
st.title("🛡️ Aura AI")
st.markdown("### *Ochranca v mobile*")
st.write("Filtrujem zložitosť sveta za teba.")

# 1. MODUL: UKÁŽ MI (Skenovanie a vizuálna pomoc)
with st.expander("👁️ „Ukáž mi“ (Analýza dokumentov)", expanded=False):
    st.write("Nahraj fotku zmluvy, listu alebo bločku. Identifikujem riziká.")
    uploaded_files = st.file_uploader("Nahraj súbor(y)", type=['jpg', 'png', 'pdf'], accept_multiple_files=True, key="ukaz_mi")
    
    if uploaded_files:
        if st.button("🚀 Analyzovať realitu"):
            with st.spinner("Aura skenuje obsah..."):
                model = genai.GenerativeModel(get_best_model())
                prompt = (
                    "Si Aura, expert na ochranu spotrebiteľa a digitálnu bezpečnosť. "
                    "Analyzuj tento dokument a štruktúruj odpoveď takto:\n"
                    "1. Čo je to za dokument?\n"
                    "2. 🚩 RIZIKÁ (ak nejaké existujú)\n"
                    "3. ✅ KĽÚČOVÉ FAKTY (termíny, sumy, podmienky)\n"
                    "4. 🚀 ODPORÚČANÁ AKCIA (čo má používateľ urobiť).\n"
                    "Odpovedaj v slovenčine, buď stručný a jasný."
                )
                content: list[Any] = [prompt]
                for f in uploaded_files:
                    if f.type == "application/pdf":
                        content.append({'mime_type': 'application/pdf', 'data': f.read()})
                    else:
                        content.append(cast(Any, Image.open(f)))
                
                response = model.generate_content(content)
                st.markdown("---")
                st.info(response.text)
                
                pdf_report = create_pdf(response.text, u_name, "Aura Protokol - Analýza dokumentu")
                st.download_button("📥 Stiahnuť analýzu (PDF)", pdf_report, "Aura_Analyza.pdf", "application/pdf")
                st.session_state['history'].append(f"Ukáž mi: {uploaded_files[0].name}")

# 2. MODUL: POMÔŽ MI (Texty, úrady, riešenia)
with st.expander("💬 „Pomôž mi“ (Riešenie a dokumentácia)", expanded=True):
    st.write("Popíš problém (reklamácia, odvolanie, spor). Aura pripraví právny základ a text listu.")
    user_issue = st.text_area("Popis problému:", placeholder="Napr.: Chcem reklamovať topánky, ale obchod mi neuznal reklamáciu...")
    
    if st.button("💡 Navrhni riešenie"):
        if user_issue:
            with st.spinner("Aura hľadá riešenie..."):
                model = genai.GenerativeModel(get_best_model())
                help_prompt = (
                    f"Si Aura, digitálny ochranár. Na základe problému: '{user_issue}' urob:\n"
                    f"1. Právny základ (v 3 bodoch na čo má {u_name} nárok).\n"
                    f"2. Vypracuj formálny list (reklamáciu/odvolanie) s miestami na doplnenie v [ ].\n"
                    "Odpovedaj profesionálne v slovenčine."
                )
                res = model.generate_content(help_prompt)
                st.markdown("---")
                st.success(res.text)
                
                pdf_letter = create_pdf(res.text, u_name, "Aura Dokument - Riešenie")
                st.download_button("📥 Stiahnuť pripravený list (PDF)", pdf_letter, "Aura_Podklad.pdf", "application/pdf")
                st.session_state['history'].append(f"Pomôž mi: {user_issue[:20]}...")

# 3. MODUL: DOHLIADNI (Ochrana pri rozhovoroch a sporoch)
with st.expander("🎙️ „Dohliadni“ (Analýza rozhovoru)", expanded=False):
    st.info("VÝVOJ: Tento modul bude slúžiť na diskrétnu podporu pri rozhovoroch.")
    st.write("Tu bude prebiehať analýza textového prepisu rozhovoru pre detekciu manipulácie a nátlaku.")
    test_transcript = st.text_area("Vlož prepis rozhovoru (testovacia verzia):")
    if st.button("Analyzovať komunikáciu"):
        st.warning("Plná funkčnosť hlasovej analýzy bude pridaná v ďalšej fáze.")

# 4. MODUL: NAVIGUJ (Inteligentné pripomienky)
with st.expander("📍 „Naviguj“ (Kontextuálna pomoc)", expanded=False):
    st.info("VÝVOJ: Radar na tvoje práva v okolí.")
    st.write("Tento modul ťa upozorní na dôležité termíny a miesta (napr. koniec lehoty na reklamáciu, keď si v meste).")

st.divider()
st.caption("Aura AI - Projekt začatý 27. 2. 2026. Vízia: Ochranca v mobile.")