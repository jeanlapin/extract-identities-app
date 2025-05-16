import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extraction d'identités depuis texte web", layout="wide")
st.title("🔍 Extraction d'identités depuis du texte web")
st.markdown("""
Collez ici le contenu d'une page web (copié avec Ctrl+A, Ctrl+C).
Utilisez l'un des trois boutons selon la structure du texte.
""")

# Liste noire indicative pour extraction structurée
BLACKLIST = {
    "court", "trials", "decisions", "public", "republic", "help", "history", "supreme",
    "administrative", "organization", "jurisdiction", "list", "contact", "sitemap",
    "cases", "incoming", "news", "about", "members", "search", "home", "feedback", "privacy"
}

# --- Fonction Ambassades (inchangée)
def extract_from_embassy_format(text):
    results = []
    text = re.sub(r'\s+', ' ', text)
    pattern = re.compile(
        r'Flag of ([A-Za-z ]+?)\s+((?:Dr\.|Mr\.|Mrs\.|Ms\.)?\s*[A-Z][a-z\'\-]+(?:\s[A-Z][a-z\'\-]+)*)\s*-\s*([A-Za-z \-\']+?)\s+(Embassy|Consulate|Permanent Mission)[^F]*',
        re.IGNORECASE
    )
    matches = pattern.findall(text)
    for match in matches:
        country = match[0].strip()
        full_name = match[1].strip()
        function = match[2].strip()
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

# --- Fonction structurée classique

def extract_general_identities(text):
    results = []
    seen = set()
    lines = text.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line.split()) != 2:
            continue

        match = re.match(r'^([A-ZÉÈËÊÀÂÎÏÇ][a-zéèëêàâîïç\'-]+)\s+([A-ZÉÈËÊÀÂÎÏÇ][a-zéèëêàâîïç\'-]+)$', line)
        if match:
            prenom, nom = match.groups()
            if prenom.lower() in BLACKLIST or nom.lower() in BLACKLIST:
                continue

            full_identity = f"{prenom} {nom}"
            if full_identity.lower() in seen:
                continue
            seen.add(full_identity.lower())

            fonction = ""
            date_naissance = ""
            for j in range(1, 4):
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    if re.search(r'(président|anëtar|kryetar|conseiller|judge|membre|chargé|ambassador|consul)', next_line, re.IGNORECASE):
                        fonction = next_line
                    elif re.search(r'\b(né[e]? le|born on|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', next_line, re.IGNORECASE):
                        date_naissance = next_line

            results.append({
                "identité": full_identity,
                "nom": nom.upper(),
                "prénom": prenom.lower(),
                "fonction": fonction,
                "pays": "",
                "date de naissance": date_naissance
            })

    return pd.DataFrame(results)

# --- Nouvelle fonction : extraction large et libre

def extract_all_possible_identities(text):
    candidates = re.findall(r'\b(?:[A-ZÉÈËÊÀÂÎÏÇ][a-zéèëêàâîïç\'-]+\s+){1,3}[A-ZÉÈËÊÀÂÎÏÇ][a-zéèëêàâîïç\'-]+\b', text)
    seen = set()
    results = []
    for identity in candidates:
        clean = identity.strip()
        if clean.lower() in seen:
            continue
        seen.add(clean.lower())
        parts = clean.split()
        if len(parts) >= 2:
            prenom = parts[0].lower()
            nom = parts[-1].upper()
        else:
            prenom = ""
            nom = parts[0].upper()
        results.append({
            "identité": clean,
            "nom": nom,
            "prénom": prenom,
            "fonction": "",
            "pays": "",
            "date de naissance": ""
        })
    return pd.DataFrame(results)

# --- Interface utilisateur
text_input = st.text_area("Collez ici le contenu de la page web :", height=300)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Format Ambassades") and text_input:
        df = extract_from_embassy_format(text_input)
        if df.empty:
            st.warning("Aucune identité détectée en format ambassade.")
        else:
            st.success(f"{len(df)} identité(s) extraites.")
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="📥 Télécharger (ambassades)",
                data=buffer,
                file_name="identites_ambassades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

with col2:
    if st.button("🔍 Format structuré classique") and text_input:
        df = extract_general_identities(text_input)
        if df.empty:
            st.warning("Aucune identité détectée en format structuré.")
        else:
            st.success(f"{len(df)} identité(s) extraites.")
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="📥 Télécharger (structuré)",
                data=buffer,
                file_name="identites_structurees.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

with col3:
    if st.button("🔍 Scanner tout format") and text_input:
        df = extract_all_possible_identities(text_input)
        if df.empty:
            st.warning("Aucune identité détectée (scan libre).")
        else:
            st.success(f"{len(df)} identité(s) extraites.")
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="📥 Télécharger (scan libre)",
                data=buffer,
                file_name="identites_tous_formats.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
