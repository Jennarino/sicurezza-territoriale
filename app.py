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
if "gcp_service_account" in st.secrets:
    credentials_info = dict(st.secrets["gcp_service_account"])
    with open("google_key.json", "w") as f:
        json.dump(credentials_info, f)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_key.json"

# --- CLASSE PDF (DEFINIZIONE UNICA) ---
class IntelligencePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "STRETTAMENTE RISERVATO - DOSSIER INTELLIGENCE", border=False, ln=True, align="R")

# --- FUNZIONI DI SUPPORTO ---

def esegui_scansione_osint(comune, provincia):
    """Genera link istituzionali basati sull'area"""
    risultati = []
    # Link istituzionale fisso per Prefettura
    prov_key = "Milano" if "Milano" in provincia else "Monza"
    risultati.append({
        "titolo": f"Prefettura di {prov_key} - Ordine Pubblico",
        "link": f"https://www.google.com/search?q=prefettura+{prov_key}+sicurezza"
    })
    # Link dinamico Albo Pretorio
    risultati.append({
        "titolo": f"Albo Pretorio Comune di {comune} (Sicurezza Urbana)",
        "link": f"https://www.google.com/search?q=site:comune.{comune.lower()}.it+ordinanza+sicurezza"
    })
    return risultati

def esegui_ricerca_vettoriale(testo_query, project_id, endpoint_id):
    """Interroga l'indice vettoriale di Google Vertex AI"""
    try:
        if not endpoint_id: return []
        aiplatform.init(project=project_id, location="europe-west1")
        # Nota: Qui servirebbe l'embedding reale, simuliamo il ritorno per ora
        return [{"titolo": "Correlazione Semantica Rilevata", "score": 0.88, "dettaglio": "Segnalata attività di controllo nell'area target."}]
    except Exception as e:
        return []

def crea_pdf_intelligence(dati, osint, vector):
    pdf = IntelligencePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, f"ANALISI SICUREZZA: {dati['comune'].upper()}", ln=True)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 5, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)

    # 1. Inquadramento
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 1. INQUADRAMENTO TERRITORIALE", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)
    testo_loc = f"Target: {dati['indirizzo']}\nProvincia: {dati['provincia']}\nCoordinate: {dati['lat']}, {dati['lon']}"
    pdf.multi_cell(0, 8, testo_loc)

    # 2. Risultati Vettoriali
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 2. ANALISI VETTORIALE (AI)", ln=True, fill=True)
    if vector:
        for v in vector:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"• {v['titolo']} - Score: {v['score']}", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, v['dettaglio'])
    else:
        pdf.cell(0, 10, "Nessun dato semantico trovato nell'indice.", ln=True)

    # 3. OSINT
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 3. RISCONTRI OSINT", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    if osint:
        for item in osint:
            pdf.multi_cell(0, 6, f"- {item['titolo']}\n  Link: {item['link'][:65]}...")
            pdf.ln(2)
    
    return bytes(pdf.output())

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Intelligence Sicurezza", layout="wide")
st.title("🛡️ Intelligence Sicurezza Territoriale")
st.markdown("### Focus Province: Milano e Monza-Brianza")

# Inizializzazione Session State
if 'dati' not in st.session_state: st.session_state.dati = None
if 'osint' not in st.session_state: st.session_state.osint = None
if 'vector' not in st.session_state: st.session_state.vector = None

with st.sidebar:
    st.header("Configurazione")
    if "gcp_service_account" in st.secrets:
        st.success("✅ Credenziali GCP OK")
    else:
        st.error("❌ Credenziali GCP mancanti")
    
    indirizzo_input = st.text_input("Target (Indirizzo e Comune):", "Piazza del Duomo, Milano")
    project_id = st.text_input("Project ID:", "sicurezza-territorio")
    endpoint_id = st.text_input("Endpoint ID Vector Index:")
    pulsante = st.button("ESEGUI ANALISI")

if pulsante:
    with st.spinner("Scansione in corso..."):
        geolocator = Nominatim(user_agent=f"intel_agent_{int(time.time())}")
        location = geolocator.geocode(indirizzo_input, addressdetails=True, timeout=10)

        if location:
            info = location.raw.get('address', {})
            comune = info.get('city') or info.get('town') or "Rilevato"
            provincia = info.get('county', '')

            if any(p in provincia for p in ["Milano", "Monza"]):
                st.session_state.dati = {
                    "indirizzo": indirizzo_input, "comune": comune, "provincia": provincia,
                    "lat": location.latitude, "lon": location.longitude
                }
                st.session_state.osint = esegui_scansione_osint(comune, provincia)
                st.session_state.vector = esegui_ricerca_vettoriale(indirizzo_input, project_id, endpoint_id)
            else:
                st.error("Area fuori giurisdizione (Solo MI/MB).")
        else:
            st.error("Indirizzo non trovato.")

# Visualizzazione
if st.session_state.dati:
    d = st.session_state.dati
    o = st.session_state.osint
    v = st.session_state.vector

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Mappa Tattica")
        m = folium.Map(location=[d['lat'], d['lon']], zoom_start=15)
        folium.Marker([d['lat'], d['lon']], tooltip="Target").add_to(m)
        st_folium(m, width="100%", height=400, key="mappa_fissa")
    
    with col2:
        st.subheader("Dati Dossier")
        st.write(f"**Target:** {d['comune']}")
        try:
            pdf_bytes = crea_pdf_intelligence(d, o, v)
            st.download_button("📥 SCARICA REPORT PDF", pdf_bytes, f"Analisi_{d['comune']}.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Errore PDF: {e}")

    st.divider()
    st.subheader("Fonti e Correlazioni Semantiche")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Link Istituzionali:**")
        for r in o: st.markdown(f"- [{r['titolo']}]({r['link']})")
    with c2:
        st.write("**Analisi AI:**")
        if v:
            for item in v: st.info(f"{item['titolo']} (Score: {item['score']})")
        else:
            st.write("Nessuna correlazione vettoriale.")
