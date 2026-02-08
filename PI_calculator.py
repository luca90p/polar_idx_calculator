import streamlit as st
import numpy as np
import pandas as pd

def calculate_pi(z1, z2, z3):
    total = z1 + z2 + z3
    if total == 0: return 0.0
    f1, f2, f3 = z1/total, z2/total, z3/total
    denom = max(f2, 0.0001) 
    return np.log10((f1 / denom) * f3 * 100)

def solve_for_f3_with_f1(f1, pi_target):
    k = (10**pi_target) / 100
    # K = (f1 / (1 - f1 - f3)) * f3  => K(1 - f1 - f3) = f1 * f3
    # K - K*f1 - K*f3 = f1*f3 => K(1 - f1) = (f1 + K) * f3
    return (k * (1 - f1)) / (f1 + k)

st.set_page_config(page_title="TID Control System v4.0", layout="wide")
st.title("🎛️ Controllo di Processo: TID & Polarization Dashboard")

tab1, tab2, tab3 = st.tabs(["1. Design Combinazioni", "2. Tracking Real-Time", "3. Planning Rimanente"])

# --- TAB 1 & 2 (Invariati per continuità) ---
with tab1:
    st.header("📐 Sintesi delle Combinazioni")
    target_pi_t1 = st.slider("Imposta PI Desiderato (a.U.)", 0.5, 3.5, 2.0, step=0.1)
    k = (10**target_pi_t1) / 100
    z1_range = np.linspace(0.70, 0.95, 26)
    results_t1 = []
    for z1 in z1_range:
        z2 = (z1 * (1 - z1)) / (k + z1)
        z3 = 1 - z1 - z2
        if z2 >= 0 and z3 >= 0:
            results_t1.append({"Z1 %": z1*100, "Z2 %": z2*100, "Z3 %": z3*100})
    st.table(pd.DataFrame(results_t1).style.format("{:.1f}"))

with tab2:
    st.header("📊 Telemetria in Tempo Reale")
    c1, c2, c3 = st.columns(3)
    m1_done = c1.number_input("Minuti Z1 fatti", min_value=0.0, value=120.0)
    m2_done = c2.number_input("Minuti Z2 fatti", min_value=0.0, value=20.0)
    m3_done = c3.number_input("Minuti Z3 fatti", min_value=0.0, value=15.0)
    st.metric("PI Attuale", f"{calculate_pi(m1_done, m2_done, m3_done):.2f}")

# --- TAB 3: PLANNING AGGIORNATO ---
with tab3:
    st.header("🔧 Ottimizzazione del Lavoro Rimanente")
    st.write("Calcola il bilanciamento Z1/Z2 necessario in base ai minuti di Z3 che vuoi aggiungere.")
    
    target_pi = st.slider("Target PI Settimanale", 1.0, 3.5, 2.5, key="t3_pi")
    
    # Nuova opzione chiesta dall'utente
    strategy = st.radio("Strategia di Pianificazione:", 
                        ("Specifica Delta Z3 (+ 80% Z1)", "Standard 80% Z1 (Volume Fisso)", "Minimizza Tempo Totale"))
    
    res_final = None
    
    if strategy == "Specifica Delta Z3 (+ 80% Z1)":
        delta_z3 = st.number_input("Quanti altri minuti in Z3 vuoi fare?", min_value=0.0, value=30.0)
        z3_final_target = m3_done + delta_z3
        f1_fixed = 0.80 # Standard d'élite
        
        # Risoluzione per il volume totale necessario
        f3_required = solve_for_f3_with_f1(f1_fixed, target_pi)
        if f3_required > 0:
            total_vol_needed = z3_final_target / f3_required
            res_final = (total_vol_needed * f1_fixed, total_vol_needed * (0.2 - f3_required), z3_final_target)
        
    elif strategy == "Standard 80% Z1 (Volume Fisso)":
        target_vol = st.number_input("Volume Totale Target (min)", value=300)
        f1 = 0.80
        f2 = (f1 * (1 - f1)) / ((10**target_pi / 100) + f1)
        res_final = (target_vol * f1, target_vol * f2, target_vol * (1-f1-f2))
        
    else: # Minimizza Tempo Totale
        best_m = float('inf')
        for f1_t in np.linspace(0.60, 0.95, 351):
            k_t = (10**target_pi) / 100
            f2_t = (f1_t * (1 - f1_t)) / (k_t + f1_t)
            f3_t = 1 - f1_t - f2_t
            if f2_t > 0 and f3_t > 0:
                m_req = max(m1_done/f1_t, m2_done/f2_t, m3_done/f3_t)
                if m_req < best_m:
                    best_m, res_final = m_req, (m_req*f1_t, m_req*f2_t, m_req*f3_t)

    if res_final:
        r1, r2, r3 = max(0, res_final[0]-m1_done), max(0, res_final[1]-m2_done), max(0, res_final[2]-m3_done)
        st.subheader("📋 Output: Minuti Rimanenti da Eseguire")
        oc1, oc2, oc3 = st.columns(3)
        oc1.warning(f"Z1 (Easy): {int(r1)} min")
        oc2.info(f"Z2 (Soglia): {int(r2)} min")
        oc3.success(f"Z3 (Qualità): {int(r3)} min")
        
        st.write(f"**Volume Finale Settimana:** {int(sum(res_final))} min | PI Finale: {target_pi:.2f}")
        if r1 + r2 + r3 == 0:
            st.error("⚠️ Attenzione: I minuti già eseguiti superano la configurazione target per questo PI.")
