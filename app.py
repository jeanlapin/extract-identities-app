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

def extract_identities(text):
    # Découpe en blocs à partir de chaque occurrence de "Flag of"
    blocks = re.split(r"(?=Flag of )", text)
    results = []

    for block in blocks:
        match = re.match(
            r"Flag of ([A-Za-z\\s]+)\\s+((Dr\\.|Mr\\.|Mrs\\.|Ms\\.|Miss)?\\s*[A-Z][a-z\\'\\-\\.]+(?:\\s[A-Z][a-z\\'\\-\\.]+)*)\\s+-\\s+([A-Za-z\\s\\'\\-]+)",
            block.strip()
        )

        if match:
            country = match.group(1).strip()
            fullname = match.group(2).strip()
            fonction = match.group(4).strip()

            # Nettoyage nom/prénom
            fullname_clean = re.sub(r'^(Dr\\.|Mr\\.|Mrs\\.|Ms\\.|Miss)\\s+', '', fullname)
            parts = fullname_clean.strip().split()
            prenom = parts[0] if parts else ""
            nom = parts[-1] if len(parts) > 1 else ""

            results.append({
                "identité": fullname_clean,
                "nom": nom.upper(),
                "prénom": prenom.lower(),
                "fonction": fonction,
                "pays": country,
                "date de naissance": ""
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
