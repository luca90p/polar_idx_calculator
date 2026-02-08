import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- FUNZIONI DI CALCOLO ---
def calculate_pi(z1, z2, z3):
    total = z1 + z2 + z3
    if total == 0: return 0.0
    f1, f2, f3 = z1/total, z2/total, z3/total
    denom = max(f2, 0.0001) 
    return np.log10((f1 / denom) * f3 * 100)

def solve_for_f3_with_f1(f1, pi_target):
    k = (10**pi_target) / 100
    # Formula inversa derivata per f3 dato f1 e PI
    # k = (f1 * f3) / (1 - f1 - f3)  -> k - k*f1 - k*f3 = f1*f3
    return (k * (1 - f1)) / (f1 + k)

def solve_for_f3_standard(f1, target_pi):
    # Risolve il sistema classico dove f2 è determinato dal PI
    k = (10**target_pi) / 100
    f2 = (f1 * (1 - f1)) / (k + f1)
    return 1 - f1 - f2

# --- FUNZIONE GRAFICA (FIGURA 2 TREFF ET AL.) ---
def plot_pi_chart(curr_f1=None, curr_f3=None, label="Tu sei qui", color='red'):
    x = np.linspace(0.01, 0.99, 200)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # --- Linee Vincolo (Paper Figure 2) ---
    # Linea a: f1 + f2 + f3 = 1 (con f2=0) -> f3 = 1 - f1 (Limite fisico superiore)
    line_a = 1 - x
    
    # Linea b: f3 > f2 -> f3 > (1-f1)/2 (Limite inferiore polarizzazione strutturale)
    line_b = (1 - x) / 2
    
    # Linea c: f1 > f3 -> f3 = f1 (Limite prevalenza aerobica)
    line_c = x
    
    # Linea d: f1 > f2 -> f2 = f1 -> f3 = 1 - 2*f1 (Limite base aerobica)
    line_d = 1 - 2*x
    
    # --- Curva PI = 2.00 (Soglia Polarizzazione) ---
    # f3 = (1-f1) / (1+f1) derivata da log((f1/f2)*f3*100)=2
    curve_pi_2 = (1 - x) / (1 + x)
    
    # Plot delle linee
    ax.plot(x, line_a, 'k-', lw=1, alpha=0.3, label='Limite Fisico (a)')
    ax.plot(x, line_c, 'k--', lw=1, alpha=0.3, label='f1 = f3 (c)')
    
    # --- Colorazione Aree ---
    # Area VERDE (Polarizzata): PI > 2.00
    # Delimitata inferiormente dalla curva PI=2 e superiormente dai limiti fisici (min tra linea a e linea c)
    upper_bound = np.minimum(line_a, line_c)
    ax.fill_between(x, curve_pi_2, upper_bound, 
                    where=(upper_bound > curve_pi_2),
                    color='green', alpha=0.2, label='Area Polarizzata (PI > 2.0)')
    
    # Area GIALLA (Non Polarizzata): PI <= 2.00
    # Delimitata superiormente dalla curva PI=2 e inferiormente da linea b (o d)
    lower_bound = np.maximum(0, line_b) # f3 non può essere negativo
    ax.fill_between(x, lower_bound, curve_pi_2,
                    where=(curve_pi_2 > lower_bound),
                    color='yellow', alpha=0.2, label='Area Piramidale/Soglia')

    # Curva PI=2 in evidenza
    ax.plot(x, curve_pi_2, 'b--', lw=2, label='Soglia PI = 2.00')

    # --- Punto Utente ---
    if curr_f1 is not None and curr_f3 is not None:
        ax.scatter(curr_f1, curr_f3, color=color, s=150, zorder=10, edgecolors='black', label=label)
        # Annotazione coordinate
        ax.annotate(f"  Z1:{curr_f1:.0%} Z3:{curr_f3:.0%}", (curr_f1, curr_f3), fontsize=9)

    # Setup Grafico
    ax.set_xlim(0.4, 1.0) # Zoom sulla zona di interesse (Z1 40-100%)
    ax.set_ylim(0.0, 0.4) # Zoom su Z3 (0-40%)
    ax.set_xlabel('Frazione Zona 1 (Base Aerobica)')
    ax.set_ylabel('Frazione Zona 3 (Alta Intensità)')
    ax.set_title('Spazio delle Fasi TID (Treff et al.)')
    ax.legend(loc='upper right', fontsize='small')
    ax.grid(True, alpha=0.2)
    
    return fig

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="TID Control System v5.0", layout="wide")
st.title("🎛️ Controllo di Processo: TID & Polarization Dashboard")

tab1, tab2, tab3 = st.tabs(["1. Design Combinazioni", "2. Tracking Real-Time", "3. Planning Rimanente"])

# --- TAB 1: DESIGN (Invariato) ---
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

# --- TAB 2: TRACKING REAL-TIME (Aggiornato con Grafico) ---
with tab2:
    st.header("📊 Telemetria in Tempo Reale")
    col_input, col_plot = st.columns([1, 2])
    
    with col_input:
        m1_done = st.number_input("Minuti Z1 fatti", min_value=0.0, value=120.0)
        m2_done = st.number_input("Minuti Z2 fatti", min_value=0.0, value=20.0)
        m3_done = st.number_input("Minuti Z3 fatti", min_value=0.0, value=15.0)
        
        total_done = m1_done + m2_done + m3_done
        current_pi = calculate_pi(m1_done, m2_done, m3_done)
        
        st.divider()
        st.metric("PI Attuale", f"{current_pi:.2f} a.U.")
        st.metric("Volume Totale", f"{int(total_done)} min")
        
        if current_pi > 2.0:
            st.success("Stato: POLARIZZATO (Area Verde)")
        elif total_done > 0:
            st.warning("Stato: PIRAMIDALE / SOGLIA (Area Gialla)")

    with col_plot:
        if total_done > 0:
            f1_curr = m1_done / total_done
            f3_curr = m3_done / total_done
            st.pyplot(plot_pi_chart(f1_curr, f3_curr, label="Stato Attuale", color='red'))
        else:
            st.info("Inserisci i minuti per visualizzare il grafico.")

# --- TAB 3: PLANNING RIMANENTE (Aggiornato con Grafico Target) ---
with tab3:
    st.header("🔧 Ottimizzazione del Lavoro Rimanente")
    st.write("Calcola il bilanciamento Z1/Z2 necessario in base ai minuti di Z3 che vuoi aggiungere.")
    
    col_plan_input, col_plan_plot = st.columns([1, 2])
    
    with col_plan_input:
        target_pi = st.slider("Target PI Settimanale", 1.0, 3.5, 2.5, key="t3_pi")
        
        strategy = st.radio("Strategia di Pianificazione:", 
                            ("Specifica Delta Z3 (+ 80% Z1)", "Standard 80% Z1 (Volume Fisso)", "Minimizza Tempo Totale"))
        
        res_final = None
        
        if strategy == "Specifica Delta Z3 (+ 80% Z1)":
            delta_z3 = st.number_input("Quanti altri minuti in Z3 vuoi fare?", min_value=0.0, value=30.0)
            z3_final_target = m3_done + delta_z3
            f1_fixed = 0.80 
            
            f3_required = solve_for_f3_with_f1(f1_fixed, target_pi)
            if f3_required > 0:
                total_vol_needed = z3_final_target / f3_required
                res_final = (total_vol_needed * f1_fixed, total_vol_needed * (1 - f1_fixed - f3_required), z3_final_target)
            
        elif strategy == "Standard 80% Z1 (Volume Fisso)":
            target_vol = st.number_input("Volume Totale Target (min)", value=300)
            f1 = 0.80
            f3 = solve_for_f3_standard(f1, target_pi)
            f2 = 1 - f1 - f3
            res_final = (target_vol * f1, target_vol * f2, target_vol * f3)
            
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
            st.subheader("Da Eseguire:")
            st.warning(f"Z1: {int(r1)} min")
            st.info(f"Z2: {int(r2)} min")
            st.success(f"Z3: {int(r3)} min")
            st.write(f"**Totale Finale:** {int(sum(res_final))} min")

    with col_plan_plot:
        if res_final:
            total_final = sum(res_final)
            if total_final > 0:
                f1_fin = res_final[0] / total_final
                f3_fin = res_final[2] / total_final
                st.pyplot(plot_pi_chart(f1_fin, f3_fin, label="Target Finale", color='blue'))
