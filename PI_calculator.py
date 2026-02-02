import streamlit as st
import numpy as np

st.title("🧮 Analizzatore Fisiologico: PI & Mader Optimizer")

# --- INPUT VOLUME ---
st.sidebar.header("Parametri di Carico")
total_vol = st.sidebar.number_input("Volume Totale Settimanale (min)", min_value=0, value=300)

# --- INPUT ZONE (Slider interconnessi) ---
st.sidebar.header("Training Intensity Distribution (%)")
z1_pct = st.sidebar.slider("Zona 1 (Aerobico Basso)", 0, 100, 80)
# Calcolo residuo per assicurare sum=100
remaining = 100 - z1_pct
z2_pct = st.sidebar.slider("Zona 2 (Soglia/VLaMax)", 0, remaining, min(remaining, 10))
z3_pct = 100 - z1_pct - z2_pct
st.sidebar.text(f"Zona 3 (Alta Intensità): {z3_pct}%")

# --- LOGICA MATEMATICA (Treff et al. 2019) ---
z1, z2, z3 = z1_pct/100, z2_pct/100, z3_pct/100

if z2 > 0:
    # Formula standard [cite: 540]
    pi = np.log10((z1 / z2) * z3 * 100)
else:
    # Correzione per Zone 2 = 0 
    pi = np.log10((z1 / 0.01) * z3 - 0.01 * 100) if z3 > 0 else 0

# --- OUTPUT ---
col1, col2, col3 = st.columns(3)
col1.metric("Polarization Index (PI)", f"{pi:.2f} a.U.")
col2.metric("Stato TID", "POLARIZZATO" if pi > 2.0 else "PIRAMIDALE")
col3.metric("Volume Z1", f"{int(total_vol * z1)} min")

# --- ANALISI FISIOLOGICA (Mader & Studio Periodizzazione) ---
st.subheader("Analisi Termodinamica del Sistema")

if pi > 2.0:
    st.success("🎯 **Assetto Polarizzato**: Ottimale per l'incremento della cilindrata ($VO_2max$) e il recupero del sistema nervoso[cite: 528, 556].")
else:
    st.info("📉 **Assetto Piramidale/Soglia**: Ideale per la soppressione del $VLaMax$ e l'efficienza nella Mezza Maratona[cite: 521, 570].")

# Tabella riassuntiva dei flussi
data = {
    "Zona": ["Z1 (Bassa)", "Z2 (Soglia)", "Z3 (Alta)"],
    "Minuti": [total_vol*z1, total_vol*z2, total_vol*z3],
    "Effetto Mader": ["Recupero/Capillarizzazione", "Soppressione VLaMax", "Stimolo VO2max"]
}
st.table(data)

st.caption("Riferimenti scientifici: Treff et al. (2019) [PI Formula], Casado et al. (2022) [TID Analysis].")
