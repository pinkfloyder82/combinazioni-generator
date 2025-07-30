import streamlit as st
import pandas as pd
from itertools import combinations
import random
import io
import base64

# Configurazione pagina
st.set_page_config(
    page_title="🎯 Generatore Combinazioni",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def generate_combinations_with_fixed(source_numbers, k, fixed_numbers=None):
    """
    Genera combinazioni di k numeri da source_numbers, assicurando che
    i numeri in fixed_numbers siano inclusi in ogni combinazione.

    Args:
        source_numbers (list): La lista di numeri da cui generare le combinazioni.
                                Questo è il pool totale di numeri del tuo sistema.
        k (int): La lunghezza desiderata di ogni combinazione (es. 5 numeri).
        fixed_numbers (list, optional): Una lista di numeri che DEVONO essere presenti in OGNI combinazione finale.
                                        Default a None (nessun numero fisso richiesto in ogni combinazione).

    Returns:
        list: Una lista di tuple, dove ogni tupla è una combinazione ordinata di k numeri.
              Ogni tupla conterrà i fixed_numbers e gli elementi selezionati.
    """
    if fixed_numbers is None:
        fixed_numbers = []

    # Validazioni iniziali dei tipi di input
    if not isinstance(source_numbers, list) or not all(isinstance(n, int) for n in source_numbers):
        raise ValueError("La lista 'source_numbers' deve contenere solo numeri interi.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("La lunghezza 'k' deve essere un numero intero positivo.")
    if not isinstance(fixed_numbers, list) or not all(isinstance(n, int) for n in fixed_numbers):
        raise ValueError("La lista 'fixed_numbers' (numeri da includere) deve contenere solo numeri interi.")

    # Nuova validazione: I numeri fissi devono essere presenti nel pool di source_numbers
    for f_num in fixed_numbers:
        if f_num not in source_numbers:
            raise ValueError(f"Il numero fisso {f_num} non è presente nella lista dei numeri sorgente generata ({source_numbers}).")

    # Validazione cruciale per la logica di generazione delle combinazioni
    if len(fixed_numbers) > k:
        raise ValueError(f"Il numero di numeri fissi ({len(fixed_numbers)}) non può essere maggiore della lunghezza desiderata della singola combinazione ({k}).")

    # Prepara la lista di numeri da cui selezionare gli elementi "non fissi"
    # Sono tutti i numeri sorgente meno quelli che sono già fissi
    remaining_numbers_for_selection = [num for num in source_numbers if num not in fixed_numbers]

    # Quanti elementi dobbiamo ancora scegliere per completare la combinazione di lunghezza k
    elements_to_pick = k - len(fixed_numbers)

    # Caso speciale: Se tutti gli elementi della combinazione sono numeri fissi
    if elements_to_pick == 0:
        # Assicurati che i numeri fissi siano effettivamente di lunghezza k
        if len(fixed_numbers) == k:
            return [tuple(sorted(fixed_numbers))]
        else:
            # Questo caso dovrebbe essere catturato dalla validazione len(fixed_numbers) > k
            raise ValueError("Errore interno: elements_to_pick è 0 ma len(fixed_numbers) != k.")

    # Validazione: Assicurati che ci siano abbastanza numeri rimanenti per formare la combinazione
    if elements_to_pick > len(remaining_numbers_for_selection):
        raise ValueError(f"Numeri insufficienti disponibili per completare le combinazioni. "
                         f"Hai bisogno di {elements_to_pick} numeri aggiuntivi, ma ne hai solo {len(remaining_numbers_for_selection)} disponibili dopo aver escluso i fissi dal pool sorgente.")

    # Genera le combinazioni dalla lista dei numeri rimanenti
    generated_combinations_parts = combinations(remaining_numbers_for_selection, elements_to_pick)

    final_combinations = []
    for combo_part in generated_combinations_parts:
        # Unisce la parte generata con i numeri fissi e ordina per garantire unicità e consistenza
        full_combo = list(combo_part) + fixed_numbers
        final_combinations.append(tuple(sorted(full_combo)))

    # Converte in un set per eliminare eventuali duplicati (anche se `combinations` e `sorted(tuple)` dovrebbero evitarli)
    # e poi torna a una lista di tuple ordinate.
    return sorted(list(set(final_combinations)))


def reduce_combinations_with_guarantee_greedy(full_combinations, guarantee_size, max_combinations=None):
    if not full_combinations:
        st.warning("Nessuna combinazione da ridurre. Assicurati che le combinazioni iniziali siano state generate.")
        return []

    # Validazione: la dimensione della garanzia deve essere sensata
    if guarantee_size <= 0:
        st.error("Errore: La dimensione della garanzia deve essere un numero positivo.")
        return []
    if guarantee_size > len(full_combinations[0]):
        st.error("Errore: La dimensione della garanzia non può essere maggiore della lunghezza della combinazione stessa.")
        return []

    # Caso speciale: se guarantee_size è uguale alla lunghezza della combinazione
    # L'algoritmo greedy in questo caso non ridurrebbe, perché ogni combinazione è un "target" a sé.
    # Applichiamo solo il limite max_combinations, se presente.
    if guarantee_size == len(full_combinations[0]):
        st.info("Garanzia impostata alla lunghezza della combinazione. Non verrà applicata ulteriore riduzione oltre il limite massimo di combinazioni, se specificato.")
        if max_combinations is not None and len(full_combinations) > max_combinations:
            # Prendo un campione casuale se il limite è inferiore alle combinazioni totali
            return sorted(random.sample(full_combinations, max_combinations))
        else:
            return full_combinations # Ritorna tutte le combinazioni se non c'è limite o è inferiore


    required_subsets = set()
    
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 Calcolo sottoinsiemi da garantire (target sets)...")
        progress_bar = st.progress(0)
        
        num_full_combos = len(full_combinations)
        update_interval = max(1, num_full_combos // 100) # Aggiorna almeno 100 volte
        if num_full_combos < 1000: # Per dataset piccoli, aggiorna più frequentemente
            update_interval = 1

        for i, combo in enumerate(full_combinations):
            for subset in combinations(combo, guarantee_size):
                required_subsets.add(tuple(sorted(subset))) # Garantisce unicità e ordine
            if (i + 1) % update_interval == 0 or (i + 1) == num_full_combos:
                progress_bar.progress((i + 1) / num_full_combos)
        
        progress_bar.empty() # Pulisce la progress bar per questa fase
        
    covered_subsets = set()
    selected_combinations = []
    combos_remaining = set(full_combinations) # Lavoriamo su un set per rimozioni efficienti

    with progress_container:
        st.info(f"🎯 Selezione combinazioni con algoritmo greedy per coprire {len(required_subsets):,} sottoinsiemi...")
        progress_bar2 = st.progress(0)
        
        iteration = 0
        while covered_subsets != required_subsets and combos_remaining:
            best_combo = None
            best_new_coverage = -1

            # Ottimizzazione: Per dataset molto grandi, non iterare su tutti i remaining_combos
            # Ma per questo algoritmo greedy, l'iterazione completa è spesso necessaria per trovare il "migliore"
            # Se fosse troppo lento, si potrebbe campionare un sottoinsieme dei remaining_combos.
            for combo in combos_remaining:
                new_subsets = set(combinations(combo, guarantee_size))
                uncovered = new_subsets - covered_subsets
                if len(uncovered) > best_new_coverage:
                    best_new_coverage = len(uncovered)
                    best_combo = combo
            
            if best_new_coverage == 0:
                st.warning("⚠ Nessuna combinazione rimanente può coprire nuovi sottoinsiemi. Uscita anticipata dall'algoritmo greedy.")
                break

            if best_combo is None:
                st.warning("⚠ Algoritmo greedy non ha trovato la combinazione migliore. Uscita anticipata.")
                break

            selected_combinations.append(best_combo)
            covered_subsets.update(set(combinations(best_combo, guarantee_size)))
            combos_remaining.remove(best_combo)
            
            iteration += 1
            if len(required_subsets) > 0:
                progress = min(len(covered_subsets) / len(required_subsets), 1.0)
                progress_bar2.progress(progress)
            
            if max_combinations is not None and len(selected_combinations) >= max_combinations:
                st.info(f"🔒 Raggiunto limite massimo di combinazioni: {max_combinations}")
                break
    
    progress_container.empty()
    return sorted(selected_combinations)

# Funzione per generare il link di download (per non resettare la pagina)
def get_download_link(data, filename, mime_type, link_text):
    b64 = base64.b64encode(data.encode()).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{link_text}</a>'

def get_excel_download_link(data, filename, link_text):
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{link_text}</a>'


# Header principale
st.markdown('<h1 class="main-header">🎯 Generatore di Combinazioni con Garanzia</h1>', unsafe_allow_html=True)
st.markdown("*Crea combinazioni ottimizzate con algoritmo greedy e garanzia personalizzabile*")
st.markdown("*Utilizzalo per tentare la sorte con le tue lotterie preferite*")
st.markdown(
    """
    <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
        Supporta lo sviluppo: <a href="https://paypal.me/peppino82" target="_blank">☕ Offrimi un caffè su PayPal</a>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# Sidebar per i parametri
st.sidebar.header("⚙ Configurazione Parametri")
st.sidebar.markdown("Configura i parametri per la generazione delle combinazioni:")

col_range1, col_range2 = st.sidebar.columns(2)
with col_range1:
    range_min = st.number_input("Min", min_value=1, max_value=50, value=1, key="range_min")
with col_range2:
    range_max = st.number_input("Max", min_value=10, max_value=100, value=40, key="range_max")

# NUOVA OPZIONE: Filtro numeri pari/dispari (prima del slider numero_di_numeri)
tipo_numeri_generazione = st.sidebar.radio(
    "Tipo di numeri da generare",
    ("Tutti", "Solo Pari", "Solo Dispari"),
    index=0,
    help="Scegli se generare numeri pari, dispari o entrambi nel range specificato."
)

# Filtra preliminarmente i numeri disponibili nel range in base al tipo selezionato
potential_numbers_filtered_by_type = []
for num in range(range_min, range_max + 1):
    if tipo_numeri_generazione == "Solo Pari" and num % 2 != 0:
        continue
    if tipo_numeri_generazione == "Solo Dispari" and num % 2 == 0:
        continue
    potential_numbers_filtered_by_type.append(num)

# Calcola il massimo valore possibile per il numero_di_numeri slider
# che è il numero di elementi nel range filtrato
max_possible_system_numbers = len(potential_numbers_filtered_by_type)

numero_di_numeri = st.sidebar.slider(
    "📊 Numeri totali per il sistema",
    min_value=5, max_value=max_possible_system_numbers, value=min(15, max_possible_system_numbers
