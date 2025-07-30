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

# Funzione per generare tutte le combinazioni di k elementi da un pool di numeri
def generate_all_k_combinations_from_pool(source_numbers_pool, k):
    """
    Genera tutte le combinazioni di k numeri dal pool fornito.

    Args:
        source_numbers_pool (list): La lista (pool) di numeri da cui generare le combinazioni.
        k (int): La lunghezza desiderata di ogni combinazione.

    Returns:
        list: Una lista di tuple, dove ogni tupla è una combinazione ordinata di k numeri.
    """
    if not isinstance(source_numbers_pool, list) or not all(isinstance(n, int) for n in source_numbers_pool):
        raise ValueError("Il 'pool' di numeri sorgente deve contenere solo numeri interi.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("La lunghezza 'k' della combinazione deve essere un numero intero positivo.")

    if k > len(source_numbers_pool):
        raise ValueError(f"Impossibile generare combinazioni di lunghezza {k} da un pool di soli {len(source_numbers_pool)} numeri.")

    # Genera tutte le combinazioni e le ordina per consistenza
    all_combinations = [tuple(sorted(combo)) for combo in combinations(source_numbers_pool, k)]
    return sorted(list(set(all_combinations))) # set per unicità, sorted per ordine consistente


def reduce_combinations_with_guarantee_greedy(full_combinations, guarantee_size, max_combinations=None):
    if not full_combinations:
        st.warning("Nessuna combinazione da ridurre. Assicurati che le combinazioni iniziali siano state generate.")
        return []

    if guarantee_size <= 0:
        st.error("Errore: La dimensione della garanzia deve essere un numero positivo.")
        return []
    if guarantee_size > len(full_combinations[0]):
        st.error("Errore: La dimensione della garanzia non può essere maggiore della lunghezza della combinazione stessa.")
        return []

    # Caso speciale: se guarantee_size è uguale alla lunghezza della combinazione
    # In questo caso, ogni combinazione è un "target" a sé. L'algoritmo non ridurrebbe
    # ma selezionerebbe solo le combinazioni esatte. Applichiamo solo il limite max_combinations, se presente.
    if guarantee_size == len(full_combinations[0]):
        st.info("Garanzia impostata alla lunghezza della combinazione (esatta). Non verrà applicata ulteriore riduzione oltre il limite massimo di combinazioni, se specificato. Verranno incluse tutte le combinazioni iniziali.")
        if max_combinations is not None and len(full_combinations) > max_combinations:
            return sorted(random.sample(full_combinations, max_combinations)) # Prendo un campione casuale
        else:
            return full_combinations # Ritorna tutte le combinazioni se non c'è limite

    required_subsets = set()
    
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 Calcolo sottoinsiemi da garantire (target sets)...")
        progress_bar = st.progress(0)
        
        num_full_combos = len(full_combinations)
        update_interval = max(1, num_full_combos // 100)
        if num_full_combos < 1000:
            update_interval = 1

        for i, combo in enumerate(full_combinations):
            for subset in combinations(combo, guarantee_size):
                required_subsets.add(tuple(sorted(subset)))
            if (i + 1) % update_interval == 0 or (i + 1) == num_full_combos:
                progress_bar.progress((i + 1) / num_full_combos)
        
        progress_bar.empty()
        
    covered_subsets = set()
    selected_combinations = []
    combos_remaining = set(full_combinations)

    with progress_container:
        st.info(f"🎯 Selezione combinazioni con algoritmo greedy per coprire {len(required_subsets):,} sottoinsiemi...")
        progress_bar2 = st.progress(0)
        
        iteration = 0
        while covered_subsets != required_subsets and combos_remaining:
            best_combo = None
            best_new_coverage = -1

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

# Funzioni per il download
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

max_numbers_in_range = range_max - range_min + 1

# Calcola il massimo valore possibile per il numero_di_numeri slider
# che è il numero di elementi nel range (pre-filtri pari/dispari per la preview)
max_possible_system_numbers_raw = range_max - range_min + 1

# Slider "Numeri totali per il sistema"
numero_di_numeri = st.sidebar.slider(
    "📊 Numeri totali per il sistema",
    min_value=5, max_value=max_possible_system_numbers_raw, value=min(15, max_possible_system_numbers_raw), # Default 15 o max disponibile
    key="num_gen_slider",
    help="Questo è il numero totale di numeri che formeranno il pool di base del tuo sistema. "
         "Se i 'Numeri da includere' (fissi nel pool) sono pari a questo valore, verranno usati SOLO quelli come base per il sistema."
)

k_combination_length = st.sidebar.slider(
    "🔢 Lunghezza combinazione",
    min_value=3, max_value=10, value=5,
    key="k_len_slider",
    help="Quanti numeri per ogni combinazione finale"
)

garanzia = st.sidebar.slider(
    "🎯 Garanzia",
    min_value=1, # La garanzia può essere anche 1 (copertura minima)
    max_value=k_combination_length, # Max guarantee can be k as well, it means covering all exact combinations
    value=min(3, k_combination_length),
    key="guarantee_slider",
    help="Quanti numeri devono essere garantiti in comune in ciascun sottoinsieme. Deve essere minore o uguale della lunghezza combinazione."
)

# Parametri avanzati
with st.sidebar.expander("⚙ Parametri Avanzati"):
    # Spostato qui come richiesto
    tipo_numeri_generazione = st.radio(
        "Tipo di numeri da generare nel pool",
        ("Tutti", "Solo Pari", "Solo Dispari"),
        index=0,
        key="tipo_numeri_gen_radio",
        help="Scegli se i numeri casuali aggiunti al pool del sistema devono essere pari, dispari o entrambi nel range specificato."
    )

    numeri_fissi_input = st.text_input(
        "📌 Numeri da includere nel pool (separati da virgola)",
        "",
        key="fixed_numbers_input",
        help=f"Questi numeri saranno inclusi nel pool di {numero_di_numeri} numeri base. "
             "Se il loro numero è pari a 'Numeri totali per il sistema', verranno usati SOLO questi numeri."
    )
    
    max_combinazioni_input = st.text_input(
        "🔒 Max combinazioni finali (vuoto = nessun limite)",
        "",
        key="max_comb_input",
        help="Limite massimo di combinazioni finali da selezionare dall'algoritmo greedy. Utile per controllare la dimensione del risultato."
    )
    
    seed_random = st.number_input(
        "🎲 Seed per casualità (0 = casuale)",
        min_value=0, max_value=9999, value=0,
        key="seed_input",
        help="Usa lo stesso seed per ottenere risultati riproducibili per la generazione dei numeri casuali del pool."
    )

# Elaborazione input per i numeri fissi e il pool
fixed_numbers_for_pool_construction = []
if numeri_fissi_input.strip():
    try:
        raw_fixed_numbers = [int(x.strip()) for x in numeri_fissi_input.split(',')]
        # Rimuovi duplicati e ordina per pulizia
        fixed_numbers_for_pool_construction = sorted(list(set(raw_fixed_numbers)))
        
    except ValueError:
        st.sidebar.error("❌ Formato numeri da includere non valido. Inserire numeri interi separati da virgola.")
        fixed_numbers_for_pool_construction = []


max_combinations = None
if max_combinazioni_input.strip():
    try:
        max_combinations = int(max_combinazioni_input)
        if max_combinations <= 0:
            max_combinations = None
    except ValueError:
        st.sidebar.error("❌ Formato max combinazioni non valido. Inserire un numero intero positivo.")

# Set seed se specificato
if seed_random > 0:
    random.seed(seed_random)

# Validazioni
validazione_ok = True
errori = []

if range_max <= range_min:
    errori.append("Il range massimo deve essere maggiore del range minimo.")
    validazione_ok = False

if garanzia > k_combination_length:
    errori.append("La garanzia non può essere maggiore della lunghezza della combinazione.")
    validazione_ok = False

# Validazione: "Numeri da includere" (fissi nel pool) non devono essere fuori range/tipo
# e la loro quantità non può superare il "Numeri totali per il sistema"
valid_fixed_numbers_in_range_and_type = []
for num in fixed_numbers_for_pool_construction:
    if range_min <= num <= range_max:
        if tipo_numeri_generazione == "Solo Pari" and num % 2 != 0:
            continue
        if tipo_numeri_generazione == "Solo Dispari" and num % 2 == 0:
            continue
        valid_fixed_numbers_in_range_and_type.append(num)
        
if len(valid_fixed_numbers_in_range_and_type) != len(fixed_numbers_for_pool_construction):
    st.sidebar.warning("Alcuni 'Numeri da includere' sono stati ignorati perché fuori range o non conformi al filtro pari/dispari. Verranno considerati solo i validi.")
fixed_numbers_for_pool_construction = valid_fixed_numbers_in_range_and_type # Aggiorna la lista dei fissi validi


if len(fixed_numbers_for_pool_construction) > numero_di_numeri:
    errori.append(f"Il numero di 'Numeri da includere' ({len(fixed_numbers_for_pool_construction)}) non può essere maggiore di 'Numeri totali per il sistema' ({numero_di_numeri}).")
    validazione_ok = False

# Calcola il numero massimo di numeri casuali che possiamo estrarre dal range filtrato,
# dopo aver escluso i fissi già presenti.
potential_numbers_for_sampling = []
for num in range(range_min, range_max + 1):
    if num in fixed_numbers_for_pool_construction: # Escludi i fissi che saranno nel pool
        continue
    if tipo_numeri_generazione == "Solo Pari" and num % 2 != 0:
        continue
    if tipo_numeri_generazione == "Solo Dispari" and num % 2 == 0:
        continue
    potential_numbers_for_sampling.append(num)

# Validazione: Ci sono abbastanza numeri disponibili per formare il pool del sistema?
numbers_to_sample_for_pool_size = numero_di_numeri - len(fixed_numbers_for_pool_construction)
if numbers_to_sample_for_pool_size > 0: # Se dobbiamo pescare numeri casuali
    if numbers_to_sample_for_pool_size > len(potential_numbers_for_sampling):
        errori.append(f"Impossibile creare un pool di {numero_di_numeri} numeri. "
                     f"Hai {len(fixed_numbers_for_pool_construction)} numeri fissi e solo {len(potential_numbers_for_sampling)} numeri casuali disponibili nel range e con i filtri. "
                     f"Servono {numbers_to_sample_for_pool_size} numeri casuali in più.")
        validazione_ok = False
elif numbers_to_sample_for_pool_size < 0:
    # Questo caso dovrebbe essere già catturato dal check `len(fixed_numbers_for_pool_construction) > numero_di_numeri`
    pass


# Validazione: Se k (lunghezza combinazione) è maggiore del numero totale di numeri del pool
if k_combination_length > numero_di_numeri:
    errori.append(f"La lunghezza della combinazione ({k_combination_length}) non può essere maggiore del 'Numeri totali per il sistema' ({numero_di_numeri}).")
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
    st.write(f"📌 *Numeri da includere nel pool:* {fixed_numbers_for_pool_construction if fixed_numbers_for_pool_construction else 'Nessuno'}")
    st.write(f"🎯 *Garanzia:* {garanzia}")
    st.write(f"🔒 *Max combinazioni finali:* {max_combinations if max_combinations else 'Nessun limite'}")
    st.write(f"🔄 *Tipo numeri nel pool:* {tipo_numeri_generazione}")
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
            
            # --- LOGICA DI COSTRUZIONE DEL POOL DI NUMERI DEL SISTEMA (source_numbers_list) ---
            # Questo è il pool di `numero_di_numeri` elementi da cui verranno generate tutte le combinazioni
            
            # Campiona i numeri casuali necessari per raggiungere la dimensione del pool,
            # escludendo i numeri fissi già scelti e rispettando i filtri.
            sampled_numbers = []
            if numbers_to_sample_for_pool_size > 0: # Se dobbiamo pescare numeri casuali
                sampled_numbers = random.sample(potential_numbers_for_sampling, numbers_to_sample_for_pool_size)
            
            # Costruisci la lista finale dei numeri sorgente (pool del sistema: fissi + campionati, unici e ordinati)
            source_numbers_list = sorted(list(set(fixed_numbers_for_pool_construction + sampled_numbers)))
            
            # Doppia validazione finale sulla dimensione del pool generato, in caso di bug imprevisti
            if len(source_numbers_list) != numero_di_numeri:
                 st.warning(f"Attenzione: la dimensione del pool di numeri generati ({len(source_numbers_list)}) non corrisponde a 'Numeri totali per il sistema' richiesti ({numero_di_numeri}). Questo può indicare un problema con i numeri fissi o i filtri. Il sistema userà {len(source_numbers_list)} numeri come base.")
            
            # --- FINE LOGICA DI COSTRUZIONE DEL POOL ---

            st.success(f"🎲 *Pool di numeri del sistema ({tipo_numeri_generazione.lower()}):* {source_numbers_list}")
            
            # Generazione combinazioni iniziali da questo pool
            with st.spinner("Generazione combinazioni iniziali (da tutto il pool)..."):
                # Ora passiamo il pool completo e k. La funzione genera tutte le combinazioni da esso.
                full_combinations = generate_all_k_combinations_from_pool(
                    source_numbers_list,
                    k_combination_length
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
                source_str = ','.join(map(str, source_numbers_list)) # Usa map(str, ...) per handle ints
                if len(full_combinations) > 0: # Evita divisione per zero
                    riduzione_perc = (1 - len(final_combinations)/len(full_combinations)) * 100
                else:
                    riduzione_perc = 0.0

                header_info = [
                    f"Generazione Combinazioni - Riepilogo",
                    f"Data Generazione: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Numeri totali per il sistema (richiesti): {numero_di_numeri}",
                    f"Pool di numeri effettivo usato: {len(source_numbers_list)} -> {source_str}",
                    f"Range: {range_min}-{range_max}",
                    f"Lunghezza Combinazione: {k_combination_length}",
                    f"Numeri da includere nel pool (fissi): {fixed_numbers_for_pool_construction if fixed_numbers_for_pool_construction else 'Nessuno'}",
                    f"Tipo numeri nel pool: {tipo_numeri_generazione}",
                    f"Garanzia: {garanzia}",
                    f"Max Combinazioni finali: {max_combinations if max_combinations else 'Nessun limite'}",
                    f"Seed casualità: {seed_random if seed_random > 0 else 'Casuale'}",
                    f"Combinazioni iniziali generate (da tutto il pool): {len(full_combinations):,}",
                    f"Combinazioni finali (ridotte): {len(final_combinations):,}",
                    f"Riduzione rispetto alle iniziali: {riduzione_perc:.1f}%",
                    "", # Riga vuota per separazione
                    "Combinazioni:"
                ]
                
                # Visualizzazione risultati
                st.markdown("---")
                st.subheader("📊 Risultati Generati")
                
                # Statistiche
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("🎯 Combinazioni Finali", len(final_combinations))
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
            st.info("💡 Prova a modificare i parametri e riprova. Assicurati che il 'Pool di numeri del sistema' sia sufficientemente grande rispetto alla 'Lunghezza combinazione'.")

# Footer informativo
st.markdown("---")
with st.expander("📖 Come Funziona l'Algoritmo"):
    st.markdown("""
    *🎯 Algoritmo Greedy con Garanzia:*
    
    1. **Generazione Pool di Numeri del Sistema**: Il sistema crea un pool di numeri (`Numeri totali per il sistema`) mescolando i tuoi 'Numeri da includere nel pool' (fissi) con numeri casuali (rispettando il range e il filtro pari/dispari). Questo è il set di numeri di base da cui si estrarrà.
    2. **Generazione Combinazioni Iniziali**: Da questo pool di numeri di base, vengono generate *tutte* le possibili combinazioni della 'Lunghezza combinazione' desiderata.
    3. **Analisi dei Sottoinsiemi (Target Sets)**: Vengono calcolati tutti i sottoinsiemi (es. le terzine se la garanzia è 3) di dimensione 'Garanzia' presenti nelle combinazioni iniziali. Questi sono gli elementi che l'algoritmo cercherà di "coprire".
    4. **Ottimizzazione (Greedy)**: L'algoritmo seleziona un sottoinsieme di queste combinazioni iniziali. Ad ogni passo, sceglie la combinazione che "copre" il maggior numero di 'target sets' non ancora coperti. Questo si ripete fino a quando tutti i 'target sets' sono coperti o si raggiunge un limite massimo di combinazioni.
    5. **Risultato**: Il sistema ti fornisce il set di combinazioni ridotte che soddisfa la 'Garanzia' richiesta.
    
    *💡 Esempio:* Se hai 'Lunghezza combinazione' 5 e 'Garanzia' 3, il sistema garantisce che ogni possibile terzina di numeri (formata dai numeri presenti nel tuo 'Pool di numeri del sistema') sarà inclusa in almeno una delle combinazioni finali selezionate.
    """)

with st.expander("❓ Aiuto e Suggerimenti"):
    st.markdown("""
    *🔧 Parametri Principali:*
    - **Numeri totali per il sistema**: La dimensione del pool di numeri da cui verranno generate le combinazioni. Questo numero deve essere maggiore o uguale al numero di 'Numeri da includere nel pool'.
    - **Range Min/Max**: L'intervallo da cui vengono pescati i numeri casuali per completare il pool.
    - **Lunghezza combinazione**: Quanti numeri per ogni combinazione finale (es. 5 numeri per il Lotto). Non può essere maggiore del 'Numeri totali per il sistema'.
    - **Garanzia**: Quanti numeri devono essere garantiti in comune. Deve essere minore o uguale della 'Lunghezza combinazione'. Se è uguale, il sistema garantirà la presenza delle combinazioni esatte.
    
    *⚙ Parametri Avanzati:*
    - **Tipo di numeri da generare nel pool**: Filtra i numeri casuali del pool (es. solo pari o solo dispari).
    - **Numeri da includere nel pool (fissi)**: Questi numeri saranno sempre parte del tuo 'Pool di numeri del sistema'. Se indichi un numero sufficiente di fissi, non verranno aggiunti numeri casuali.
    - **Max combinazioni finali**: Limite massimo al numero di combinazioni finali generate. Utile per controllare la dimensione del risultato e il tempo di calcolo.
    - **Seed per casualità**: Ti permette di riprodurre gli stessi risultati (relativi alla generazione del pool casuale) in diverse esecuzioni.
    
    *⚡ Performance:*
    - L'algoritmo greedy può essere intensivo per un numero molto elevato di combinazioni iniziali o di sottoinsiemi da coprire. Riduci il 'Pool di numeri del sistema' o la 'Lunghezza combinazione' se i tempi sono eccessivi.
    - Il 'Max combinazioni finali' può aiutare a controllare le performance.
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
