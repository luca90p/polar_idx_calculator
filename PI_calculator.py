import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- MOTORE MATEMATICO ESATTO ---

def calculate_pi(z1, z2, z3):
    total = z1 + z2 + z3
    if total == 0: return 0.0
    f1, f2, f3 = z1/total, z2/total, z3/total
    denom = max(f2, 0.0001) 
    return np.log10((f1 / denom) * f3 * 100)

def solve_z2_quadratic(z1, z3, target_pi):
    """
    Trova Z2 necessario dati Z1 e Z3 fissi.
    Risolve: K * Z2^2 + K(Z1+Z3)*Z2 - Z1*Z3 = 0
    """
    K = (10**target_pi) / 100.0
    a = K
    b = K * (z1 + z3)
    c = - (z1 * z3)
    
    delta = b**2 - 4*a*c
    if delta < 0: return None
    
    # Soluzione positiva
    z2 = (-b + np.sqrt(delta)) / (2*a)
    return max(0, z2)

def solve_z1_linear(z2, z3, target_pi):
    """
    Trova Z1 necessario dati Z2 e Z3 fissi.
    Equazione: Z1 * (Z3 - K*Z2) = K*Z2*(Z2+Z3)
    Asintoto: Se Z3 <= K*Z2, impossibile alzare il PI aumentando solo Z1.
    """
    K = (10**target_pi) / 100.0
    denom = z3 - (K * z2)
    
    if denom <= 0: return float('inf') # Impossibile (Asintoto raggiunto)
    
    num = K * z2 * (z2 + z3)
    z1 = num / denom
    return max(0, z1)

def solve_z3_linear(z1, z2, target_pi):
    """
    Trova Z3 necessario dati Z1 e Z2 fissi.
    Equazione simmetrica a Z1.
    """
    K = (10**target_pi) / 100.0
    denom = z1 - (K * z2)
    
    if denom <= 0: return float('inf')
    
    num = K * z2 * (z1 + z2)
    z3 = num / denom
    return max(0, z3)

def solve_fixed_ratio(m1, m2, m3, target_pi, f1_target=0.8):
    """
    Strategia Standard: Z1 al 80%, calcola il resto.
    """
    K = (10**target_pi) / 100.0
    
    # Dal sistema PI con f1 fisso: f3 = (K * (1-f1)) / (f1 + K)
    # f1 + f2 + f3 = 1
    denom_f3 = f1_target + K
    if denom_f3 == 0: return m1, m2, m3, "Errore Matematico"
    
    f3_ideal = (K * (1 - f1_target)) / denom_f3
    f2_ideal = 1 - f1_target - f3_ideal
    
    if f2_ideal <= 0 or f3_ideal <= 0:
        return m1, m2, m3, "Impossibile: PI troppo alto per 80% Z1"

    # Calcolo volume minimo per soddisfare i minuti già fatti
    req_vol = 0
    if f1_target > 0: req_vol = max(req_vol, m1 / f1_target)
    if f2_ideal > 0: req_vol = max(req_vol, m2 / f2_ideal)
    if f3_ideal > 0: req_vol = max(req_vol, m3 / f3_ideal)
    
    return req_vol*f1_target, req_vol*f2_ideal, req_vol*f3_ideal, "Standard 80% Z1"

# --- PLOTTING ---
def plot_pi_chart(curr_f1, curr_f3, target_f1=None, target_f3=None):
    x = np.linspace(0.01, 0.99, 200)
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Curve e Limiti
    curve_pi_2 = (1 - x) / (1 + x)
    line_a = 1 - x
    upper_bound = np.minimum(line_a, x)
    
    ax.fill_between(x, curve_pi_2, upper_bound, where=(upper_bound > curve_pi_2),
                    color='#d4edda', alpha=0.5, label='Polarizzato (>2.0)')
    ax.fill_between(x, 0, curve_pi_2, color='#fff3cd', alpha=0.5, label='Piramidale (<2.0)')
    ax.plot(x, curve_pi_2, 'k--', alpha=0.3)

    # Punti
    ax.scatter(curr_f1, curr_f3, c='red', s=80, edgecolors='k', label='Attuale', zorder=5)
    if target_f1 is not None:
        ax.scatter(target_f1, target_f3, c='blue', s=80, marker='X', edgecolors='w', label='Target', zorder=5)
        ax.arrow(curr_f1, curr_f3, target_f1-curr_f1, target_f3-curr_f3, 
                 color='k', alpha=0.2, width=0.005, length_includes_head=True)

    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.0, 0.4)
    ax.set_xlabel('Frazione Z1')
    ax.set_ylabel('Frazione Z3')
    ax.legend(loc='upper right')
    return fig

# --- APP ---
st.set_page_config(page_title="PI Solver v6.0", layout="wide")
st.title("🎛️ Performance Engineering: Solver Esatto")

tab1, tab2, tab3 = st.tabs(["1. Lab", "2. Monitoraggio", "3. Solver Ottimizzazione"])

# TAB 1 & 2 (Standard Visual)
with tab1:
    st.caption("Playground teorico")
    t_pi = st.slider("Target PI", 0.5, 3.5, 2.0)
    t_z1 = st.slider("Z1 %", 50, 95, 80)
    k = 10**t_pi / 100
    f1 = t_z1/100
    f2 = (f1*(1-f1))/(k+f1)
    st.write(f"Z1: {f1*100:.1f}% | Z2: {f2*100:.1f}% | Z3: {(1-f1-f2)*100:.1f}%")

with tab2:
    c_in, c_out = st.columns(2)
    m1 = c_in.number_input("Z1 Eseguiti", 0.0, value=120.0, step=10.0)
    m2 = c_in.number_input("Z2 Eseguiti", 0.0, value=20.0, step=5.0)
    m3 = c_in.number_input("Z3 Eseguiti", 0.0, value=15.0, step=5.0)
    pi_now = calculate_pi(m1, m2, m3)
    c_out.metric("PI Attuale", f"{pi_now:.2f}")
    tot = m1+m2+m3
    if tot > 0: c_out.pyplot(plot_pi_chart(m1/tot, m3/tot))

# TAB 3: SOLVER CORRETTO
with tab3:
    st.markdown("### 🚀 Motore di Ottimizzazione (Logica Quadratica)")
    
    col_set, col_res = st.columns([1, 2])
    
    with col_set:
        target_pi_opt = st.slider("PI Obiettivo", 1.0, 3.5, 2.4, step=0.1)
        mode = st.radio("Strategia", 
                        ["A. Standard 80% Z1", 
                         "B. Fisso Delta Z3 (Minimizza Tempo)", 
                         "C. Minimizza Tempo Totale (Libero)"])
        
        delta_z3_in = 0.0
        if "B." in mode:
            delta_z3_in = st.number_input("Minuti Z3 da aggiungere", 0.0, value=10.0, step=5.0)

    # CALCOLO SOLUZIONE
    z1_f, z2_f, z3_f, note = m1, m2, m3, "Nessuna modifica"
    
    # LOGICA A: 80% Z1
    if "A." in mode:
        z1_f, z2_f, z3_f, note = solve_fixed_ratio(m1, m2, m3, target_pi_opt)
        
    # LOGICA B: Z3 Fisso (User defined) -> Ottimizza Z1 o Z2
    elif "B." in mode:
        z3_target = m3 + delta_z3_in
        # Tentativo 1: Modifico solo Z2 (tengo Z1 fisso)
        z2_opt = solve_z2_quadratic(m1, z3_target, target_pi_opt)
        
        # Tentativo 2: Modifico solo Z1 (tengo Z2 fisso)
        z1_opt = solve_z1_linear(m2, z3_target, target_pi_opt)
        
        # Valutazione Costi (Minuti aggiunti)
        cost_z2 = (z2_opt - m2) if (z2_opt is not None and z2_opt >= m2) else float('inf')
        cost_z1 = (z1_opt - m1) if (z1_opt != float('inf') and z1_opt >= m1) else float('inf')
        
        if cost_z2 == float('inf') and cost_z1 == float('inf'):
            note = "IMPOSSIBILE: Con questa Z3 fissata, il PI target è irraggiungibile (Asintoto)."
            # Fallback: non cambio nulla o mostro errore
        elif cost_z2 < cost_z1:
            z1_f, z2_f, z3_f = m1, z2_opt, z3_target
            note = "Ottimizzato aggiungendo Z2 (Miglior tempo)"
        else:
            z1_f, z2_f, z3_f = z1_opt, m2, z3_target
            note = "Ottimizzato aggiungendo Z1 (Miglior tempo - Necessario per diluizione)"

    # LOGICA C: Global Min Time (Tocca la leva più conveniente)
    elif "C." in mode:
        # Provo tutte e 3 le strade
        # 1. Muovo Z1
        z1_c = solve_z1_linear(m2, m3, target_pi_opt)
        cost_1 = (z1_c - m1) if z1_c >= m1 else float('inf')
        
        # 2. Muovo Z2
        z2_c = solve_z2_quadratic(m1, m3, target_pi_opt)
        cost_2 = (z2_c - m2) if (z2_c is not None and z2_c >= m2) else float('inf')
        
        # 3. Muovo Z3
        z3_c = solve_z3_linear(m1, m2, target_pi_opt)
        cost_3 = (z3_c - m3) if z3_c >= m3 else float('inf')
        
        # Scelta minima
        min_cost = min(cost_1, cost_2, cost_3)
        
        if min_cost == float('inf'):
             note = "IMPOSSIBILE raggiungere il Target partendo da qui."
        elif min_cost == cost_3:
            z1_f, z2_f, z3_f, note = m1, m2, z3_c, "Strategia Pura: Aggiunta Z3"
        elif min_cost == cost_2:
            z1_f, z2_f, z3_f, note = m1, z2_c, m3, "Strategia Pura: Aggiunta Z2"
        else:
            z1_f, z2_f, z3_f, note = z1_c, m2, m3, "Strategia Pura: Aggiunta Z1"

    # OUTPUT RISULTATI
    with col_res:
        if "IMPOSSIBILE" in note:
            st.error(note)
            st.warning("Suggerimento: Aumenta i minuti di Z3 o riduci il PI target.")
        else:
            st.success(f"💡 Soluzione Trovata: {note}")
            
            add_1, add_2, add_3 = max(0, z1_f-m1), max(0, z2_f-m2), max(0, z3_f-m3)
            
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("AGGIUNGI Z1", f"+{int(add_1)} min")
            cc2.metric("AGGIUNGI Z2", f"+{int(add_2)} min")
            cc3.metric("AGGIUNGI Z3", f"+{int(add_3)} min")
            
            st.divider()
            tot_f = z1_f + z2_f + z3_f
            pi_f = calculate_pi(z1_f, z2_f, z3_f)
            
            st.write(f"**Volume Finale:** {int(tot_f)} min | **PI Calcolato:** {pi_f:.2f}")
            
            if tot_f > 0:
                st.pyplot(plot_pi_chart(
                    m1/(tot) if tot>0 else 0, m3/(tot) if tot>0 else 0,
                    z1_f/tot_f, z3_f/tot_f
                ))
