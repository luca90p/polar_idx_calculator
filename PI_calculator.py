import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- MOTORE DI CALCOLO FISIOLOGICO ---

def calculate_pi(z1, z2, z3):
    """Calcola il Polarization Index secondo Treff et al."""
    total = z1 + z2 + z3
    if total == 0: return 0.0
    f1, f2, f3 = z1/total, z2/total, z3/total
    # Protezione matematica per Z2=0
    denom = max(f2, 0.0001) 
    return np.log10((f1 / denom) * f3 * 100)

def solve_quadratic_for_z2(z1, z3, target_pi):
    """
    Risolve l'equazione inversa del PI per trovare Z2, dati Z1 e Z3 fissi.
    Formula derivata: K * Z2^2 + K(Z1+Z3)*Z2 - Z1*Z3 = 0
    dove K = 10^PI / 100
    """
    if target_pi <= 0: return 0
    k = (10**target_pi) / 100
    
    # Coefficienti eq. di secondo grado: ax^2 + bx + c = 0
    a = k
    b = k * (z1 + z3)
    c = - (z1 * z3)
    
    # Formula risolutiva
    delta = b**2 - 4*a*c
    if delta < 0: return 0 # Impossibile
    z2 = (-b + np.sqrt(delta)) / (2*a)
    return max(0, z2)

def solve_for_z1_z2_given_z3_and_ratio(z3_total, target_pi, target_f1_ratio=0.8):
    """
    Trova Z1 e Z2 ideali dato un Z3 fisso e un desiderio di mantenere Z1 al X% del totale.
    """
    # 1. Calcoliamo f3 necessario per il PI dato f1 fisso
    # PI = log((f1/f2)*f3*100) -> 10^PI/100 = K
    # K = (f1 * f3) / (1 - f1 - f3)
    # Risolvendo per f3:
    k = (10**target_pi) / 100
    f3_ideal = (k * (1 - target_f1_ratio)) / (target_f1_ratio + k)
    
    if f3_ideal <= 0: return 0, 0 # PI impossibile con questo ratio
    
    # 2. Calcoliamo il volume totale necessario per supportare quel Z3
    # Z3 = Total * f3_ideal -> Total = Z3 / f3_ideal
    total_needed = z3_total / f3_ideal
    
    z1_ideal = total_needed * target_f1_ratio
    z2_ideal = total_needed * (1 - target_f1_ratio - f3_ideal)
    
    return z1_ideal, z2_ideal

# --- VISUALIZZAZIONE GRAFICA ---

def plot_pi_chart(curr_f1=None, curr_f3=None, target_f1=None, target_f3=None):
    x = np.linspace(0.01, 0.99, 200)
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Vincoli geometrici Treff et al.
    line_a = 1 - x           # Limite fisico (f2=0)
    line_b = (1 - x) / 2     # Limite polarizzazione (f3>f2)
    line_c = x               # Limite prevalenza (f1>f3)
    curve_pi_2 = (1 - x) / (1 + x) # Curva PI=2.0
    
    # Aree
    upper_bound = np.minimum(line_a, line_c)
    ax.fill_between(x, curve_pi_2, upper_bound, where=(upper_bound > curve_pi_2),
                    color='#d4edda', label='Polarizzato (PI > 2.0)') # Verde chiaro
    ax.fill_between(x, 0, curve_pi_2, color='#fff3cd', label='Piramidale (PI < 2.0)') # Giallo chiaro

    # Curva PI=2
    ax.plot(x, curve_pi_2, color='gray', linestyle='--', linewidth=1)

    # Punto Attuale
    if curr_f1 is not None:
        ax.scatter(curr_f1, curr_f3, color='red', s=100, label='Attuale', zorder=5, edgecolors='black')
        
    # Punto Target
    if target_f1 is not None:
        ax.scatter(target_f1, target_f3, color='blue', s=100, marker='X', label='Target', zorder=5, edgecolors='white')
        # Freccia
        if curr_f1 is not None:
            ax.arrow(curr_f1, curr_f3, target_f1-curr_f1, target_f3-curr_f3, 
                     head_width=0.02, color='black', alpha=0.5, length_includes_head=True)

    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.0, 0.4)
    ax.set_xlabel('Frazione Z1')
    ax.set_ylabel('Frazione Z3')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.2)
    return fig

# --- APP STREAMLIT ---

st.set_page_config(page_title="PI Calculator Pro", layout="wide")
st.title("🎛️ Performance Engineering: TID Solver")

tab1, tab2, tab3 = st.tabs(["1. Lab Combinazioni", "2. Monitoraggio", "3. Calcolatore Target"])

# TAB 1: Esplorazione Teorica
with tab1:
    st.markdown("### 📐 Simulatore Teorico")
    t1_pi = st.slider("Target PI", 0.5, 3.5, 2.0, key="t1")
    t1_z1_pct = st.slider("Frazione Z1 desiderata (%)", 50, 95, 80, key="t1_z1")
    
    # Calcolo inverso
    f1 = t1_z1_pct / 100
    k = (10**t1_pi) / 100
    f2 = (f1 * (1 - f1)) / (k + f1)
    f3 = 1 - f1 - f2
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Z1 %", f"{f1*100:.1f}%")
    c2.metric("Z2 %", f"{f2*100:.1f}%")
    c3.metric("Z3 %", f"{f3*100:.1f}%")
    
    if f2 < 0 or f3 < 0:
        st.error("Combinazione impossibile (richiede percentuali negative). Abbassa Z1 o cambia PI.")

# TAB 2: Input Dati
with tab2:
    st.markdown("### 📊 Inserimento Telemetria")
    c1, c2, c3 = st.columns(3)
    m1 = c1.number_input("Minuti Z1 Eseguiti", 0.0, step=10.0, value=120.0)
    m2 = c2.number_input("Minuti Z2 Eseguiti", 0.0, step=5.0, value=15.0)
    m3 = c3.number_input("Minuti Z3 Eseguiti", 0.0, step=5.0, value=10.0)
    
    tot_done = m1 + m2 + m3
    pi_now = calculate_pi(m1, m2, m3)
    
    st.metric("PI Attuale", f"{pi_now:.2f}", delta="Polarizzato" if pi_now > 2.0 else "Piramidale")
    if tot_done > 0:
        st.pyplot(plot_pi_chart(m1/tot_done, m3/tot_done))

# TAB 3: Il Solver (Core della richiesta)
with tab3:
    st.markdown("### 🚀 Pianificazione Scientifica")
    st.info("Obiettivo: Raggiungere il PI target considerando i minuti GIA' eseguiti.")
    
    col_setup, col_res = st.columns([1, 2])
    
    with col_setup:
        target_pi_val = st.slider("PI Obiettivo Finale", 1.0, 3.5, 2.5, step=0.1)
        
        # Logica di Input richiesta dall'utente
        add_mode = st.radio("Vincolo di Progetto:", ["Fisso Delta Z3 (Aggiungo Qualità)", "Minimizza Tempo Totale"])
        
        delta_z3 = 0.0
        if add_mode == "Fisso Delta Z3 (Aggiungo Qualità)":
            delta_z3 = st.number_input("Quanti minuti di Z3 vuoi aggiungere?", 0.0, value=20.0, step=5.0)
    
    # --- LOGICA DEL SOLVER ---
    z1_final, z2_final, z3_final = 0, 0, 0
    
    # Calcolo Z3 Finale Target
    if add_mode == "Fisso Delta Z3 (Aggiungo Qualità)":
        z3_target = m3 + delta_z3
    else:
        z3_target = max(m3, 1.0) # Minimo sindacale per calcolo
        
    # --- STRATEGIA 1: TENTATIVO CON Z1 AL 80% (STANDARD D'ELITE) ---
    # Proviamo a vedere se con Z3 fisso e Z1 all'80% i numeri "ci stanno"
    z1_ideal, z2_ideal = solve_for_z1_z2_given_z3_and_ratio(z3_target, target_pi_val, 0.80)
    
    # Verifica compatibilità con minuti già fatti (Sunk Costs)
    if z1_ideal >= m1 and z2_ideal >= m2:
        # Scenario Perfetto: Possiamo raggiungere il PI mantenendo la struttura 80% Z1
        z1_final, z2_final, z3_final = z1_ideal, z2_ideal, z3_target
        calc_note = "Soluzione Ottimale (Z1 mantenuta all'80%)"
    else:
        # Scenario Complesso: Abbiamo già fatto troppa Z1 o Z2 per mantenere l'80% esatto.
        # Dobbiamo adattarci. Manteniamo i minuti già fatti come base.
        
        # Caso A: Abbiamo troppa Z1 (m1 > z1_ideal). 
        # Fissiamo Z1 = m1 (non aggiungiamo altro Z1 se non necessario) e Z3 = target.
        # Calcoliamo la Z2 necessaria per bilanciare questa Z1 eccessiva e colpire il PI.
        z1_base = max(m1, z1_ideal)
        z2_calc = solve_quadratic_for_z2(z1_base, z3_target, target_pi_val)
        
        if z2_calc >= m2:
            # Basta aggiungere Z2
            z1_final, z2_final, z3_final = z1_base, z2_calc, z3_target
            calc_note = "Adattamento: Z1 fissata al volume attuale, Z2 compensata."
        else:
            # Caso B: Abbiamo anche troppa Z2 (z2_calc < m2).
            # Significa che Z1 e Z2 attuali sono sbilanciati per quel PI.
            # Dobbiamo aumentare Z1 per diluire la Z2 eccessiva.
            # Risolviamo iterativamente o incrementando Z1 finché l'equazione Z2 regge.
            # Metodo semplificato: Fissiamo Z2 = m2 e Z3 = target, calcoliamo Z1 necessario.
            # K = (Z1/Z2)*Z3 -> Z1 = (K*Z2)/Z3
            # Attenzione alla formula esatta PI. 
            # 10^PI/100 = K. K = (Z1/Z2)*Z3 (approssimato per Z2>0). 
            # Z1 = (K * m2) / f3_target? No, f3 cambia.
            # Usiamo loop di ricerca rapido per stabilità o formula inversa Z1.
            # K = (f1/f2)*f3. Z1 = Volume * f1. 
            # Formula inversa diretta: Z1 = (K * Z2^2 + K * Z2 * Z3) / (Z3 - K * Z2)
            # Dove K = 10^PI / 100
            
            K = (10**target_pi_val) / 100
            denom = z3_target - K * m2
            if denom > 0:
                z1_needed = (K * m2 * (m2 + z3_target)) / denom
                z1_final = max(z1_needed, m1)
                z2_final = m2
                z3_final = z3_target
                calc_note = "Adattamento Forzato: Aggiunta Z1 extra per compensare eccesso di Z2."
            else:
                st.error("Configurazione matematica impossibile con questi minuti eseguiti. Aumenta Z3.")
                z1_final, z2_final, z3_final = m1, m2, m3

    # --- OUTPUT RISULTATI ---
    with col_res:
        # Calcolo Delta
        add_z1 = max(0, z1_final - m1)
        add_z2 = max(0, z2_final - m2)
        add_z3 = max(0, z3_final - m3)
        
        st.markdown(f"#### 📝 Tabella di Marcia ({calc_note})")
        
        c_res1, c_res2, c_res3 = st.columns(3)
        c_res1.success(f"**+ {int(add_z1)} min**\n\nZ1 (Corsa Lenta)")
        c_res2.info(f"**+ {int(add_z2)} min**\n\nZ2 (Soglia)")
        c_res3.warning(f"**+ {int(add_z3)} min**\n\nZ3 (Qualità)")
        
        st.divider()
        final_tot = z1_final + z2_final + z3_final
        final_real_pi = calculate_pi(z1_final, z2_final, z3_final)
        
        st.write(f"**Volume Finale:** {int(final_tot)} min")
        st.write(f"**PI Finale Previsto:** {final_real_pi:.4f} (Target: {target_pi_val})")
        
        # Grafico Target
        if final_tot > 0:
            st.pyplot(plot_pi_chart(
                curr_f1=m1/tot_done if tot_done>0 else 0, 
                curr_f3=m3/tot_done if tot_done>0 else 0,
                target_f1=z1_final/final_tot,
                target_f3=z3_final/final_tot
            ))
