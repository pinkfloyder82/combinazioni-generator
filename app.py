
import streamlit as st
import pandas as pd
from itertools import combinations
import random
import io
import base64

# Configurazione pagina
st.set_page_config(page_title="🎯 Generatore Combinazioni", page_icon="🎯", layout="wide")

def generate_combinations_with_fixed(source_numbers, k, fixed_numbers=None):
    if fixed_numbers is None:
        fixed_numbers = []

    if not isinstance(source_numbers, list) or not all(isinstance(n, int) for n in source_numbers):
        raise ValueError("La lista 'source_numbers' deve contenere solo numeri interi.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("La lunghezza 'k' deve essere un numero intero positivo.")
    if not isinstance(fixed_numbers, list) or not all(isinstance(n, int) for n in fixed_numbers):
        raise ValueError("La lista 'fixed_numbers' deve contenere solo numeri interi.")

    full_set = sorted(set(source_numbers))
    if len(full_set) < k:
        raise ValueError("Numeri insufficienti per generare combinazioni della lunghezza richiesta.")

    return list(combinations(full_set, k))

# Interfaccia utente
st.title("🎯 Generatore Combinazioni con Numeri Fissi e Garanzia")

range_min = 1
range_max = 90

numero_di_numeri = st.sidebar.slider("📊 Numeri totali da generare", min_value=5, max_value=90, value=15)
k_combination_length = st.sidebar.slider("🔢 Lunghezza combinazione", min_value=2, max_value=8, value=5)
garanzia = st.sidebar.slider("🎯 Garanzia", min_value=2, max_value=min(7, k_combination_length - 1), value=3)

numeri_fissi_input = st.sidebar.text_input("📌 Numeri fissi (separati da virgola)", "1,2,3")
try:
    fixed_numbers_to_include = [int(x.strip()) for x in numeri_fissi_input.split(',') if x.strip()]
except ValueError:
    st.sidebar.error("❌ Formato numeri da includere non valido")
    st.stop()

if len(fixed_numbers_to_include) > numero_di_numeri:
    numero_di_numeri = len(fixed_numbers_to_include)
    st.sidebar.warning(f"⚠️ 'Numeri totali da generare' aggiornato a {numero_di_numeri} per includere tutti i numeri fissi.")

if len(fixed_numbers_to_include) > k_combination_length:
    st.sidebar.warning("⚠️ Hai inserito più numeri fissi della lunghezza della combinazione. Saranno comunque considerati.")

# Generazione numeri casuali aggiuntivi
available_numbers = [n for n in range(range_min, range_max + 1) if n not in fixed_numbers_to_include]
random_numbers = random.sample(available_numbers, numero_di_numeri - len(fixed_numbers_to_include))
source_numbers = fixed_numbers_to_include + random_numbers

st.write(f"📦 Numeri sorgente ({len(source_numbers)}):", sorted(source_numbers))

generate_button = st.button("🚀 Genera combinazioni")
if generate_button:
    try:
        full_combinations = generate_combinations_with_fixed(source_numbers, k_combination_length, fixed_numbers_to_include)
        st.success(f"✅ Generate {len(full_combinations)} combinazioni da {k_combination_length} numeri")
        df = pd.DataFrame(full_combinations, columns=[f"N{i+1}" for i in range(k_combination_length)])
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Errore: {str(e)}")
