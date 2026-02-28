# Aura — Local PDF/Image Analyzer with Generative AI

Lokálna aplikácia (Streamlit) na analýzu PDF a obrázkov s fallbackom na textový model.

## Zhrnutie
- Extrakcia textu z PDF pomocou `PyPDF2`.
- OCR z obrázkov cez `pytesseract` + systémový Tesseract.
- Preferencia lokálne extrahovaného textu a `models/text-bison-001` na šetrenie kvót.

## Rýchly štart
1. Vytvorte a aktivujte virtuálne prostredie (Windows PowerShell):
```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2. Skontrolujte, že `tesseract` je v PATH (alebo nastavte priamo `pytesseract.pytesseract.tesseract_cmd`).
3. Spustite aplikáciu:
```powershell
python -m streamlit run aura_web.py --server.port 8501
```

## Bezpečnosť a dobré praktiky
- Nikdy nezahadzujte API kľúče do repozitára: použite `.env` a pridajte ho do `.gitignore`.
- Pre pohodlné pushovanie na GitHub používajte `gh auth login` alebo `git credential manager`.

## Licencia
- (Pridajte vašu licenciu sem, napr. MIT)

## Kontakt
- maty558 (GitHub)
