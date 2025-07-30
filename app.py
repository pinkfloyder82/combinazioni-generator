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
    if fixed_numbers is None:
        fixed_numbers = []

    if not isinstance(source_numbers, list) or not all(isinstance(n, int) for n in source_numbers):
        raise ValueError("La lista 'source_numbers' deve contenere solo numeri interi.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("La lunghezza 'k' deve essere un numero intero positivo.")
    if not isinstance(fixed_numbers, list) or not all(isinstance(n, int) for n in fixed_numbers):
        raise ValueError("La lista 'fixed_numbers' deve contenere solo numeri interi.")

    # Nuova validazione spostata qui: se i numeri fissi sono più lunghi di k, è un problema per la combinazione singola.
    if len(fixed_numbers) > k:
        raise ValueError("Il numero di numeri fissi non può essere maggiore della lunghezza della singola combinazione (k).")

    # Controlliamo che tutti i numeri fissi siano presenti nella source_numbers
    for f_num in fixed_numbers:
        if f_num not in source_numbers:
            raise ValueError(f"Il numero fisso {f_num} non è presente nella lista dei numeri sorgente fornita per la generazione.")

    remaining_numbers = [num for num in source_numbers if num not in fixed_numbers]
    elements_to_pick = k - len(fixed_numbers)

    if elements_to_pick == 0:
        return [tuple(sorted(fixed_numbers))]

    if elements_to_pick > len(remaining_numbers):
        raise ValueError("Numeri insufficienti nella lista sorgente (dopo aver escluso i numeri fissi) per completare la combinazione della lunghezza richiesta (k).")

    generated_combinations_parts = combinations(remaining_numbers, elements_to_pick)

    final_combinations = []
    for combo_part in generated_combinations_parts:
        full_combo = list(combo_part) + fixed_numbers
        final_combinations.append(tuple(sorted(full_combo)))

    return sorted(list(set(final_combinations)))

def reduce_combinations_with_guarantee_greedy(full_combinations, guarantee_size, max_combinations=None):
    if not full_combinations:
        st.warning("Nessuna combinazione da ridurre. Assicurati che le combinazioni iniziali siano state generate.")
        return []

    # Se guarantee_size è uguale alla lunghezza della combinazione, ogni combinazione è un suo stesso subset richiesto.
    # Questo algoritmo è più efficiente se si evita di generare subset che sono la combinazione stessa.
    # Se guarantee_size = k_combination_length, la garanzia è che ogni combinazione debba essere presente.
    # In quel caso, la riduzione non ha senso, a meno di limitare max_combinations.
    if guarantee_size > len(full_combinations[0]):
        st.error("Errore: La dimensione della garanzia non può essere maggiore della lunghezza della combinazione stessa.")
        return []
    if guarantee_size == len(full_combinations[0]):
        # Se la garanzia è sulla combinazione intera, non c'è riduzione da fare se non per max_combinations
        st.info("Garanzia impostata alla lunghezza della combinazione. Non verrà applicata ulteriore riduzione oltre il limite massimo di combinazioni, se specificato.")
        if max_combinations is not None and len(full_combinations) > max_combinations:
            return sorted(random.sample(full_combinations, max_combinations)) # Prendo un campione casuale se c'è limite
        else:
            return full_combinations # Ritorna tutte le combinazioni se non c'è limite o è inferiore

    required_subsets = set()
    
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 Calcolo sottoinsiemi da garantire...")
        progress_bar = st.progress(0)
        
        # Stima il numero di iterazioni per la progress bar per evitare aggiornamenti troppo frequenti
        # e per gestire grandi numeri di combinazioni
        num_full_combos = len(full_combinations)
        update_interval = max(1, num_full_combos // 100) # Aggiorna almeno 100 volte

        for i, combo in enumerate(full_combinations):
            for subset in combinations(combo, guarantee_size):
                required_subsets.add(tuple(sorted(subset)))
            if (i + 1) % update_interval == 0 or (i + 1) == num_full_combos:
                progress_bar.progress((i + 1) / num_full_combos)
        
        # Una volta calcolati tutti i sottoinsiemi richiesti, azzera la progress bar per la fase successiva
        progress_bar.empty()
        
    covered_subsets = set()
    selected_combinations = []
    combos_remaining = set(full_combinations) # Lavoriamo su un set per rimozioni efficienti

    with progress_container:
        st.info(f"🎯 Selezione combinazioni con algoritmo greedy per coprire {len(required_subsets):,} sottoinsiemi...")
        progress_bar2 = st.progress(0)
        
        iteration = 0
        while covered_subsets != required_subsets and combos_remaining: # Aggiunto check combos_remaining
            best_combo = None
            best_new_coverage = -1 # Inizia da -1, così anche 0 nuovi subsets è un miglioramento

            # Per migliorare le performance su grandi dataset, potremmo non iterare su tutti i combos_remaining ad ogni step
            # Ma per ora, manteniamo l'iterazione completa.
            for combo in combos_remaining:
                new_subsets = set(combinations(combo, guarantee_size))
                uncovered = new_subsets - covered_subsets
                if len(uncovered) > best_new_coverage:
                    best_new_coverage = len(uncovered)
                    best_combo = combo
            
            if best_new_coverage == 0: # Nessuna combo rimanente può coprire nuovi subsets
                st.warning("⚠ Impossibile migliorare la copertura con le combinazioni rimanenti. Uscita anticipata.")
                break

            if best_combo is None:
                st.warning("⚠ Algoritmo greedy non ha trovato la combinazione migliore. Uscita anticipata.")
                break

            selected_combinations.append(best_combo)
            covered_subsets.update(set(combinations(best_combo, guarantee_size)))
            combos_remaining.remove(best_combo) # Rimuovi la combinazione selezionata
            
            iteration += 1
            # Aggiorna la progress bar in base alla percentuale di copertura raggiunta
            if len(required_subsets) > 0:
                progress = min(len(covered_subsets) / len(required_subsets), 1.0)
                progress_bar2.progress(progress)
            
            if max_combinations is not None and len(selected_combinations) >= max_combinations:
                st.info(f"🔒 Raggiunto limite massimo di combinazioni: {max_combinations}")
                break
    
    # Pulisce i progress bar
    progress_container.empty()
    return sorted(selected_combinations) # Ordina le combinazioni finali per consistenza

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
    range_min = st.number_input("Min", min_value=1, max_value=50, value=1)
with col_range2:
    range_max = st.number_input("Max", min_value=10, max_value=100, value=40)

max_numbers_in_range = range_max - range_min + 1

# Calcolo preliminare dei numeri disponibili con il filtro pari/dispari
preliminary_potential_numbers = []
for num in range(range_min, range_max + 1):
    preliminary_potential_numbers.append(num)

# NUOVA OPZIONE: Filtro numeri pari/dispari (prima del slider numero_di_numeri)
tipo_numeri_generazione = st.sidebar.radio(
    "Tipo di numeri da generare",
    ("Tutti", "Solo Pari", "Solo Dispari"),
    index=0,
    help="Scegli se generare numeri pari, dispari o entrambi nel range specificato."
)

# Filtra preliminarmente i numeri disponibili in base al tipo selezionato
filtered_for_slider_numbers = []
for num in preliminary_potential_numbers:
    if tipo_numeri_generazione == "Solo Pari" and num % 2 != 0:
        continue
    if tipo_numeri_generazione == "Solo Dispari" and num % 2 == 0:
        continue
    filtered_for_slider_numbers.append(num)

# Aggiorna il max_value del slider numero_di_numeri
numero_di_numeri = st.sidebar.slider(
    "📊 Numeri totali per il sistema",
    min_value=5, max_value=len(filtered_for_slider_numbers), value=min(10, len(filtered_for_slider_numbers)),
    key="num_gen_slider",
    help="Questo è il numero totale di numeri da cui verranno generate le combinazioni. "
         "Se i 'Numeri da includere' (fissi) sono pari a questo valore, verranno usati SOLO quelli come base per il sistema."
)

k_combination_length = st.sidebar.slider(
    "🔢 Lunghezza combinazione",
    min_value=3, max_value=10, value=5,
    help="Quanti numeri per ogni combinazione finale"
)

garanzia = st.sidebar.slider(
    "🎯 Garanzia",
    min_value=2, max_value=min(k_combination_length - 1, k_combination_length), # Max guarantee cannot be k or more
    value=min(3, k_combination_length -1), # Ensure default value is valid
    help="Quanti numeri devono essere garantiti in comune. Deve essere inferiore della lunghezza combinazione."
)

# Parametri avanzati
with st.sidebar.expander("⚙ Parametri Avanzati"):
    numeri_fissi_input = st.text_input(
        "📌 Numeri da includere (separati da virgola)",
        "",
        help=f"Numeri che DEVONO essere inclusi nel pool di {numero_di_numeri} numeri base. "
             "Verranno usati per completare il set di base, e i rimanenti verranno scelti casualmente. "
             "Se il loro numero è pari a 'Numeri totali per il sistema', verranno usati SOLO questi numeri."
    )
    
    max_combinazioni_input = st.text_input(
        "🔒 Max combinazioni (vuoto = nessun limite)",
        "",
        help="Limite massimo di combinazioni finali da selezionare dall'algoritmo greedy."
    )
    
    seed_random = st.number_input(
        "🎲 Seed per casualità (0 = casuale)",
        min_value=0, max_value=9999, value=0,
        help="Usa lo stesso seed per ottenere risultati riproducibili per la generazione dei numeri sorgente."
    )

# Elaborazione input
fixed_numbers_to_include = []
if numeri_fissi_input.strip():
    try:
        fixed_numbers_to_include = [int(x.strip()) for x in numeri_fissi_input.split(',')]
        # Filtra i numeri fissi che sono fuori dal range definito o non corrispondono al filtro pari/dispari
        fixed_numbers_to_include = [x for x in fixed_numbers_to_include if x in filtered_for_slider_numbers]
        if len(fixed_numbers_to_include) != len([int(x.strip()) for x in numeri_fissi_input.split(',')]):
             st.sidebar.warning("Alcuni 'Numeri da includere' sono stati ignorati perché fuori range o non conformi al filtro pari/dispari.")
    except ValueError:
        st.sidebar.error("❌ Formato numeri da includere non valido")
        fixed_numbers_to_include = []

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
    errori.append("Il range massimo deve essere maggiore del range minimo.")
    validazione_ok = False

if garanzia >= k_combination_length:
    errori.append("La garanzia deve essere minore della lunghezza della combinazione.")
    validazione_ok = False

# Validazione cruciale per i numeri fissi e il numero totale di numeri da generare
if len(fixed_numbers_to_include) > numero_di_numeri:
    errori.append(f"Il numero di 'Numeri da includere' ({len(fixed_numbers_to_include)}) non può essere maggiore di 'Numeri totali per il sistema' ({numero_di_numeri}).")
    validazione_ok = False

# Non è più valido che len(fixed_numbers_to_include) > k_combination_length sia un errore qui.
# Questo controllo è stato spostato dentro generate_combinations_with_fixed per la singola combinazione.

# Validazione: Se numeri_di_numeri è maggiore dei numeri disponibili dopo il filtro
if numero_di_numeri > len(filtered_for_slider_numbers):
    errori.append(f"Impossibile generare {numero_di_numeri} numeri totali per il sistema. "
                 f"Con il range e il filtro '{tipo_numeri_generazione}', sono disponibili solo {len(filtered_for_slider_numbers)} numeri.")
    validazione_ok = False

# Validazione: Non abbastanza numeri rimanenti per formare k-lunghezza se si usano fissi
if k_combination_length - len(fixed_numbers_to_include) < 0:
    errori.append(f"La lunghezza della combinazione ({k_combination_length}) è inferiore al numero di numeri da includere ({len(fixed_numbers_to_include)}).")
    validazione_ok = False

if k_combination_length - len(fixed_numbers_to_include) > len(filtered_for_slider_numbers) - len(fixed_numbers_to_include):
    # Questo controlla se ci sono abbastanza numeri casuali da pescare tra i 'remaining_numbers'
    # per raggiungere k_combination_length.
    if len(fixed_numbers_to_include) < k_combination_length: # Solo se dobbiamo pescare numeri aggiuntivi
        errori.append(f"Non ci sono abbastanza numeri disponibili ({len(filtered_for_slider_numbers) - len(fixed_numbers_to_include)}) per formare combinazioni di lunghezza {k_combination_length} con i {len(fixed_numbers_to_include)} numeri fissi specificati.")
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
    st.write(f"🎲 *Numeri totali per il sistema:* {numero_di_numeri}")
    st.write(f"📊 *Range:* {range_min} - {range_max}")
    st.write(f"🔢 *Lunghezza combinazione:* {k_combination_length}")
    st.write(f"📌 *Numeri da includere:* {fixed_numbers_to_include if fixed_numbers_to_include else 'Nessuno'}")
    st.write(f"🎯 *Garanzia:* {garanzia}")
    st.write(f"🔒 *Max combinazioni:* {max_combinations if max_combinations else 'Nessun limite'}")
    st.write(f"🔄 *Tipo numeri:* {tipo_numeri_generazione}")
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
            
            # --- LOGICA AGGIORNATA PER LA GENERAZIONE DELLA source_numbers_list ---
            # Filtra i numeri disponibili nel range in base al tipo (pari/dispari)
            potential_numbers_filtered_by_type = []
            for num in range(range_min, range_max + 1):
                if tipo_numeri_generazione == "Solo Pari" and num % 2 != 0:
                    continue
                if tipo_numeri_generazione == "Solo Dispari" and num % 2 == 0:
                    continue
                potential_numbers_filtered_by_type.append(num)

            # Rimuovi i numeri fissi dal pool di numeri da cui campionare casualmente
            temp_potential_numbers_for_sampling = [n for n in potential_numbers_filtered_by_type if n not in fixed_numbers_to_include]
            
            # Calcola quanti numeri casuali dobbiamo ancora pescare
            numbers_to_sample = numero_di_numeri - len(fixed_numbers_to_include)

            if numbers_to_sample < 0: # Questo caso dovrebbe essere già catturato dalle validazioni
                st.error("Errore interno: numeri da campionare negativi. Controllare le impostazioni dei numeri fissi.")
                start_time.empty()
                st.stop()

            # Campiona i numeri casuali necessari, se ce ne sono
            sampled_numbers = []
            if numbers_to_sample > 0:
                if numbers_to_sample > len(temp_potential_numbers_for_sampling):
                    st.error(f"❌ Impossibile generare {numero_di_numeri} numeri totali. Non ci sono abbastanza numeri casuali disponibili ({len(temp_potential_numbers_for_sampling)}) nel range e con i filtri per completare i restanti {numbers_to_sample} numeri.")
                    start_time.empty()
                    st.stop()
                sampled_numbers = random.sample(temp_potential_numbers_for_sampling, numbers_to_sample)
            
            # Costruisci la lista finale dei numeri sorgente (fissi + campionati, unici e ordinati)
            source_numbers_list = sorted(list(set(fixed_numbers_to_include + sampled_numbers)))
            # --- FINE LOGICA AGGIORNATA ---

            st.success(f"🎲 *Numeri sorgente generati ({tipo_numeri_generazione.lower()}):* {source_numbers_list}")
            
            # Generazione combinazioni
            with st.spinner("Generazione combinazioni iniziali..."):
                full_combinations = generate_combinations_with_fixed(
                    source_numbers_list, # Ora source_numbers_list contiene già i numeri fissi nel suo pool
                    k_combination_length,
                    # Non passiamo più fixed_numbers_to_include qui come parametro 'fixed_numbers',
                    # perché la funzione generate_combinations_with_fixed è stata progettata per
                    # operare su una lista 'source_numbers' che già contiene il pool completo.
                    # MA! L'utente vuole che i numeri fissi siano *in ogni* combinazione.
                    # Quindi la `generate_combinations_with_fixed` è comunque corretta e vuole i `fixed_numbers_to_include`
                    # come parametro separato per imporre che siano inclusi. La confusione era sulla `source_numbers_list`
                    # che doveva essere il pool da cui estrarre.
                    fixed_numbers_to_include # Correggo: il parametro va mantenuto per imporre l'inclusione
                )
            st.success(f"✅ *Combinazioni iniziali generate:* {len(full_combinations):,}")
            
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
                    f"Numeri totali per il sistema: {numero_di_numeri}",
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
                    csv_buffer.write(line + "\n")
                df_output.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                filename = f"combinazioni_G{garanzia}_C{len(final_combinations)}_L{k_combination_length}.csv"
                
                col_download1, col_download2 = st.columns(2)
                with col_download1:
                    st.markdown(get_download_link(csv_data, filename, "text/csv", "📁 Scarica CSV"), unsafe_allow_html=True)
                
                with col_download2:
                    # Genera anche un Excel con intestazione
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        # Scrivi l'intestazione come un DataFrame temporaneo
                        header_df = pd.DataFrame(header_info)
                        header_df.to_excel(writer, sheet_name='Riepilogo e Combinazioni', index=False, header=False)
                        
                        # Inizia il DataFrame delle combinazioni dopo l'header
                        startrow = len(header_info)
                        df_output.to_excel(writer, sheet_name='Riepilogo e Combinazioni', index=False, startrow=startrow)
                    excel_data = excel_buffer.getvalue()
                    
                    filename_excel = filename.replace('.csv', '.xlsx')
                    st.markdown(get_excel_download_link(excel_data, filename_excel, "📊 Scarica Excel"), unsafe_allow_html=True)
                
                start_time.empty()
                
            else:
                st.error("❌ Nessuna combinazione generata o ridotta con i parametri specificati. Prova a regolare i parametri o a disattivare i numeri fissi/garanzia se la lista iniziale è troppo piccola.")
                
        except Exception as e:
            st.error(f"❌ *Errore durante la generazione:* {str(e)}")
            st.info("💡 Prova a modificare i parametri e riprova. Assicurati che il numero di 'Numeri totali per il sistema' sia sufficientemente grande rispetto ai 'Numeri da includere' e alla 'Lunghezza combinazione'.")

# Footer informativo
st.markdown("---")
with st.expander("📖 Come Funziona l'Algoritmo"):
    st.markdown("""
    *🎯 Algoritmo Greedy con Garanzia:*
    
    1. *Generazione*: Crea tutte le combinazioni possibili dai numeri sorgente, includendo i numeri fissi specificati in ogni combinazione.
    2. *Analisi*: Calcola tutti i sottoinsiemi di dimensione 'garanzia' che devono essere coperti da queste combinazioni.
    3. *Ottimizzazione*: Seleziona iterativamente le combinazioni dal set iniziale che coprono il maggior numero di sottoinsiemi non ancora coperti.
    4. *Risultato*: Ottiene il minor numero di combinazioni che garantiscono la copertura di tutti i sottoinsiemi richiesti, o fino al limite massimo impostato.
    
    *💡 Esempio:* Con garanzia 3, ogni terzina possibile (formata dai numeri presenti nelle combinazioni iniziali) sarà presente in almeno una delle combinazioni finali selezionate.
    """)

with st.expander("❓ Aiuto e Suggerimenti"):
    st.markdown("""
    *🔧 Parametri Principali:*
    - *Numeri totali per il sistema*: Quanti numeri formano il pool di base da cui verranno create le combinazioni. Questo numero deve essere maggiore o uguale al numero di 'Numeri da includere'.
    - *Range*: Intervallo da cui pescare i numeri per creare il pool di base.
    - *Lunghezza combinazione*: Quanti numeri per ogni combinazione finale (es. 5 numeri per il Lotto). Deve essere maggiore del numero di 'Numeri da includere' se non si usano solo numeri fissi.
    - *Garanzia*: Dimensione dei sottoinsiemi da garantire. Deve essere sempre minore della 'Lunghezza combinazione'.
    
    *💡 Suggerimenti:*
    - Inizia con parametri piccoli per testare.
    - **Numeri da includere (fissi)**: Questi numeri appariranno in *ogni* combinazione finale. Se il numero di questi elementi è uguale a 'Numeri totali per il sistema', allora il sistema utilizzerà SOLO questi numeri come pool di base, senza generare numeri casuali.
    - Il 'Seed' ti permette di riprodurre gli stessi risultati in diverse esecuzioni.
    - *Tipo di numeri da generare*: Puoi scegliere di generare solo numeri pari, solo numeri dispari, o tutti i numeri nel range.
    
    *⚡ Performance:*
    - L'algoritmo greedy può essere intensivo per un numero molto elevato di combinazioni iniziali o di sottoinsiemi da coprire.
    - Usa 'Max combinazioni' per limitare il risultato finale, anche se la copertura completa non è stata raggiunta.
    """)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🚀 Powered by Streamlit <br>
        Creato da Giuseppe Andolfi<br>
        dammi il tuo feedback: <a href="mailto:andolfi.giuseppe@gmail.com">andolfi.giuseppe@gmail.com</a>
    </div>
    """,
    unsafe_allow_html=True
)
