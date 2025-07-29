import streamlit as st
import pandas as pd
from itertools import combinations
import random
import io
import base64 # Importato per la gestione dei download senza reset

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
    if fixed_numbers is None:
        fixed_numbers = []

    if not isinstance(source_numbers, list) or not all(isinstance(n, int) for n in source_numbers):
        raise ValueError("La lista 'source_numbers' deve contenere solo numeri interi.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("La lunghezza 'k' deve essere un numero intero positivo.")
    if not isinstance(fixed_numbers, list) or not all(isinstance(n, int) for n in fixed_numbers):
        raise ValueError("La lista 'fixed_numbers' deve contenere solo numeri interi.")
    if len(fixed_numbers) > k:
        raise ValueError("Il numero di numeri fissi non può essere maggiore di k.")
    for f_num in fixed_numbers:
        if f_num not in source_numbers:
            raise ValueError(f"Il numero fisso {f_num} non è presente nella lista sorgente.")

    remaining_numbers = [num for num in source_numbers if num not in fixed_numbers]
    elements_to_pick = k - len(fixed_numbers)

    if elements_to_pick == 0:
        return [tuple(sorted(fixed_numbers))]

    if elements_to_pick > len(remaining_numbers):
        raise ValueError("Numeri insufficienti per completare la combinazione.")

    generated_combinations_parts = combinations(remaining_numbers, elements_to_pick)

    final_combinations = []
    for combo_part in generated_combinations_parts:
        full_combo = list(combo_part) + fixed_numbers
        final_combinations.append(tuple(sorted(full_combo)))

    return sorted(list(set(final_combinations)))

def reduce_combinations_with_guarantee_greedy(full_combinations, guarantee_size, max_combinations=None):
    required_subsets = set()
    
    # Progress bar per Streamlit
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 Calcolo sottoinsiemi da garantire...")
        progress_bar = st.progress(0)
        
        for i, combo in enumerate(full_combinations):
            for subset in combinations(combo, guarantee_size):
                required_subsets.add(tuple(sorted(subset)))
            if i % max(1, len(full_combinations) // 20) == 0:  # Aggiorna ogni 5%
                progress_bar.progress((i + 1) / len(full_combinations))
    
    covered_subsets = set()
    selected_combinations = []
    combos_remaining = set(full_combinations)

    with progress_container:
        st.info("🎯 Selezione combinazioni con algoritmo greedy...")
        progress_bar2 = st.progress(0)
        
        iteration = 0
        while covered_subsets != required_subsets:
            best_combo = None
            best_new_coverage = 0

            for combo in combos_remaining:
                new_subsets = set(combinations(combo, guarantee_size))
                uncovered = new_subsets - covered_subsets
                if len(uncovered) > best_new_coverage:
                    best_new_coverage = len(uncovered)
                    best_combo = combo

            if best_combo is None:
                st.warning("⚠ Impossibile migliorare la copertura, uscita anticipata.")
                break

            selected_combinations.append(best_combo)
            covered_subsets.update(set(combinations(best_combo, guarantee_size)))
            combos_remaining.remove(best_combo)
            
            iteration += 1
            if iteration % 5 == 0:
                progress = min(len(covered_subsets) / len(required_subsets), 1.0)
                progress_bar2.progress(progress)

            if max_combinations is not None and len(selected_combinations) >= max_combinations:
                st.info(f"🔒 Raggiunto limite massimo di combinazioni: {max_combinations}")
                break
    
    # Pulisce i progress bar
    progress_container.empty()
    return selected_combinations

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
st.markdown("---")

# Sidebar per i parametri
st.sidebar.header("⚙ Configurazione Parametri")
st.sidebar.markdown("Configura i parametri per la generazione delle combinazioni:")

# Parametri principali
# numero_di_numeri = st.sidebar.slider(
#     "📊 Numeri totali da generare", 
#     min_value=5, max_value=50, value=10, # Max_value verrà aggiornato dinamicamente
#     help="Quanti numeri casuali generare dall'intervallo specificato. Seleziona un numero pari ai 'Numeri fissi' per usare solo quelli."
# )

col_range1, col_range2 = st.sidebar.columns(2)
with col_range1:
    range_min = st.number_input("Min", min_value=1, max_value=50, value=1)
with col_range2:
    range_max = st.number_input("Max", min_value=10, max_value=100, value=40)

# Aggiorna il max_value del slider numero_di_numeri
# Questo va fatto dopo che range_min e range_max sono definiti
max_numbers_in_range = range_max - range_min + 1
numero_di_numeri = st.sidebar.slider(
    "📊 Numeri totali da generare", 
    min_value=5, max_value=max_numbers_in_range, value=min(10, max_numbers_in_range), # Ensure value doesn't exceed new max
    key="num_gen_slider", # Aggiunto una key per evitare problemi di Streamlit
    help="Quanti numeri casuali generare dall'intervallo specificato. Seleziona un numero pari ai 'Numeri fissi' per usare solo quelli."
)


k_combination_length = st.sidebar.slider(
    "🔢 Lunghezza combinazione", 
    min_value=3, max_value=10, value=5,
    help="Quanti numeri per ogni combinazione"
)

garanzia = st.sidebar.slider(
    "🎯 Garanzia", 
    min_value=2, max_value=min(8, k_combination_length-1), value=3,
    help="Quanti numeri devono essere garantiti in comune"
)

# Parametri avanzati
with st.sidebar.expander("⚙ Parametri Avanzati"):
    numeri_fissi_input = st.text_input(
        "📌 Numeri da includere (separati da virgola)", 
        "",
        help="Numeri che DEVONO essere inclusi nel set di numeri sorgente. Se il numero di questi numeri fissi è pari a 'Numeri totali da generare', allora verranno usati SOLO questi numeri come sorgente."
    )
    
    max_combinazioni_input = st.text_input(
        "🔒 Max combinazioni (vuoto = nessun limite)", 
        "",
        help="Limite massimo di combinazioni da generare"
    )
    
    seed_random = st.number_input(
        "🎲 Seed per casualità (0 = casuale)", 
        min_value=0, max_value=9999, value=0,
        help="Usa lo stesso seed per ottenere risultati riproducibili"
    )

    # NUOVA OPZIONE: Filtro numeri pari/dispari
    tipo_numeri_generazione = st.radio(
        "Tipo di numeri da generare",
        ("Tutti", "Solo Pari", "Solo Dispari"),
        index=0,
        help="Scegli se generare numeri pari, dispari o entrambi nel range specificato."
    )

# Elaborazione input
fixed_numbers_to_include = []
if numeri_fissi_input.strip():
    try:
        fixed_numbers_to_include = [int(x.strip()) for x in numeri_fissi_input.split(',')]
        # Filtra i numeri fissi che sono fuori dal range definito
        fixed_numbers_to_include = [x for x in fixed_numbers_to_include if range_min <= x <= range_max]
    except ValueError:
        st.sidebar.error("❌ Formato numeri da includere non valido")
        fixed_numbers_to_include = [] # Svuota per evitare errori successivi

max_combinations = None
if max_combinazioni_input.strip():
    try:
        max_combinations = int(max_combinazioni_input)
        if max_combinations <= 0:
            max_combinations = None
    except ValueError:
        st.sidebar.error("❌ Formato max combinazioni non valido")

# Set seed se specificato
if seed_random > 0:
    random.seed(seed_random)

# Validazioni
validazione_ok = True
errori = []

if range_max <= range_min:
    errori.append("Il range massimo deve essere maggiore del range minimo")
    validazione_ok = False

# Calcolo dei numeri disponibili in base al tipo selezionato
available_numbers_in_range_filtered = []
for num in range(range_min, range_max + 1):
    if tipo_numeri_generazione == "Solo Pari" and num % 2 != 0:
        continue
    if tipo_numeri_generazione == "Solo Dispari" and num % 2 == 0:
        continue
    available_numbers_in_range_filtered.append(num)

# Rivedi la validazione per i numeri totali da generare
if numero_di_numeri > len(available_numbers_in_range_filtered):
    errori.append(f"Troppi numeri richiesti ({numero_di_numeri}) per l'intervallo specificato e il filtro '{tipo_numeri_generazione}'. Numeri disponibili: {len(available_numbers_in_range_filtered)}")
    validazione_ok = False

if garanzia >= k_combination_length:
    errori.append("La garanzia deve essere minore della lunghezza della combinazione")
    validazione_ok = False

if len(fixed_numbers_to_include) > k_combination_length:
    errori.append("Troppi numeri da includere per la lunghezza della combinazione")
    validazione_ok = False

# Valida che i numeri fissi siano compatibili con il tipo di numeri generato
if tipo_numeri_generazione == "Solo Pari":
    for f_num in fixed_numbers_to_include:
        if f_num % 2 != 0:
            errori.append(f"Il numero da includere {f_num} è dispari ma hai selezionato 'Solo Pari'.")
            validazione_ok = False
elif tipo_numeri_generazione == "Solo Dispari":
    for f_num in fixed_numbers_to_include:
        if f_num % 2 == 0:
            errori.append(f"Il numero da includere {f_num} è pari ma hai selezionato 'Solo Dispari'.")
            validazione_ok = False

# Validazione: Se numeri fissi sono più del numero_di_numeri, errore
if len(fixed_numbers_to_include) > numero_di_numeri:
    errori.append(f"Il numero di 'Numeri da includere' ({len(fixed_numbers_to_include)}) non può essere maggiore di 'Numeri totali da generare' ({numero_di_numeri}).")
    validazione_ok = False

# Validazione: Tutti i numeri fissi devono essere nel range filtrato
for f_num in fixed_numbers_to_include:
    if f_num not in available_numbers_in_range_filtered:
        errori.append(f"Il numero da includere {f_num} non è valido con il range e/o il filtro pari/dispari selezionato.")
        validazione_ok = False


# Mostra errori
if errori:
    for errore in errori:
        st.error(f"❌ {errore}")
    st.info("💡 Correggi gli errori per abilitare la generazione.")

# Layout principale
col1, col2 = st.columns([2, 1])

with col2:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.subheader("📋 Riepilogo Configurazione")
    st.write(f"🎲 *Numeri totali da generare:* {numero_di_numeri}")
    st.write(f"📊 *Range:* {range_min} - {range_max}")
    st.write(f"🔢 *Lunghezza combinazione:* {k_combination_length}")
    st.write(f"📌 *Numeri da includere:* {fixed_numbers_to_include if fixed_numbers_to_include else 'Nessuno'}")
    st.write(f"🎯 *Garanzia:* {garanzia}")
    st.write(f"🔒 *Max combinazioni:* {max_combinations if max_combinations else 'Nessun limite'}")
    st.write(f"🔄 *Tipo numeri:* {tipo_numeri_generazione}") # Nuovo riepilogo
    if seed_random > 0:
        st.write(f"🎲 *Seed:* {seed_random}")
    st.markdown('</div>', unsafe_allow_html=True)

with col1:
    # Pulsante principale
    generate_button = st.button(
        "🚀 Genera Combinazioni", 
        type="primary", 
        disabled=not validazione_ok,
        use_container_width=True
    )
    
    if generate_button and validazione_ok:
        try:
            start_time = st.empty()
            start_time.info("🔄 Avvio generazione...")
            
            # Generazione numeri sorgente
            # Modifica qui per includere il filtro pari/dispari
            if tipo_numeri_generazione == "Tutti":
                potential_numbers = list(range(range_min, range_max + 1))
            elif tipo_numeri_generazione == "Solo Pari":
                potential_numbers = [n for n in range(range_min, range_max + 1) if n % 2 == 0]
            else: # Solo Dispari
                potential_numbers = [n for n in range(range_min, range_max + 1) if n % 2 != 0]

            # Rimuovi i numeri fissi da potential_numbers prima del campionamento casuale
            # Così eviti di campionarli due volte o di avere duplicati in source_numbers_list
            # e ti assicuri che il campionamento casuale prenda solo i "restanti"
            temp_potential_numbers = [n for n in potential_numbers if n not in fixed_numbers_to_include]
            
            # Determina quanti numeri casuali dobbiamo ancora pescare
            numbers_to_sample = numero_di_numeri - len(fixed_numbers_to_include)

            if numbers_to_sample < 0: # Questo caso dovrebbe essere già catturato dalle validazioni
                st.error("Errore interno: numeri da campionare negativi. Controllare le impostazioni dei numeri fissi.")
                start_time.empty()
                st.stop()

            if numbers_to_sample > len(temp_potential_numbers):
                st.error(f"❌ Impossibile generare {numero_di_numeri} numeri. Hai specificato {len(fixed_numbers_to_include)} numeri da includere. Non ci sono abbastanza numeri casuali disponibili ({len(temp_potential_numbers)}) nel range e con i filtri per completare i restanti {numbers_to_sample} numeri.")
                start_time.empty()
                st.stop() # Ferma l'esecuzione se non ci sono abbastanza numeri

            sampled_numbers = random.sample(temp_potential_numbers, numbers_to_sample)
            source_numbers_list = sorted(list(set(fixed_numbers_to_include + sampled_numbers)))


            st.success(f"🎲 *Numeri sorgente generati ({tipo_numeri_generazione.lower()}):* {source_numbers_list}")
            
            # Generazione combinazioni
            with st.spinner("Generazione combinazioni iniziali..."):
                full_combinations = generate_combinations_with_fixed(
                    source_numbers_list,
                    k_combination_length,
                    fixed_numbers_to_include
                )
            st.success(f"✅ *Combinazioni generate:* {len(full_combinations):,}")
            
            # Riduzione con garanzia
            if len(full_combinations) > 0:
                final_combinations = reduce_combinations_with_guarantee_greedy(
                    full_combinations, garanzia, max_combinations
                )
                st.success(f"🎯 *Combinazioni finali:* {len(final_combinations):,}")
                
                # Creazione DataFrame
                df_output = pd.DataFrame(
                    final_combinations, 
                    columns=[f'N{i+1}' for i in range(k_combination_length)]
                )
                
                # Statistiche per l'intestazione
                source_str = ','.join(str(n) for n in source_numbers_list)
                if len(full_combinations) > 0: # Evita divisione per zero
                    riduzione_perc = (1 - len(final_combinations)/len(full_combinations)) * 100
                else:
                    riduzione_perc = 0.0

                header_info = [
                    f"Generazione Combinazioni - Riepilogo",
                    f"Data Generazione: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Numeri totali da generare: {numero_di_numeri}",
                    f"Range: {range_min}-{range_max}",
                    f"Lunghezza Combinazione: {k_combination_length}",
                    f"Numeri da includere: {fixed_numbers_to_include if fixed_numbers_to_include else 'Nessuno'}",
                    f"Garanzia: {garanzia}",
                    f"Max Combinazioni: {max_combinations if max_combinations else 'Nessun limite'}",
                    f"Tipo Numeri: {tipo_numeri_generazione}",
                    f"Seed: {seed_random if seed_random > 0 else 'Casuale'}",
                    f"Numeri sorgente generati: {source_str}",
                    f"Combinazioni iniziali generate: {len(full_combinations):,}",
                    f"Combinazioni finali: {len(final_combinations):,}",
                    f"Riduzione: {riduzione_perc:.1f}%",
                    "", # Riga vuota per separazione
                    "Combinazioni:"
                ]
                
                # Visualizzazione risultati
                st.markdown("---")
                st.subheader("📊 Risultati Generati")
                
                # Statistiche
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("🎯 Combinazioni", len(final_combinations))
                with col_stat2:
                    st.metric("📉 Riduzione", f"{riduzione_perc:.1f}%")
                with col_stat3:
                    st.metric("🔢 Garanzia", garanzia)
                
                # Tabella risultati
                st.dataframe(df_output, use_container_width=True, height=400)
                
                # Generazione file CSV con intestazione
                csv_buffer = io.StringIO()
                for line in header_info:
                    csv_buffer.write(line + "\n") # Scrive ogni riga dell'header
                df_output.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                filename = f"combinazioni_G{garanzia}_C{len(final_combinations)}_L{k_combination_length}.csv"
                
                col_download1, col_download2 = st.columns(2)
                with col_download1:
                    # Usiamo il link di download per non resettare la pagina
                    st.markdown(get_download_link(csv_data, filename, "text/csv", "📁 Scarica CSV"), unsafe_allow_html=True)
                
                with col_download2:
                    # Genera anche un Excel con intestazione
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        # Scrivi l'intestazione come un DataFrame temporaneo
                        header_df = pd.DataFrame(header_info)
                        header_df.to_excel(writer, sheet_name='Riepilogo e Combinazioni', index=False, header=False)
                        
                        # Inizia il DataFrame delle combinazioni dopo l'header
                        # Calcola la riga di partenza per il dataframe dei risultati
                        startrow = len(header_info) 
                        df_output.to_excel(writer, sheet_name='Riepilogo e Combinazioni', index=False, startrow=startrow)
                    excel_data = excel_buffer.getvalue()
                    
                    filename_excel = filename.replace('.csv', '.xlsx')
                    # Usiamo il link di download per non resettare la pagina
                    st.markdown(get_excel_download_link(excel_data, filename_excel, "📊 Scarica Excel"), unsafe_allow_html=True)
                
                start_time.empty()
                
            else:
                st.error("❌ Nessuna combinazione generata con i parametri specificati")
                
        except Exception as e:
            st.error(f"❌ *Errore durante la generazione:* {str(e)}")
            st.info("💡 Prova a modificare i parametri e riprova")

# Footer informativo
st.markdown("---")
with st.expander("📖 Come Funziona l'Algoritmo"):
    st.markdown("""
    *🎯 Algoritmo Greedy con Garanzia:*
    
    1. *Generazione*: Crea tutte le combinazioni possibili dai numeri sorgente
    2. *Analisi*: Calcola tutti i sottoinsiemi di dimensione 'garanzia' da coprire
    3. *Ottimizzazione*: Seleziona le combinazioni che coprono il maggior numero di sottoinsiemi non ancora coperti
    4. *Risultato*: Ottiene il minor numero di combinazioni che garantiscono la copertura completa
    
    *💡 Esempio:* Con garanzia 3, ogni terzina possibile sarà presente in almeno una delle combinazioni finali.
    """)

with st.expander("❓ Aiuto e Suggerimenti"):
    st.markdown("""
    *🔧 Parametri Principali:*
    - *Numeri totali da generare*: Quanti numeri generare (più numeri = più combinazioni). **Non può superare i numeri disponibili nel range selezionato.**
    - *Range*: Intervallo da cui pescare i numeri.
    - *Lunghezza combinazione*: Quanti numeri per ogni combinazione.
    - *Garanzia*: Dimensione dei sottoinsiemi da garantire.
    
    *💡 Suggerimenti:*
    - Inizia con parametri piccoli per testare.
    - La garanzia deve essere minore della lunghezza combinazione.
    - **Numeri da includere (precedentemente "Numeri fissi")**: Inserisci i numeri che DEVONO apparire nel set di numeri sorgente. Se il numero di elementi che inserisci qui è uguale a 'Numeri totali da generare', allora il programma userà SOLO questi numeri come sorgente, senza generarne altri casualmente.
    - Il seed ti permette di riprodurre gli stessi risultati.
    - *Tipo di numeri da generare*: Puoi scegliere di generare solo numeri pari, solo numeri dispari, o tutti i numeri nel range.
    
    *⚡ Performance:*
    - Combinazioni > 1000: potrebbero richiedere tempo.
    - Usa 'Max combinazioni' per limitare il risultato.
    """)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
    "🚀 Powered by Streamlit | 🎯 Algoritmo Greedy Ottimizzato"
    "</div>", 
    unsafe_allow_html=True
)
