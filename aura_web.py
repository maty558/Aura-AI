import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# 1. NASTAVENIA
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Chýba API kľúč v súbore .env! Prosím, pridaj ho.")
    st.stop()

genai.configure(api_key=API_KEY)

# Konfigurácia stránky
st.set_page_config(page_title="Aura AI - Ochranár", page_icon="🛡️", layout="wide")

# Inicializácia histórie v pamäti prehliadača
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- BOČNÝ PANEL ---
with st.sidebar:
    st.title("👤 Profil používateľa")
    u_name = st.text_input("Meno", value="Používateľ")
    u_email = st.text_input("E-mail", placeholder="email@priklad.sk")
    
    st.divider()
    st.subheader("📜 História analýz")
    if st.session_state['history']:
        for i, entry in enumerate(reversed(st.session_state['history'])):
            st.info(f"{entry}")
        if st.button("Vymazať históriu"):
            st.session_state['history'] = []
            st.rerun()
    else:
        st.write("Zatiaľ žiadna aktivita.")

# --- HLAVNÁ ČASŤ ---
st.title("🛡️ Aura")
st.subheader(f"Vitaj, {u_name}. Čo dnes skontrolujeme?")

# Režim: UKÁŽ MI
with st.expander("👁️ Režim: Ukáž mi (Nahrať dokument)", expanded=True):
    uploaded_file = st.file_uploader("Vlož fotku (JPG, PNG) alebo PDF zmluvy", type=['jpg', 'jpeg', 'png', 'pdf'])
    
    if uploaded_file:
        if st.button("Analyzovať dokument"):
            with st.spinner("Aura dôkladne prezerá dokument..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Príprava obsahu pre Gemini
                    content = ["Si Aura, expert na ochranu spotrebiteľa. Analyzuj tento súbor. Identifikuj: 1. Typ dokumentu, 2. 🚩 RIZIKÁ, 3. ✅ KĽÚČOVÉ FAKTY, 4. 🚀 ODPORÚČANÁ AKCIA. Odpovedaj jasne v slovenčine."]
                    
                    if uploaded_file.type == "application/pdf":
                        pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.read()}]
                        content.extend(pdf_parts)
                    else:
                        img = Image.open(uploaded_file)
                        content.append(img)
                    
                    response = model.generate_content(content)
                    
                    # Zobrazenie výsledku
                    st.markdown("### 📊 Výsledok analýzy")
                    st.write(response.text)
                    
                    # Uloženie do histórie
                    st.session_state['history'].append(f"Analyzované: {uploaded_file.name}")
                    
                except Exception as e:
                    st.error(f"Nastala chyba pri analýze: {e}")

st.divider()

# Režim: POMÔŽ MI
with st.expander("💬 Režim: Pomôž mi (Popísať problém)"):
    user_input = st.text_area("Popíš svoju situáciu (napr. 'E-shop mi nechce vrátiť peniaze'):")
    
    if st.button("Získať radu"):
        if user_input:
            with st.spinner("Hľadám najlepšie riešenie..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Si Aura, asistent ochrany. Navrhni postup pre: {user_input}")
                st.markdown("### 💡 Odporúčanie Aury")
                st.write(response.text)
                st.session_state['history'].append(f"Otázka: {user_input[:30]}...")