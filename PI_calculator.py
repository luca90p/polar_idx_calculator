import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Performance Engineer: PI Dashboard", layout="wide")

def calculate_pi(z1, z2, z3):
    if z1 + z2 + z3 == 0: return 0.0
    f1, f2, f3 = z1/(z1+z2+z3), z2/(z1+z2+z3), z3/(z1+z2+z3)
    if f2 > 0:
        return np.log10((f1 / f2) * f3 * 100)
    else:
        return np.log10((f1 / 0.01) * f3 * 100) if f3 > 0 else 0.0

st.title("🎛️ Performance Control System: TID & Polarization")

tab1, tab2, tab3 = st.tabs([
    "1. Design delle Combinazioni", 
    "2. Tracking Real-Time", 
    "3. Planning Rimanente"
])

# --- TAB 1: DESIGN ---
with tab1:
    st.header("Sintesi delle Combinazioni Possibili")
    st.write("Dato un PI obiettivo, calcola come devono variare Z2 e Z3 in base alla Zona 1 scelta.")
    
    target_pi_t1 = st.slider("Imposta PI Desiderato (a.U.)", 0.5, 3.5, 2.0, step=0.1)
    k = (10**target_pi_t1) / 100
    
    # Generiamo un range di Z1 plausibili (70-90%)
    z1_range = np.linspace(0.70, 0.95, 26)
    results = []
    for z1 in z1_range:
        z2 = (z1 * (1 - z1)) / (k + z1)
        z3 = 1 - z1 - z2
        if z2 >= 0 and z3 >= 0:
            results.append({"Z1 %": z1*100, "Z2 %": z2*100, "Z3 %": z3*100})
    
    df_res = pd.DataFrame(results)
    st.table(df_res.style.format("{:.1f}"))
    st.line_chart(df_res.set_index("Z1 %"))

# --- TAB 2: TRACKING ---
with tab2:
    st.header("Stato del Sistema (Real-Time)")
    col1, col2, col3 = st.columns(3)
    m1 = col1.number_input("Minuti eseguiti Z1", min_value=0.0, value=120.0)
    m2 = col2.number_input("Minuti eseguiti Z2", min_value=0.0, value=20.0)
    m3 = col3.number_input("Minuti eseguiti Z3", min_value=0.0, value=15.0)
    
    current_pi = calculate_pi(m1, m2, m3)
    st.metric("PI Attuale", f"{current_pi:.2f} a.U.")
    
    total = m1 + m2 + m3
    st.progress(m1/total if total > 0 else 0)
    st.write(f"Volume Totale: {int(total)} min | TID: {m1/total*100:.1f}% / {m2/total*100:.1f}% / {m3/total*100:.1f}%")

# --- TAB 3: PLANNING ---
with tab3:
    st.header("Calcolo del Lavoro Rimanente")
    st.write("Definisci l'obiettivo finale e ottieni cosa manca per chiudere la settimana correttamente.")
    
    c1, c2 = st.columns(2)
    target_pi_t3 = c1.slider("Target PI Settimanale", 0.5, 3.5, 2.0, key="t3_pi")
    target_vol = c2.number_input("Target Volume Settimanale (min)", value=300)
    
    st.divider()
    st.write("**Dati Attuali:**")
    curr_z1 = st.number_input("Minuti già fatti Z1", value=m1, key="t3_z1")
    curr_z2 = st.number_input("Minuti già fatti Z2", value=m2, key="t3_z2")
    curr_z3 = st.number_input("Minuti già fatti Z3", value=m3, key="t3_z3")
    
    # Fissiamo la Z1 target al valore attuale di frazione o a un valore standard (es 80%)
    z1_final_target = 0.80 # Assunzione ingegneristica di base
    k_t3 = (10**target_pi_t3) / 100
    z2_final = (z1_final_target * (1 - z1_final_target)) / (k_t3 + z1_final_target)
    z3_final = 1 - z1_final_target - z2_final
    
    rem_z1 = max(0, (target_vol * z1_final_target) - curr_z1)
    rem_z2 = max(0, (target_vol * z2_final) - curr_z2)
    rem_z3 = max(0, (target_vol * z3_final) - curr_z3)
    
    st.subheader("📋 Output: Minuti Rimanenti da eseguire")
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.warning(f"Z1: {int(rem_z1)} min")
    res_col2.info(f"Z2: {int(rem_z2)} min")
    res_col3.success(f"Z3: {int(rem_z3)} min")
