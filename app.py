import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GMAO Stock - Campus EMI", layout="wide")

# --- INITIALISATION DE LA BASE DE DONNÉES (Simulation) ---
if 'stock_df' not in st.session_state:
    data = {
        'ID_QR': ['PMP-01', 'ANO-02', 'GLY-03', 'SEL-04', 'SND-05'],
        'Designation': ['Circulateur Solaire Wilo', 'Anode Magnésium', 'Bidon Glycol 20L', 'Sel Adoucisseur (25kg)', 'Sonde PT1000'],
        'Quantite': [2, 10, 5, 20, 8],
        'Prix_Unitaire_DH': [1500, 350, 800, 95, 120]
    }
    st.session_state.stock_df = pd.DataFrame(data)

# --- FONCTION : GÉNÉRER LE PDF DE FACTURATION ---
def generate_pdf(id_trans, fournisseur, items_list, total_general):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "BON DE RÉCEPTION / FACTURATION STOCK", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Référence : {id_trans} | Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(100, 10, f"Organisme : Campus Universitaire / EMI", ln=True)
    pdf.cell(100, 10, f"Fournisseur : {fournisseur}", ln=True)
    pdf.ln(10)

    # Tableau
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(80, 10, "Désignation", border=1, fill=True)
    pdf.cell(30, 10, "Qté", border=1, fill=True)
    pdf.cell(40, 10, "Prix Unitaire", border=1, fill=True)
    pdf.cell(40, 10, "Total (DH)", border=1, fill=True)
    pdf.ln()

    pdf.set_font("Arial", size=11)
    for item in items_list:
        pdf.cell(80, 10, item['nom'], border=1)
        pdf.cell(30, 10, str(item['qte']), border=1)
        pdf.cell(40, 10, str(item['prix']), border=1)
        pdf.cell(40, 10, str(item['total']), border=1)
        pdf.ln()

    # Total
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 10, "TOTAL GÉNÉRAL : ", align='R')
    pdf.cell(40, 10, f"{total_general} DH", border=1, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE STREAMLIT ---
st.title("🛠️ Gestion de Stock & Maintenance - Campus EMI")
st.sidebar.header("Navigation")
menu = st.sidebar.radio("Choisir une action", ["📦 État du Stock", "📤 Sortie de Pièce (Scan)", "📥 Entrée & Facturation"])

# --- ONGLET 1 : ÉTAT DU STOCK ---
if menu == "📦 État du Stock":
    st.subheader("Inventaire des pièces de rechange")
    st.table(st.session_state.stock_df)

# --- ONGLET 2 : SORTIE DE PIÈCE (SCAN) ---
elif menu == "📤 Sortie de Pièce (Scan)":
    st.subheader("Sortie de matériel par Scan QR")
    
    # Simulation du Scan
    img_file = st.camera_input("Scanner le QR Code sur la pièce")
    
    id_scan = st.text_input("Ou saisir l'ID manuellement (ex: PMP-01)")
    qte_sortie = st.number_input("Quantité à retirer", min_value=1, value=1)
    user_name = st.text_input("Nom du technicien")

    if st.button("Valider la Sortie"):
        if id_scan in st.session_state.stock_df['ID_QR'].values:
            idx = st.session_state.stock_df[st.session_state.stock_df['ID_QR'] == id_scan].index[0]
            if st.session_state.stock_df.at[idx, 'Quantite'] >= qte_sortie:
                st.session_state.stock_df.at[idx, 'Quantite'] -= qte_sortie
                st.success(f"Sortie validée : {qte_sortie} unité(s) de {id_scan} retirée(s) par {user_name}.")
            else:
                st.error("Erreur : Stock insuffisant !")
        else:
            st.warning("Pièce non trouvée dans la base de données.")

# --- ONGLET 3 : ENTRÉE & FACTURATION ---
elif menu == "📥 Entrée & Facturation":
    st.subheader("Réception de commande & Génération de facture")
    
    with st.form("form_entree"):
        fournisseur = st.text_input("Nom du Fournisseur")
        id_piece = st.selectbox("Sélectionner la pièce reçue", st.session_state.stock_df['ID_QR'])
        qte_entree = st.number_input("Quantité reçue", min_value=1, value=1)
        valider = st.form_submit_button("Enregistrer l'Entrée & Préparer Facture")

    if valider:
        # Mise à jour stock
        idx = st.session_state.stock_df[st.session_state.stock_df['ID_QR'] == id_piece].index[0]
        st.session_state.stock_df.at[idx, 'Quantite'] += qte_entree
        nom_p = st.session_state.stock_df.at[idx, 'Designation']
        prix_p = st.session_state.stock_df.at[idx, 'Prix_Unitaire_DH']
        
        # Préparation données PDF
        items_pdf = [{'nom': nom_p, 'qte': qte_entree, 'prix': prix_p, 'total': qte_entree * prix_p}]
        total_p = qte_entree * prix_p
        
        st.success(f"Stock mis à jour. Facture prête pour : {nom_p}")
        
        # Génération du bouton de téléchargement PDF
        pdf_bytes = generate_pdf(f"FAC-{datetime.now().strftime('%H%M%S')}", fournisseur, items_pdf, total_p)
        st.download_button(
            label="📄 Télécharger la Feuille de Facturation (PDF)",
            data=pdf_bytes,
            file_name=f"facture_{id_piece}.pdf",
            mime="application/pdf"
        )

# --- PIED DE PAGE ---
st.sidebar.markdown("---")
st.sidebar.info("Projet PFE - EMI Génie Mécanique\nOptimisation Énergétique & Maintenance 4.0")
