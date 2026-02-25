import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="GMAO Stock - Campus EMI", layout="wide")

# --- INITIALISATION DES BASES DE DONNÉES ---
if 'stock_df' not in st.session_state:
    st.session_state.stock_df = pd.DataFrame({
        'ID_QR': ['PMP-01', 'ANO-02', 'GLY-03', 'SEL-04', 'SND-05'],
        'Designation': ['Circulateur Solaire Wilo', 'Anode Magnésium', 'Bidon Glycol 20L', 'Sel Adoucisseur (25kg)', 'Sonde PT1000'],
        'Quantite': [2, 10, 5, 20, 8],
        'Prix_Unitaire_DH': [1500, 350, 800, 95, 120]
    })

if 'historique_sorties' not in st.session_state:
    # On crée un historique vide avec les colonnes nécessaires
    st.session_state.historique_sorties = pd.DataFrame(columns=['Date', 'ID_QR', 'Designation', 'Quantite', 'Technicien'])

# --- FONCTION : CONVERSION EXCEL ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sorties_Hebdo')
    return output.getvalue()

# --- INTERFACE ---
st.title("🛠️ Gestion de Stock & Maintenance - Campus EMI")
menu = st.sidebar.radio("Navigation", ["📦 État du Stock", "📤 Sortie de Pièce (Scan)", "📥 Entrée & Facturation", "📋 Historique Hebdo"])

# --- ONGLET : SORTIE DE PIÈCE (Modifié pour enregistrer l'historique) ---
if menu == "📤 Sortie de Pièce (Scan)":
    st.subheader("Sortie de matériel")
    id_scan = st.text_input("Scanner ou saisir l'ID QR")
    qte_sortie = st.number_input("Quantité", min_value=1, value=1)
    user_name = st.text_input("Nom du technicien")

    if st.button("Valider la Sortie"):
        if id_scan in st.session_state.stock_df['ID_QR'].values:
            idx = st.session_state.stock_df[st.session_state.stock_df['ID_QR'] == id_scan].index[0]
            if st.session_state.stock_df.at[idx, 'Quantite'] >= qte_sortie:
                # 1. Mise à jour du stock
                st.session_state.stock_df.at[idx, 'Quantite'] -= qte_sortie
                
                # 2. Enregistrement dans l'historique
                nouvelle_ligne = {
                    'Date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'ID_QR': id_scan,
                    'Designation': st.session_state.stock_df.at[idx, 'Designation'],
                    'Quantite': qte_sortie,
                    'Technicien': user_name
                }
                st.session_state.historique_sorties = pd.concat([st.session_state.historique_sorties, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
                
                st.success("Sortie enregistrée et ajoutée à l'historique.")
            else:
                st.error("Stock insuffisant !")

# --- NOUVEL ONGLET : HISTORIQUE HEBDO & EXCEL ---
elif menu == "📋 Historique Hebdo":
    st.subheader("Pièces sorties pendant la semaine")
    
    if st.session_state.historique_sorties.empty:
        st.info("Aucune sortie enregistrée pour le moment.")
    else:
        # Filtrage : On ne garde que les sorties des 7 derniers jours
        st.session_state.historique_sorties['Date_dt'] = pd.to_datetime(st.session_state.historique_sorties['Date'])
        il_y_a_une_semaine = datetime.now() - timedelta(days=7)
        df_hebdo = st.session_state.historique_sorties[st.session_state.historique_sorties['Date_dt'] > il_y_a_une_semaine]

        # Affichage du tableau (sans la colonne technique de date)
        st.dataframe(df_hebdo.drop(columns=['Date_dt']))

        # Bouton Téléchargement EXCEL
        excel_data = to_excel(df_hebdo.drop(columns=['Date_dt']))
        st.download_button(
            label="📊 Exporter l'historique vers Excel",
            data=excel_data,
            file_name=f"rapport_sorties_hebdo_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# (Les autres onglets restent identiques...)
