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

# 🔧 Nouvelle fonction robuste
def extract_identities(text):
    results = []

    # Nettoyer le texte collé : tout ramener sur une seule ligne
    text = re.sub(r'\s+', ' ', text)

    # Expression régulière très tolérante pour extraire :
    # pays, nom complet (avec titre éventuel), fonction, et ligne suivante (ambassade)
    pattern = re.compile(
        r'Flag of ([A-Za-z ]+?)\s+((?:Dr\.|Mr\.|Mrs\.|Ms\.)?\s*[A-Z][a-z\']+(?:\s[A-Z][a-z\'\-]+)*)\s*-\s*([A-Za-z \'\-]+?)\s+(Embassy|Consulate|Permanent Mission)[^F]*',
        re.IGNORECASE
    )

    matches = pattern.findall(text)

    for match in matches:
        country = match[0].strip()
        full_name = match[1].strip()
        function = match[2].strip()
        institution_type = match[3].strip()

        # Nettoyage du nom / prénom
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

# Interface utilisateur
text_input = st.text_area("Collez ici le contenu de la page web :", height=300)

if st.button("🔍 Extraire et générer le fichier Excel") and text_input:
    df = extract_identities(text_input)

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
