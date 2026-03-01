import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# 1. NASTAVENIA API A KONFIGURÁCIA
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Chýba API kľúč v súbore .env! Prosím, pridaj ho.")
    st.stop()

genai.configure(api_key=API_KEY)

# Konfigurácia Streamlit stránky
st.set_page_config(
    page_title="Aura AI - Ochranár", 
    page_icon="🛡️", 
    layout="wide"
)

# Pomocná funkcia na dynamické získanie najlepšieho dostupného modelu
def get_best_model():
    try:
        # Zistíme, ktoré modely tvoj kľúč reálne vidí
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Hľadáme prioritne 'flash' verziu (rýchla a zadarmo)
        chosen = next((m for m in available_models if "flash" in m), None)
        if not chosen:
            # Ak flash nie je v zozname, vezmeme prvý dostupný model
            chosen = available_models[0] if available_models else "models/gemini-1.5-flash"
        return chosen
    except Exception:
        # Záložná možnosť pre prípad výpadku zoznamu
        return "models/gemini-1.5-flash"

# Inicializácia histórie analýz (st.session_state zostáva v pamäti počas relácie)
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- BOČNÝ PANEL (Sidebar) ---
with st.sidebar:
    st.title("👤 Profil používateľa")
    u_name = st.text_input("Meno", value="Používateľ")
    u_email = st.text_input("E-mail", placeholder="tvoj@email.sk")
    
    st.divider()
    st.subheader("📜 História aktivít")
    
    if st.session_state['history']:
        for entry in reversed(st.session_state['history']):
            st.info(entry)
        
        if st.button("🗑️ Vymazať históriu"):
            st.session_state['history'] = []
            st.rerun()
    else:
        st.write("Zatiaľ žiadna história.")

# --- HLAVNÁ ČASŤ APLIKÁCIE ---
st.title("🛡️ Aura AI")
st.markdown(f"**Ahoj {u_name}, som tvoj digitálny ochranár.** Pomôžem ti preveriť dokumenty alebo poradiť s právami spotrebiteľa.")

# 1. SEKICA: UKÁŽ MI (Skenovanie a nahrávanie)
with st.expander("👁️ Režim: Ukáž mi (Analýza dokumentu)", expanded=True):
    st.write("Nahraj fotografiu zmluvy, bločku alebo PDF súbor.")
    uploaded_file = st.file_uploader("Vyber súbor (JPG, PNG, PDF)", type=['jpg', 'jpeg', 'png', 'pdf'])
    
    if uploaded_file:
        # Zobrazenie náhľadu, ak ide o obrázok
        if uploaded_file.type != "application/pdf":
            img_preview = Image.open(uploaded_file)
            st.image(img_preview, caption="Náhľad dokumentu", width=300)
        else:
            st.write("📄 Dokument PDF je pripravený na analýzu.")

        if st.button("🚀 Spustiť analýzu"):
            with st.spinner("Aura dôkladne analyzuje obsah dokumentu..."):
                try:
                    # Dynamické získanie modelu
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name)
                    
                    # Definícia inštrukcií pre AI
                    prompt = (
                        "Si Aura, expert na ochranu spotrebiteľa a digitálnu bezpečnosť. "
                        "Analyzuj tento dokument a štruktúruj odpoveď takto:\n"
                        "1. Čo je to za dokument?\n"
                        "2. 🚩 RIZIKÁ (ak nejaké existujú)\n"
                        "3. ✅ KĽÚČOVÉ FAKTY (termíny, sumy, podmienky)\n"
                        "4. 🚀 ODPORÚČANÁ AKCIA (čo má používateľ urobiť).\n"
                        "Odpovedaj v slovenčine, buď stručný a jasný."
                    )
                    
                    content_to_send = []
                    content_to_send.append(prompt)
                    
                    # Spracovanie podľa typu súboru
                    if uploaded_file.type == "application/pdf":
                        pdf_bytes = uploaded_file.read()
                        content_to_send.append({'mime_type': 'application/pdf', 'data': pdf_bytes})
                    else:
                        img_data = Image.open(uploaded_file)
                        content_to_send.append(img_data)
                    
                    # Odoslanie do Gemini
                    response = model.generate_content(content_to_send)
                    
                    # Zobrazenie výsledku
                    st.markdown("---")
                    st.subheader("📊 Výsledok od Aury")
                    st.markdown(response.text)
                    
                    # Uloženie do histórie
                    st.session_state['history'].append(f"Analyzované: {uploaded_file.name}")
                    
                except Exception as e:
                    st.error(f"Nastala chyba pri komunikácii s AI: {e}")

# 2. SEKCIA: POMÔŽ MI (Textové otázky)
with st.expander("💬 Režim: Pomôž mi (Právna rada)"):
    st.write("Popíš svoj problém (napr. 'Chcem vrátiť tovar zakúpený v e-shope pred 10 dňami').")
    user_problem = st.text_area("Tvoj problém alebo otázka:")
    
    if st.button("💡 Získať odporúčanie"):
        if user_problem:
            with st.spinner("Hľadám najlepšie riešenie pre teba..."):
                try:
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name)
                    
                    advice_prompt = f"Si Aura, expert na ochranu spotrebiteľa. Navrhni najlepší právny a praktický postup pre túto situáciu: {user_problem}. Odpovedaj v bodoch v slovenčine."
                    
                    response = model.generate_content(advice_prompt)
                    
                    st.markdown("---")
                    st.subheader("💡 Odporúčanie Aury")
                    st.markdown(response.text)
                    
                    # Uloženie do histórie
                    st.session_state['history'].append(f"Otázka: {user_problem[:30]}...")
                except Exception as e:
                    st.error(f"Chyba: {e}")
        else:
            st.warning("Prosím, napíš najprv svoj problém.")