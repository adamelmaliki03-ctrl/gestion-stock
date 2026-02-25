import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import io
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="GMAO Stock - Campus EMI", layout="wide")

EXCEL_PATH = "stock_campus_emi.xlsx"  # Chemin vers votre fichier Excel

# ─────────────────────────────────────────────
# FONCTIONS EXCEL (lecture / écriture)
# ─────────────────────────────────────────────

def load_stock_from_excel():
    """Charge la feuille Stock depuis le fichier Excel."""
    df = pd.read_excel(EXCEL_PATH, sheet_name="Stock", engine="openpyxl")
    # On ignore la ligne TOTAL si elle existe
    df = df[df["ID_QR"].notna() & (df["ID_QR"] != "TOTAL")]
    return df[["ID_QR", "Designation", "Quantite", "Prix_Unitaire_DH", "Seuil_Alerte"]].copy()


def save_stock_to_excel(df: pd.DataFrame):
    """Réécrit les données de stock dans la feuille Stock (conserve le formatage de l'en-tête)."""
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Stock"]

    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    alt_fill = PatternFill("solid", start_color="EAF0FB")

    # Efface les données (ligne 2 jusqu'à la fin) sans toucher l'en-tête
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.value = None

    # Réécrit les lignes
    for r_idx, row in enumerate(df.itertuples(index=False), start=2):
        values = [row.ID_QR, row.Designation, row.Quantite, row.Prix_Unitaire_DH,
                  f"=C{r_idx}*D{r_idx}", row.Seuil_Alerte]
        for c_idx, val in enumerate(values, 1):
            cell = ws.cell(r_idx, c_idx, val)
            cell.border = border
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="center" if c_idx != 2 else "left")
            if r_idx % 2 == 0:
                cell.fill = alt_fill

    # Ligne TOTAL
    total_row = len(df) + 2
    ws.cell(total_row, 1, "TOTAL").font = Font(bold=True, name="Arial")
    ws.cell(total_row, 1).border = border
    total_cell = ws.cell(total_row, 5, f"=SUM(E2:E{total_row-1})")
    total_cell.font = Font(bold=True, name="Arial", color="2E4057")
    total_cell.border = border
    total_cell.alignment = Alignment(horizontal="center")
    for c in [2, 3, 4, 6]:
        ws.cell(total_row, c).border = border

    wb.save(EXCEL_PATH)


def append_sortie_to_excel(date_str, id_qr, designation, qte, technicien):
    """Ajoute une ligne dans la feuille Historique_Sorties."""
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Historique_Sorties"]
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    next_row = ws.max_row + 1
    values = [date_str, id_qr, designation, qte, technicien]
    for c_idx, val in enumerate(values, 1):
        cell = ws.cell(next_row, c_idx, val)
        cell.border = border
        cell.font = Font(name="Arial", size=10)
        if next_row % 2 == 0:
            cell.fill = PatternFill("solid", start_color="EAF0FB")
    wb.save(EXCEL_PATH)


def load_historique_from_excel():
    """Charge la feuille Historique_Sorties."""
    df = pd.read_excel(EXCEL_PATH, sheet_name="Historique_Sorties", engine="openpyxl")
    return df


# ─────────────────────────────────────────────
# INITIALISATION SESSION STATE
# ─────────────────────────────────────────────

def init_state():
    if "stock_df" not in st.session_state:
        if os.path.exists(EXCEL_PATH):
            st.session_state.stock_df = load_stock_from_excel()
        else:
            st.error(f"Fichier Excel introuvable : {EXCEL_PATH}")
            st.stop()

init_state()


# ─────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────

def to_excel_download(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Historique")
    return output.getvalue()


def generate_pdf(id_trans, fournisseur, items_list, total_general) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "BON DE RÉCEPTION / FACTURATION STOCK", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Référence : {id_trans} | Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(100, 10, "Organisme : Campus Universitaire / EMI", ln=True)
    pdf.cell(100, 10, f"Fournisseur : {fournisseur}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", "B", 11)
    for col, w in zip(["Désignation", "Qté", "Prix Unitaire", "Total (DH)"], [80, 30, 40, 40]):
        pdf.cell(w, 10, col, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Arial", size=11)
    for item in items_list:
        pdf.cell(80, 10, item["nom"], border=1)
        pdf.cell(30, 10, str(item["qte"]), border=1)
        pdf.cell(40, 10, str(item["prix"]), border=1)
        pdf.cell(40, 10, str(item["total"]), border=1)
        pdf.ln()
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 10, "TOTAL GÉNÉRAL : ", align="R")
    pdf.cell(40, 10, f"{total_general} DH", border=1, align="C")
    return pdf.output(dest="S").encode("latin-1")


# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

st.title("🛠️ Gestion de Stock & Maintenance - Campus EMI")
st.sidebar.header("Navigation")
menu = st.sidebar.radio(
    "Choisir une action",
    ["📦 État du Stock", "📤 Sortie de Pièce (Scan)", "📥 Entrée & Facturation", "📋 Historique Hebdo"]
)

# ── Bouton de rechargement depuis Excel ──
if st.sidebar.button("🔄 Recharger depuis Excel"):
    st.session_state.stock_df = load_stock_from_excel()
    st.sidebar.success("Stock rechargé !")

st.sidebar.markdown("---")
st.sidebar.info("Projet PFE - EMI Génie Mécanique\nOptimisation Énergétique & Maintenance 4.0")


# ─────────────────────────────────────────────
# ONGLET 1 : ÉTAT DU STOCK
# ─────────────────────────────────────────────
if menu == "📦 État du Stock":
    st.subheader("Inventaire des pièces de rechange")

    col1, col2 = st.columns([3, 1])

    with col1:
        df_display = st.session_state.stock_df.copy()
        df_display["Valeur_Totale_DH"] = df_display["Quantite"] * df_display["Prix_Unitaire_DH"]

        # Mise en évidence des stocks bas
        def highlight_low(row):
            seuil = row.get("Seuil_Alerte", 0) or 0
            color = "background-color: #FFD6D6" if row["Quantite"] <= seuil else ""
            return [color] * len(row)

        st.dataframe(df_display.style.apply(highlight_low, axis=1), use_container_width=True)
        st.caption("🔴 Fond rouge = quantité ≤ seuil d'alerte")

    with col2:
        st.metric("Nb références", len(df_display))
        total_val = int((df_display["Quantite"] * df_display["Prix_Unitaire_DH"]).sum())
        st.metric("Valeur totale stock", f"{total_val:,} DH")

    st.divider()
    # Téléchargement du fichier Excel complet
    with open(EXCEL_PATH, "rb") as f:
        st.download_button(
            label="📥 Télécharger le fichier Excel complet",
            data=f.read(),
            file_name="stock_campus_emi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ─────────────────────────────────────────────
# ONGLET 2 : SORTIE DE PIÈCE
# ─────────────────────────────────────────────
elif menu == "📤 Sortie de Pièce (Scan)":
    st.subheader("Sortie de matériel par Scan QR")

    st.camera_input("Scanner le QR Code sur la pièce")
    id_scan   = st.text_input("Ou saisir l'ID manuellement (ex: PMP-01)")
    qte_sortie = st.number_input("Quantité à retirer", min_value=1, value=1)
    user_name  = st.text_input("Nom du technicien")

    if st.button("Valider la Sortie"):
        df = st.session_state.stock_df
        if id_scan in df["ID_QR"].values:
            idx = df[df["ID_QR"] == id_scan].index[0]
            if df.at[idx, "Quantite"] >= qte_sortie:
                # Mise à jour mémoire
                st.session_state.stock_df.at[idx, "Quantite"] -= qte_sortie
                designation = df.at[idx, "Designation"]

                # ✅ Sauvegarde dans Excel
                save_stock_to_excel(st.session_state.stock_df)
                append_sortie_to_excel(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    id_scan, designation, qte_sortie, user_name
                )

                st.success(f"✅ Sortie validée : {qte_sortie} × {id_scan} retiré(s) par {user_name}. Excel mis à jour.")
            else:
                st.error("❌ Stock insuffisant !")
        else:
            st.warning("⚠️ Pièce non trouvée dans la base de données.")


# ─────────────────────────────────────────────
# ONGLET 3 : ENTRÉE & FACTURATION
# ─────────────────────────────────────────────
elif menu == "📥 Entrée & Facturation":
    st.subheader("Réception de commande & Génération de facture")

    with st.form("form_entree"):
        fournisseur = st.text_input("Nom du Fournisseur")
        id_piece    = st.selectbox("Sélectionner la pièce reçue", st.session_state.stock_df["ID_QR"])
        qte_entree  = st.number_input("Quantité reçue", min_value=1, value=1)
        valider     = st.form_submit_button("Enregistrer l'Entrée & Préparer Facture")

    if valider:
        df  = st.session_state.stock_df
        idx = df[df["ID_QR"] == id_piece].index[0]
        st.session_state.stock_df.at[idx, "Quantite"] += qte_entree
        nom_p  = df.at[idx, "Designation"]
        prix_p = df.at[idx, "Prix_Unitaire_DH"]

        # ✅ Sauvegarde dans Excel
        save_stock_to_excel(st.session_state.stock_df)

        st.success(f"✅ Stock mis à jour pour {nom_p}. Excel sauvegardé.")

        items_pdf = [{"nom": nom_p, "qte": qte_entree, "prix": prix_p, "total": qte_entree * prix_p}]
        pdf_bytes = generate_pdf(f"FAC-{datetime.now().strftime('%H%M%S')}", fournisseur, items_pdf, qte_entree * prix_p)

        st.download_button(
            label="📄 Télécharger la Feuille de Facturation (PDF)",
            data=pdf_bytes,
            file_name=f"facture_{id_piece}.pdf",
            mime="application/pdf"
        )


# ─────────────────────────────────────────────
# ONGLET 4 : HISTORIQUE HEBDO
# ─────────────────────────────────────────────
elif menu == "📋 Historique Hebdo":
    st.subheader("Pièces sorties pendant la semaine")

    df_hist = load_historique_from_excel()

    if df_hist.empty or df_hist.dropna(how="all").empty:
        st.info("Aucune sortie enregistrée pour le moment.")
    else:
        df_hist["Date_dt"] = pd.to_datetime(df_hist["Date"], errors="coerce")
        il_y_a_une_semaine = datetime.now() - timedelta(days=7)
        df_hebdo = df_hist[df_hist["Date_dt"] > il_y_a_une_semaine].drop(columns=["Date_dt"])

        if df_hebdo.empty:
            st.info("Aucune sortie cette semaine.")
        else:
            st.dataframe(df_hebdo, use_container_width=True)
            st.metric("Total sorties cette semaine", len(df_hebdo))

            excel_data = to_excel_download(df_hebdo)
            st.download_button(
                label="📊 Exporter l'historique vers Excel",
                data=excel_data,
                file_name=f"rapport_sorties_hebdo_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
