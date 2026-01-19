import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from fpdf import FPDF
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Intelligence MI-MB", layout="wide", page_icon="🛡️")

# --- MOTORE DI RICERCA OSINT ---
def esegui_scansione_osint(comune, provincia):
    headers = {'User-Agent': 'Mozilla/5.0'}
    risultati = []
    # Query limitata per evitare blocchi Google
    queries = [f'site:prefettura.interno.gov.it "{comune}" sicurezza']
    
    for q in queries:
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Cerchiamo i link nei risultati di Google
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and "url?q=" in href:
                        clean_url = href.split("url?q=")[1].split("&sa=")[0]
                        if "google.com" not in clean_url:
                            risultati.append({"titolo": "Fonte Istituzionale", "link": clean_url})
                            if len(risultati) >= 3: break # Limitiamo i risultati
        except:
            continue
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

# Usiamo lo stato della sessione per evitare che la pagina si resetti
if 'analizzato' not in st.session_state:
    st.session_state.analizzato = False

with st.sidebar:
    st.header("Ricerca Target")
    indirizzo_input = st.text_input("Inserisci Indirizzo e Comune:", "Piazza del Duomo, Milano")
    pulsante = st.button("ESEGUI ANALISI")

if pulsante:
    st.session_state.analizzato = True
    with st.spinner("Accesso ai database territoriali..."):
        geolocator = Nominatim(user_agent=f"intel_agent_{int(time.time())}")
        location = geolocator.geocode(indirizzo_input, addressdetails=True, timeout=10)

        if location:
            info = location.raw.get('address', {})
            comune = info.get('city') or info.get('town') or info.get('village') or info.get('suburb') or "Non rilevato"
            provincia = info.get('county', '')

            if any(p in provincia for p in ["Milano", "Monza"]):
                dati_finali = {
                    "indirizzo": indirizzo_input, "comune": comune, "provincia": provincia,
                    "lat": location.latitude, "lon": location.longitude
                }
                
                # Esecuzione Scansione
                risultati_osint = esegui_scansione_osint(comune, provincia)
                
                # Layout
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Mappa Tattica - {comune}")
                    m = folium.Map(location=[location.latitude, location.longitude], zoom_start=15)
                    folium.Marker([location.latitude, location.longitude], tooltip="Target").add_to(m)
                    st_folium(m, width="100%", height=400, key="map")
                
                with col2:
                    st.subheader("Dati Dossier")
                    st.write(f"**Target:** {comune}")
                    st.write(f"**Provincia:** {provincia}")
                    
                    # Generazione PDF
                    try:
                        pdf_bytes = crea_pdf_intelligence(dati_finali, risultati_osint)
                        st.download_button(
                            label="📥 SCARICA REPORT (PDF)",
                            data=pdf_bytes,
                            file_name=f"Report_{comune}.pdf",
                            mime="application/pdf",
                            key="download"
                        )
                    except Exception as e:
                        st.error(f"Errore PDF: {e}")
                
                st.divider()
                st.subheader("Fonti OSINT individuate")
                if risultati_osint:
                    for r in risultati_osint:
                        st.markdown(f"🔗 [Link Istituzionale]({r['link']})")
                else:
                    st.write("Nessun link istituzionale trovato per questo comune.")
            else:
                st.error("Il sistema opera esclusivamente sulle province di Milano e Monza Brianza.")
        else:
            st.error("Indirizzo non trovato. Riprova con più dettagli.")
