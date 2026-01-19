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
    # Query mirata sui domini istituzionali
    queries = [f'site:prefettura.interno.gov.it "{comune}" sicurezza']
    
    for q in queries:
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                links = soup.find_all('a')
                for link in links[:5]:
                    href = link.get('href')
                    if href and "url?q=" in href:
                        clean_url = href.split("url?q=")[1].split("&sa=")[0]
                        if "google.com" not in clean_url:
                            risultati.append({"titolo": "Fonte Istituzionale/Prefettura", "link": clean_url})
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
    
    # Titolo principale
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 15, f"ANALISI SICUREZZA: {dati['comune'].upper()}", ln=True)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 5, f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)

    # Blocco 1: Localizzazione
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 1. INQUADRAMENTO TERRITORIALE", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)
    pdf.multi_cell(0, 8, f"Target: {dati['indirizzo']}\nComune: {dati['comune']}\nProvincia: {dati['provincia']}\nCoordinate: {dati['lat']}, {dati['lon']}")

    # Blocco 2: Riscontri OSINT
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 2. RISCONTRI DA FONTI APERTE", ln=True, fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)
    if osint:
        for item in osint:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 7, f"- {item['titolo']}")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"  Fonte: {item['link'][:70]}...", ln=True)
            pdf.ln(2)
    else:
        pdf.cell(0, 10, "Nessun dato critico rilevato nelle scansioni rapide.", ln=True)

    # Blocco 3: Valutazione
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, " 3. VALUTAZIONE SINTETICA", ln=True, fill=True)
    pdf.set_font("Helvetica", "I", 11)
    pdf.ln(2)
    valutazione = (f"Il territorio di {dati['comune']} e' soggetto al coordinamento della Prefettura di riferimento. "
                   "Si riscontra una presenza strutturata di forze dell'ordine e sistemi di controllo urbano.")
    pdf.multi_cell(0, 8, valutazione)

    pdf_bytes = pdf.output() 
    return bytes(pdf_bytes)

# --- INTERFACCIA STREAMLIT ---
st.title("🛡️ Intelligence Sicurezza Territoriale")
st.markdown("### Analisi dedicata Province di Milano e Monza-Brianza")

with st.sidebar:
    st.header("Ricerca Target")
    indirizzo_input = st.text_input("Inserisci Indirizzo e Comune:", "Piazza del Duomo, Milano")
    pulsante = st.button("ESEGUI ANALISI")

if pulsante:
    with st.spinner("Accesso ai database territoriali..."):
        # Geolocalizzazione
        geolocator = Nominatim(user_agent=f"intel_app_{int(time.time())}")
        location = geolocator.geocode(indirizzo_input, addressdetails=True, timeout=10)

        if location:
            info = location.raw['address']
            comune = info.get('city') or info.get('town') or info.get('village') or info.get('suburb') or "Non rilevato"
            provincia = info.get('county', '')

            # Controllo aree MI e MB
            if any(p in provincia for p in ["Milano", "Monza"]):
                dati_finali = {
                    "indirizzo": indirizzo_input, "comune": comune, "provincia": provincia,
                    "lat": location.latitude, "lon": location.longitude
                }
                
                # Ricerca Notizie
                risultati_osint = esegui_scansione_osint(comune, provincia)
                
                # Visualizzazione
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Mappa Tattica - {comune}")
                    m = folium.Map(location=[location.latitude, location.longitude], zoom_start=15)
                    folium.Marker([location.latitude, location.longitude], tooltip="Target").add_to(m)
                    st_folium(m, width="100%", height=400)
                
                with col2:
                    st.subheader("Dati Dossier")
                    st.write(f"**Target:** {comune}")
                    st.write(f"**Provincia:** {provincia}")
                    
                    # Chiama la funzione e ottieni i byte
                    pdf_data = crea_pdf_intelligence(dati_finali, risultati_osint)
                    
                    # Passa i byte direttamente al pulsante
                    st.download_button(
                        label="📥 SCARICA REPORT (PDF)",
                        data=pdf_data,
                        file_name=f"Report_{comune}.pdf",
                        mime="application/pdf"
                    )
                
                st.divider()
                st.subheader("Fonti OSINT individuate")
                for r in risultati_osint:
                    st.markdown(f"🔗 [Link Istituzionale]({r['link']})")
            else:
                st.error("Il sistema opera esclusivamente sulle province di Milano e Monza Brianza.")
        else:
            st.error("Indirizzo non trovato. Riprova inserendo Comune e Provincia.")
