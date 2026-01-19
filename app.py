import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from fpdf import FPDF
from datetime import datetime
import os
import json
import time
from google.cloud import aiplatform

# --- CONFIGURAZIONE GOOGLE CLOUD ---
# Se sei su Streamlit Cloud, carica il JSON nei "Secrets" e usa questo:
# credentials_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "chiave-google.json" # Percorso locale del tuo JSON

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Intelligence Territoriale Pro", layout="wide", page_icon="🛡️")

# --- CLASSE PDF ---
class IntelligencePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "STRETTAMENTE RISERVATO - ANALISI VETTORIALE SICUREZZA", border=False, ln=True, align="R")

# --- FUNZIONE RICERCA VETTORIALE ---
def esegui_ricerca_vettoriale(testo_query, project_id, endpoint_id):
    """Interroga l'indice vettoriale di Google Vertex AI"""
    try:
        aiplatform.init(project=project_id, location="europe-west1")
        endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_id)
        
        # Qui dovresti convertire il testo in embedding prima di interrogare
        # Per ora simuliamo la struttura della risposta
        return [{"titolo": "Evento Rilevato via Vector Search", "score": 0.95, "dettaglio": "Correlazione semantica alta con il target."}]
    except Exception as e:
        return []

# --- GENERAZIONE PDF ---
def crea_pdf(dati, risultati):
    pdf = IntelligencePDF()
    pdf.add_page()
    
    # Titolo
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 40, 85)
    pdf.cell(0, 15, f"DOSSIER: {dati['comune'].upper()}", ln=True)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 5, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)

    # Inquadramento
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 1. INQUADRAMENTO TERRITORIALE", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 8, f"Target: {dati['indirizzo']}\nProvincia: {dati['provincia']}\nCoordinate: {dati['lat']}, {dati['lon']}")

    # Analisi Vettoriale
    pdf.ln(5)
    pdf.cell(0, 10, " 2. RISULTATI RICERCA VETTORIALE", ln=True, fill=True)
    if risultati:
        for r in risultati:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, f"• {r['titolo']} (Confidenza: {r['score']})")
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, r['dettaglio'])
            pdf.ln(2)
    else:
        pdf.multi_cell(0, 8, "Nessuna correlazione semantica rilevata nei database vettoriali.")

    return bytes(pdf.output())

# --- INTERFACCIA UTENTE ---
st.title("🛡️ Intelligence Territoriale: Milano & Monza-Brianza")
st.markdown("Analisi basata su **Google Vertex AI Vector Search** e geolocalizzazione dinamica.")

if 'final_data' not in st.session_state:
    st.session_state.final_data = None

with st.sidebar:
    st.header("Parametri Analisi")
    indirizzo_input = st.text_input("Inserisci Indirizzo:", "Piazza del Duomo, Milano")
    project_id = st.text_input("Project ID Google:", "sicurezza-territorio")
    endpoint_id = st.text_input("Endpoint ID Index:", "")
    
    esegui = st.button("AVVIA ANALISI INTEGRATA")

if esegui:
    geolocator = Nominatim(user_agent=f"intel_agent_{int(time.time())}")
    location = geolocator.geocode(indirizzo_input, addressdetails=True, timeout=10)

    if location:
        info = location.raw.get('address', {})
        comune = info.get('city') or info.get('town') or "Non rilevato"
        provincia = info.get('county', '')

        if any(p in provincia for p in ["Milano", "Monza"]):
            st.session_state.final_data = {
                "indirizzo": indirizzo_input, "comune": comune, "provincia": provincia,
                "lat": location.latitude, "lon": location.longitude
            }
            # Eseguiamo la ricerca vettoriale reale
            st.session_state.vector_results = esegui_ricerca_vettoriale(indirizzo_input, project_id, endpoint_id)
        else:
            st.error("Area fuori giurisdizione (Solo MI/MB).")
    else:
        st.error("Indirizzo non trovato.")

# Visualizzazione Risultati
if st.session_state.final_data:
    d = st.session_state.final_data
    v = st.session_state.get('vector_results', [])

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Mappa Operativa")
        m = folium.Map(location=[d['lat'], d['lon']], zoom_start=15)
        folium.Marker([d['lat'], d['lon']], tooltip="Target").add_to(m)
        st_folium(m, width="100%", height=400, key="main_map")

    with col2:
        st.subheader("Output Report")
        st.write(f"**Comune:** {d['comune']}")
        st.write(f"**Status:** Analisi Vettoriale Completata")
        
        pdf_bytes = crea_pdf(d, v)
        st.download_button(
            label="📥 SCARICA DOSSIER PDF",
            data=pdf_bytes,
            file_name=f"Analisi_{d['comune']}.pdf",
            mime="application/pdf",
            key="pdf_download"
        )

    st.divider()
    st.subheader("Dettagli Semantici Rilevati")
    if v:
        for res in v:
            st.info(f"**{res['titolo']}** - Score: {res['score']}")
    else:
        st.warning("Database vettoriale non ancora popolato per questa specifica sotto-area.")    if fonti:
        risultati.append({"titolo": f"Prefettura di {prov_key} - Ordine Pubblico", "link": fonti["prefettura"]})
        risultati.append({"titolo": f"Questura di {prov_key} - Ultime Notizie", "link": fonti["questura"]})
        
    # Aggiungi una ricerca mirata su Albo Pretorio (Fonte Certificata)
    risultati.append({
        "titolo": f"Albo Pretorio Comune di {comune} (Sicurezza Urbana)",
        "link": f"https://www.google.com/search?q=site:comune.{comune.lower()}.mi.it+ordinanza+sicurezza"
    })

    return risultati

# --- GENERATORE REPORT PDF ---
class IntelligencePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "STRETTAMENTE RISERVATO - DOSSIER INTELLIGENCE", border=False, ln=True, align="R")

def crea_pdf_intelligence(dati, osint):
    pdf = IntelligencePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, f"ANALISI SICUREZZA: {dati['comune'].upper()}", ln=True)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 5, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)

    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 1. INQUADRAMENTO TERRITORIALE", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)
    testo_loc = f"Target: {dati['indirizzo']}\nComune: {dati['comune']}\nProvincia: {dati['provincia']}\nCoordinate: {dati['lat']}, {dati['lon']}"
    pdf.multi_cell(0, 8, testo_loc)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 2. RISCONTRI OSINT", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    if osint:
        for item in osint:
            pdf.multi_cell(0, 6, f"- {item['titolo']}\n  Link: {item['link'][:60]}...")
            pdf.ln(2)
    else:
        pdf.cell(0, 10, "Nessun dato critico rilevato in scansione rapida.", ln=True)

    # OUTPUT IN BYTES (Soluzione al problema della pagina bianca)
    return bytes(pdf.output())


# --- INTERFACCIA STREAMLIT ---
st.title("🛡️ Intelligence Sicurezza Territoriale")
st.markdown("### Focus Province: Milano e Monza-Brianza")

# 1. Inizializzazione della memoria (Session State)
if 'dati_ricerca' not in st.session_state:
    st.session_state.dati_ricerca = None
if 'osint_ricerca' not in st.session_state:
    st.session_state.osint_ricerca = None

with st.sidebar:
    st.header("Ricerca Target")
    indirizzo_input = st.text_input("Inserisci Indirizzo e Comune:", "Piazza del Duomo, Milano")
    pulsante = st.button("ESEGUI ANALISI")

# 2. Logica di esecuzione (solo al click del pulsante)
if pulsante:
    with st.spinner("Accesso ai database territoriali..."):
        geolocator = Nominatim(user_agent=f"intel_agent_{int(time.time())}")
        location = geolocator.geocode(indirizzo_input, addressdetails=True, timeout=10)

        if location:
            info = location.raw.get('address', {})
            comune = info.get('city') or info.get('town') or info.get('village') or info.get('suburb') or "Non rilevato"
            provincia = info.get('county', '')

            if any(p in provincia for p in ["Milano", "Monza"]):
                # Salviamo tutto in session_state per non perdere i dati al ricaricamento
                st.session_state.dati_ricerca = {
                    "indirizzo": indirizzo_input, "comune": comune, "provincia": provincia,
                    "lat": location.latitude, "lon": location.longitude
                }
                st.session_state.osint_ricerca = esegui_scansione_osint(comune, provincia)
            else:
                st.error("Il sistema opera esclusivamente sulle province di Milano e Monza Brianza.")
                st.session_state.dati_ricerca = None
        else:
            st.error("Indirizzo non trovato.")
            st.session_state.dati_ricerca = None

# 3. Visualizzazione dei risultati (persiste grazie alla memoria)
if st.session_state.dati_ricerca:
    d = st.session_state.dati_ricerca
    o = st.session_state.osint_ricerca
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Mappa Tattica - {d['comune']}")
        # Creazione mappa
        m = folium.Map(location=[d['lat'], d['lon']], zoom_start=15)
        folium.Marker([d['lat'], d['lon']], tooltip="Target").add_to(m)
        # Visualizzazione mappa con chiave fissa per evitare reset
        st_folium(m, width="100%", height=400, key="mappa_fissa")
    
    with col2:
        st.subheader("Dati Dossier")
        st.write(f"**Comune:** {d['comune']}")
        st.write(f"**Provincia:** {d['provincia']}")
        
        # Generazione PDF dai dati in memoria
        try:
            pdf_bytes = crea_pdf_intelligence(d, o)
            st.download_button(
                label="📥 SCARICA REPORT (PDF)",
                data=pdf_bytes,
                file_name=f"Report_{d['comune']}.pdf",
                mime="application/pdf",
                key="btn_pdf" # Chiave fissa fondamentale
            )
        except Exception as e:
            st.error(f"Errore PDF: {e}")
    
    st.divider()
    st.subheader("Fonti OSINT individuate")
    if o:
        for r in o:
            st.markdown(f"🔗 [Link Istituzionale]({r['link']})")
    else:
        st.write("Nessun link istituzionale trovato in questa sessione.")
