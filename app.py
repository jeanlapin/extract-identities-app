import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extraction d'identités depuis texte web", layout="wide")
st.title("🔍 Extraction d'identités depuis du texte web")
st.markdown("""
Collez ici le contenu d'une page web (copié avec Ctrl+A, Ctrl+C).
Choisissez le mode d'extraction ci-dessous pour générer un fichier Excel structuré.
""")

# Mode 1 : Ambassade

def extract_from_embassy_format(text):
    results = []
    text = re.sub(r'\s+', ' ', text)
    pattern = re.compile(
        r'Flag of ([A-Za-z ]+?)\s+((?:Dr\.|Mr\.|Mrs\.|Ms\.)?\s*[A-Z][a-z\']+(?:\s[A-Z][a-z\'\-]+)*)\s*-\s*([A-Za-z \-\']+?)\s+(Embassy|Consulate|Permanent Mission)[^F]*',
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

# Mode 2 : Majuscules

def extract_from_uppercase_names(text):
    lines = re.findall(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})+\b', text)
    seen = set()
    results = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            parts = line.strip().split()
            prenom = parts[0].lower() if parts else ""
            nom = parts[-1].upper() if len(parts) > 1 else ""
            results.append({
                "identité": line.title(),
                "nom": nom,
                "prénom": prenom,
                "fonction": "",
                "pays": "",
                "date de naissance": ""
            })
    return pd.DataFrame(results)

# Interface utilisateur
text_input = st.text_area("Collez ici le contenu de la page web :", height=300)
mode = st.radio("Choisissez le mode d'extraction :", ["Ambassades (Flag of…)", "Liste de noms en MAJUSCULES"])

if st.button("🔍 Extraire et générer le fichier Excel") and text_input:
    if mode == "Ambassades (Flag of…)":
        df = extract_from_embassy_format(text_input)
    else:
        df = extract_from_uppercase_names(text_input)

    if df.empty:
        st.warning("Aucune identité détectée. Veuillez vérifier le format du texte collé.")
    else:
        st.success(f"{len(df)} identité(s) extraites.")
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=buffer,
            file_name="identites_extraites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
