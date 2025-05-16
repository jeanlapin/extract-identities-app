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

# Fonction d'extraction mise à jour
def extract_identities(text):
    lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
    results = []

    for i in range(len(lines)):
        line = lines[i]

        if line.startswith("Flag of"):
            try:
                # Extraction des éléments principaux
                match = re.match(r"Flag of ([A-Za-z\s]+) ([A-Z]?[a-z\'\-\.]+(?:\s[A-Z]?[a-z\'\-\.]+)*)\s+([A-Z\-\'\s]+)\s+-\s+(.+)", line)
                if match:
                    country = match.group(1).strip()
                    firstnames = match.group(2).strip()
                    lastname = match.group(3).strip()
                    function = match.group(4).strip()

                    full_name = f"{firstnames} {lastname}".strip()

                    # Ligne suivante : poste (ambassade ou consulat)
                    institution = lines[i + 1] if i + 1 < len(lines) else ""

                    results.append({
                        "identité": full_name,
                        "nom": lastname.upper(),
                        "prénom": firstnames.lower(),
                        "fonction": function,
                        "pays": country,
                        "date de naissance": ""
                    })
            except Exception as e:
                continue

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
