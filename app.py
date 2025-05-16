import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extraction d'identités depuis texte web", layout="wide")
st.title("🔍 Extraction d'identités depuis du texte web")
st.markdown("""
Collez ici le contenu d'une page web (copié avec Ctrl+A, Ctrl+C).  
Choisissez le mode d'extraction pour générer un fichier Excel structuré.
""")

# --- Liste noire de mots qui ne sont pas des noms de personnes
blacklist = {
    "court", "trials", "decisions", "public", "republic", "help", "history", "supreme",
    "administrative", "organization", "jurisdiction", "list", "contact", "sitemap"
}

# --- Mode 1 : Extraction "Flag of ..." (ambassades)
def extract_from_embassy_format(text):
    results = []
    text = re.sub(r'\s+', ' ', text)
    pattern = re.compile(
        r'Flag of ([A-Za-z ]+?)\s+((?:Dr\.|Mr\.|Mrs\.|Ms\.)?\s*[A-Z][a-z\'\-]+(?:\s[A-Z][a-z\'\-]+)*)\s*-\s*([A-Za-z \'\-]+?)\s+(Embassy|Consulate|Permanent Mission)[^F]*',
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

# --- Mode 2 : Extraction intelligente ligne par ligne avec filtre
def extract_flexible_names(text):
    results = []
    seen = set()
    lines = text.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Ne garder que les lignes avec deux mots, chacun commençant par une majuscule
        match = re.match(r'^([A-ZÉÈËÊÀÂÎÏÇ][a-zéèëêàâîïç\'\\-]+)\\s+([A-ZÉÈËÊÀÂÎÏÇ][a-zéèëêàâîïç\'\\-]+)$', line)
        if match:
            prenom, nom = match.groups()
            if prenom.lower() in blacklist or nom.lower() in blacklist:
                continue

            identity = f\"{prenom} {nom}\"
            if identity.lower() in seen:
                continue
            seen.add(identity.lower())

            # Vérifie les lignes suivantes pour fonction et date de naissance
            fonction = \"\"
            date_naissance = \"\"
            for j in range(1, 3):
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    if re.search(r'(anëtar|kryetar|membre|président|présidente|member|judge|conseiller)', next_line, re.IGNORECASE):
                        fonction = next_line
                    if re.search(r'\\b(né[e]? le|born on|\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})\\b', next_line, re.IGNORECASE):
                        date_naissance = next_line

            results.append({
                \"identité\": identity,
                \"nom\": nom.upper(),
                \"prénom\": prenom.lower(),
                \"fonction\": fonction,
                \"pays\": \"\",
                \"date de naissance\": date_naissance
            })

    return pd.DataFrame(results)

# --- Interface utilisateur
text_input = st.text_area(\"Collez ici le contenu de la page web :\", height=300)
mode = st.radio(\"Choisissez le mode d'extraction :\", [
    \"Ambassades (Flag of…)\",
    \"Liste de noms intelligents (format libre)\"
])

if st.button(\"🔍 Extraire et générer le fichier Excel\") and text_input:
    if mode == \"Ambassades (Flag of…)\":
        df = extract_from_embassy_format(text_input)
    else:
        df = extract_flexible_names(text_input)

    if df.empty:
        st.warning(\"Aucune identité détectée. Veuillez vérifier le format du texte collé.\")
    else:
        st.success(f\"{len(df)} identité(s) extraites.\")
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button(
            label=\"📥 Télécharger le fichier Excel\",
            data=buffer,
            file_name=\"identites_extraites.xlsx\",
            mime=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\"
        )
