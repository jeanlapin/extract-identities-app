import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extraction d'identités depuis texte web", layout="wide")
st.title("🔍 Extraction d'identités depuis du texte web")
st.markdown("""
Collez ici le contenu d'une page web (copié avec Ctrl+A, Ctrl+C) pour extraire une liste de personnes.
Le fichier Excel généré sera téléchargeable directement ci-dessous.
""")

# Fonction d'extraction des identités à partir du texte brut
def extract_identities(text):
    # Nettoyage
    lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
    results = []

    # Exemple d'extraction simplifiée (à adapter selon le format exact de ton texte)
    for i, line in enumerate(lines):
        if re.search(r'[A-Z]{2,}\s+[A-Z]{2,}', line):  # détecte les noms en majuscules
            nom_prenom = line.strip()
            nom = re.findall(r'([A-Z]{2,})', nom_prenom)[0]
            prenom = re.findall(r'([A-Z]{2,})', nom_prenom)[1] if len(re.findall(r'([A-Z]{2,})', nom_prenom)) > 1 else ""
            full_name = f"{prenom.capitalize()} {nom.capitalize()}" if prenom else nom.capitalize()

            fonction, pays, dob = "", "", ""

            # On regarde les lignes suivantes pour chercher les autres infos
            for j in range(1, 5):
                if i + j < len(lines):
                    candidate = lines[i + j].strip()
                    if re.search(r'\b(n\u00e9 le|date de naissance|DOB|\d{2}/\d{2}/\d{4})', candidate, re.IGNORECASE):
                        dob = candidate
                    elif re.search(r'\bFrance|Belgique|Canada|Suisse|Allemagne|Espagne|Italie|\bUSA|\bUK\b', candidate, re.IGNORECASE):
                        pays = candidate
                    elif len(candidate.split()) <= 8:
                        fonction = candidate

            results.append({
                "identité": full_name,
                "nom": nom.upper(),
                "prénom": prenom.lower(),
                "fonction": fonction,
                "pays": pays,
                "date de naissance": dob
            })

    return pd.DataFrame(results)

# Interface utilisateur
text_input = st.text_area("Collez ici le contenu de la page web :", height=300)

if st.button("🔍 Extraire et générer le fichier Excel") and text_input:
    df = extract_identities(text_input)

    if df.empty:
        st.warning("Aucune identité détectée. Veuillez vérifier le format du texte.")
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
