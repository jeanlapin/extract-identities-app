import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extraction d'identités", layout="wide")
st.title("🔍 Extraction d'identités depuis du texte web")
st.markdown("Collez ici un texte copié depuis une page web. Utilisez l’un des boutons selon le format du texte.")

# Blacklist indicative
BLACKLIST = {
    "INCOMING", "CASES", "SEARCH", "DECISIONS", "PUBLIC", "NEWS", "CONTACTS", "COURT", "LIST",
    "TRIALS", "RELATIONS", "KED", "JUDIX", "MEMBERS", "SUPREME", "ORGANIZATION", "HISTORY",
    "REQUEST", "JURISDICTION", "HELP", "TERMS", "USE", "SITEMAP", "CONTACT", "NAVIGATED", "TO", "OF", "THE"
}

# --- Format Ambassades
def extract_from_embassy_format(text):
    results = []
    text = re.sub(r'\s+', ' ', text)
    pattern = re.compile(
        r'Flag of ([A-Za-z ]+?)\s+((?:Dr\.|Mr\.|Mrs\.|Ms\.)?\s*[A-Z][a-z\'\-]+(?:\s[A-Z][a-z\'\-]+)*)\s*-\s*([A-Za-z \-\']+?)\s+(Embassy|Consulate|Permanent Mission)[^F]*',
        re.IGNORECASE
    )
    matches = pattern.findall(text)
    for match in matches:
        country, full_name, function, _ = map(str.strip, match)
        full_name_clean = re.sub(r'^(Dr\.|Mr\.|Mrs\.|Ms\.)\s+', '', full_name)
        name_parts = full_name_clean.split()
        prenom = name_parts[0].lower() if name_parts else ""
        nom = name_parts[-1].upper() if len(name_parts) > 1 else ""
        results.append({
            "identité": full_name_clean,
            "nom": nom,
            "prénom": prenom,
            "fonction": function,
            "pays": country,
            "date de naissance": ""
        })
    return pd.DataFrame(results)

# --- Nettoyage brut pour GPT
def clean_text_for_gpt(text):
    lines = text.splitlines()
    cleaned_blocks = []
    buffer = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if all(word.istitle() or word.isupper() for word in line.split()):
            if any(word.upper() in BLACKLIST for word in line.split()):
                continue
            buffer.append(line)
            continue
        if re.search(r'(anëtar|kryetar|président|judge|member|chargé|ambassador|consul|membre)', line, re.IGNORECASE) or \
           re.search(r'\b(né[e]? le|born on|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', line, re.IGNORECASE):
            buffer.append(line)
            continue
        if buffer:
            cleaned_blocks.append("\n".join(buffer))
            buffer = []
    if buffer:
        cleaned_blocks.append("\n".join(buffer))
    return "\n\n".join(cleaned_blocks)

# --- Interface utilisateur
text_input = st.text_area("Collez ici le contenu brut :", height=300)

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Format Ambassades") and text_input:
        df = extract_from_embassy_format(text_input)
        if df.empty:
            st.warning("Aucune identité détectée.")
        else:
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("📥 Télécharger (ambassades)", buffer, "ambassades.xlsx")

with col2:
    if st.button("🧹 Nettoyer pour GPT") and text_input:
        cleaned = clean_text_for_gpt(text_input)
        st.text_area("Texte nettoyé prêt pour GPT :", value=cleaned, height=300)
        txt_bytes = BytesIO(cleaned.encode("utf-8"))
        st.download_button("📄 Télécharger texte pour GPT", txt_bytes, "texte_pour_gpt.txt", mime="text/plain")
