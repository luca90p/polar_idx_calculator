import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- MOTORE MATEMATICO ---

def calculate_pi(z1, z2, z3):
    total = z1 + z2 + z3
    if total == 0: return 0.0
    f1, f2, f3 = z1/total, z2/total, z3/total
    denom = max(f2, 0.0001) 
    return np.log10((f1 / denom) * f3 * 100)

def solve_min_time_global(m1, m2, m3, target_pi):
    """
    Trova l'aggiunta minima (x1, x2, x3) per raggiungere il PI target
    partendo da m1, m2, m3.
    Equazione: (m2 + x2) * K = (m1 + x1) * (m3 + x3)
    """
    K_target = (10**target_pi) / 100.0
    
    # Calcolo il K attuale per vedere se devo alzare o abbassare il PI
    # K = (Z1 * Z3) / Z2
    denom_curr = max(m2, 0.0001)
    K_curr = (m1 * m3) / denom_curr
    
    # Caso 1: Il PI attuale è troppo ALTO (K_curr > K_target).
    # Devo abbassare il PI. Il modo più rapido è aumentare il denominatore (Z2).
    # Aumentare Z1 o Z3 peggiorerebbe o sarebbe inefficiente.
    if K_curr > K_target:
        # Risolvo per Z2: Z2 = (Z1 * Z3) / K_target
        z2_needed = (m1 * m3) / K_target
        x2 = max(0, z2_needed - m2)
        return m1, m2 + x2, m3, f"PI troppo alto. Aggiunta Z2 chirurgica per sopprimere VLaMax."
        
    # Caso 2: Il PI attuale è troppo BASSO (K_curr < K_target).
    # Devo alzare il PI. Devo aumentare il numeratore (Z1 * Z3).
    # (m2 * K_target) = Z1 * Z3.  Chiamo P = m2 * K_target.
    # Devo trovare Z1 >= m1 e Z3 >= m3 tali che Z1*Z3 = P minimizzando (Z1-m1) + (Z3-m3).
    else:
        P = m2 * K_target
        # Se m1*m3 è già < P (sicuro, visto K_curr < K_target), devo alzare il prodotto.
        # Per minimizzare la somma aggiunta x1+x3 per raggiungere un prodotto P,
        # conviene aggiungere al fattore che è "accoppiato" col valore più alto.
        # Esempio: voglio arrivare a 100. Ho 10 * 2 = 20.
        # Aumento il 2: 10 * 10 = 100 (aggiungo 8).
        # Aumento il 10: 50 * 2 = 100 (aggiungo 40).
        # Quindi conviene aumentare il valore più piccolo (o meglio, quello che richiede meno delta).
        
        # Opzione A: Tengo Z3 fisso, aumento Z1
        z1_opt_a = P / m3
        cost_a = z1_opt_a - m1
        
        # Opzione B: Tengo Z1 fisso, aumento Z3
        z3_opt_b = P / m1
        cost_b = z3_opt_b - m3
        
        if cost_a < cost_b:
            return m1 + cost_a, m2, m3, "PI basso. Aggiungo Z1 (Strategia Minimo Volume)."
        else:
            return m1, m2, m3 + cost_b, "PI basso. Aggiungo Z3 (Strategia Minimo Volume)."

def solve_fixed_z3_min_time(m1, m2, m3, delta_z3, target_pi):
    """
    Fissa Z3 finale. Minimizza Z1 o Z2 aggiunti per centrare l'equazione.
    """
    z3_final = m3 + delta_z3
    K = (10**target_pi) / 100.0
    
    # Equazione: Z2 * K = Z1 * Z3
    # Z2 = (Z1 * Z3) / K
    
    # Provo a non aggiungere Z1 (x1=0). Vediamo quanta Z2 serve.
    z2_req_base = (m1 * z3_final) / K
    
    if z2_req_base >= m2:
        # Caso A: Basta aggiungere Z2.
        return m1, z2_req_base, z3_final, "Z3 Fissata. Bilanciamento tramite Z2."
    else:
        # Caso B: Ho già troppa Z2. Devo aumentare Z1 per bilanciare l'equazione.
        # Z1 = (Z2 * K) / Z3
        z1_req = (m2 * K) / z3_final
        return z1_req, m2, z3_final, "Z3 Fissata. Eccesso di Z2 compensato aumentando Z1."

def solve_fixed_ratio_z1(m1, m2, m3, target_pi, ratio=0.8):
    """
    Cerca di ottenere Z1 = 80% del totale, rispettando il PI e i minuti già fatti.
    """
    K = (10**target_pi) / 100.0
    
    # 1. Calcolo i rapporti ideali f1, f2, f3
    f1 = ratio
    # Dal sistema PI: f3 = (K * (1-f1)) / (f1 + K)
    f3 = (K * (1 - f1)) / (f1 + K)
    f2 = 1 - f1 - f3
    
    if f2 < 0 or f3 < 0:
        return m1, m2, m3, "Impossibile matematicamente con questo PI e 80% Z1."

    # 2. Calcolo il volume totale necessario per soddisfare i minuti già fatti
    # Total >= m1/f1, Total >= m2/f2, Total >= m3/f3
    # Gestisco divisione per zero
    req_1 = m1/f1 if f1 > 0 else 0
    req_2 = m2/f2 if f2 > 0 else 0
    req_3 = m3/f3 if f3 > 0 else 0
    
    total_needed = max(req_1, req_2, req_3)
    
    return total_needed*f1, total_needed*f2, total_needed*f3, "Vincolo 80% Z1 rispettato."

# --- PLOTTING ---
def plot_pi_chart(curr_f1=None, curr_f3=None, target_f1=None, target_f3=None):
    x = np.linspace(0.01, 0.99, 200)
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Linee limite
    line_a = 1 - x
    curve_pi_2 = (1 - x) / (1 + x)
    upper_bound = np.minimum(line_a, x)
    
    # Aree
    ax.fill_between(x, curve_pi_2, upper_bound, where=(upper_bound > curve_pi_2),
                    color='#d4edda', alpha=0.5, label='Polarizzato (>2.0)')
    ax.fill_between(x, 0, curve_pi_2, color='#fff3cd', alpha=0.5, label='Piramidale (<2.0)')
    ax.plot(x, curve_pi_2, 'k--', alpha=0.3)

    if curr_f1 is not None:
        ax.scatter(curr_f1, curr_f3, color='red', s=100, label='Attuale', zorder=5, edgecolors='k')
    if target_f1 is not None:
        ax.scatter(target_f1, target_f3, color='blue', s=100, marker='X', label='Target Ottimale', zorder=5, edgecolors='w')
        if curr_f1:
            ax.arrow(curr_f1, curr_f3, target_f1-curr_f1, target_f3-curr_f3, 
                     color='k', alpha=0.3, width=0.005)

    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.0, 0.4)
    ax.set_xlabel('Frazione Z1')
    ax.set_ylabel('Frazione Z3')
    ax.legend(loc='upper right')
    return fig

# --- MAIN APP ---
st.set_page_config(page_title="PI Solver v5.0", layout="wide")
st.title("🎛️ Performance Engineering: TID Optimizer")

tab1, tab2, tab3 = st.tabs(["1. Lab", "2. Monitoraggio", "3. Solver Ottimizzazione"])

# TAB 1 & 2 (Standard)
with tab1:
    st.write("Simulatore teorico (non collegato ai dati reali)")
    t_pi = st.slider("Target PI", 0.5, 3.5, 2.0)
    t_z1 = st.slider("Z1 %", 50, 95, 80)
    k = 10**t_pi / 100
    f1 = t_z1/100
    f2 = (f1*(1-f1))/(k+f1)
    st.write(f"Z1: {f1*100:.1f}% | Z2: {f2*100:.1f}% | Z3: {(1-f1-f2)*100:.1f}%")

with tab2:
    col_in, col_out = st.columns(2)
    m1 = col_in.number_input("Z1 Eseguiti", 0.0, value=120.0, step=10.0)
    m2 = col_in.number_input("Z2 Eseguiti", 0.0, value=20.0, step=5.0)
    m3 = col_in.number_input("Z3 Eseguiti", 0.0, value=15.0, step=5.0)
    pi_now = calculate_pi(m1, m2, m3)
    col_out.metric("PI Attuale", f"{pi_now:.2f}")
    if (m1+m2+m3)>0:
        col_out.pyplot(plot_pi_chart(m1/(m1+m2+m3), m3/(m1+m2+m3)))

# TAB 3 (NUOVA LOGICA)
with tab3:
    st.markdown("### 🚀 Motore di Ottimizzazione")
    
    c_set, c_res = st.columns([1, 2])
    
    with c_set:
        target_pi_opt = st.slider("1. PI Obiettivo", 1.0, 3.5, 2.5, step=0.1)
        mode = st.radio("2. Strategia di Calcolo", 
                        ["A. Standard 80% Z1 (Volume Variabile)", 
                         "B. Fisso Delta Z3 + Minimizza Tempo", 
                         "C. Minimizza Tempo Totale (Algoritmo Puro)"])
        
        delta_z3_in = 0
        if "B." in mode:
            delta_z3_in = st.number_input("Minuti Z3 da aggiungere", 0.0, value=20.0, step=5.0)

    # CALCOLO
    z1_f, z2_f, z3_f, note = m1, m2, m3, "Errore"
    
    if "A." in mode:
        z1_f, z2_f, z3_f, note = solve_fixed_ratio_z1(m1, m2, m3, target_pi_opt, 0.8)
    elif "B." in mode:
        z1_f, z2_f, z3_f, note = solve_fixed_z3_min_time(m1, m2, m3, delta_z3_in, target_pi_opt)
    elif "C." in mode:
        z1_f, z2_f, z3_f, note = solve_min_time_global(m1, m2, m3, target_pi_opt)
        
    # OUTPUT
    with c_res:
        st.info(f"💡 Logica Applicata: **{note}**")
        
        add_1 = max(0, z1_f - m1)
        add_2 = max(0, z2_f - m2)
        add_3 = max(0, z3_f - m3)
        
        cc1, cc2, cc3 = st.columns(3)
        cc1.success(f"AGGIUNGI Z1\n# +{int(add_1)} min")
        cc2.warning(f"AGGIUNGI Z2\n# +{int(add_2)} min")
        cc3.error(f"AGGIUNGI Z3\n# +{int(add_3)} min")
        
        st.divider()
        tot_f = z1_f + z2_f + z3_f
        pi_f = calculate_pi(z1_f, z2_f, z3_f)
        
        st.write(f"**Volume Finale:** {int(tot_f)} min | **PI Finale:** {pi_f:.2f}")
        
        if tot_f > 0:
            st.pyplot(plot_pi_chart(
                m1/(m1+m2+m3) if (m1+m2+m3)>0 else 0, m3/(m1+m2+m3) if (m1+m2+m3)>0 else 0,
                z1_f/tot_f, z3_f/tot_f
            ))
