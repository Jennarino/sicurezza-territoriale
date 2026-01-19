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
st.set_page_config(page_title="Intelligence Territoriale MI-MB", layout="wide", page_icon="🛡️")

# --- MOTORE DI RICERCA OSINT ---
def esegui_scansione_osint(comune, provincia):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    risultati = []
    
    # Query mirate per sicurezza e ordine pubblico
    queries = [
        f'site:prefettura.interno.gov.it "{comune}" sicurezza',
        f'site:questure.poliziadistato.it "{comune}" controlli',
        f'"{comune}" cronaca nera sicurezza 2025'
    ]
    
    for q in queries:
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for g in soup.find_all('div', class_='tF2Cxc')[:2]: # Prendi i primi 2 da ogni query
                    titolo = g.find('h3').text if g.find('h3') else "Dettaglio Fonte"
                    link = g.find('a')['href'] if g.find('a') else ""
                    risultati.append({"titolo": titolo, "link": link})
            time.sleep(1) # Delay anti-blocco
        except:
            pass
    return risultati

# --- GENERATORE REPORT PDF ---
class IntelligencePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.set_text_color(50, 50, 150)
        self.cell(0, 10, "STRETTAMENTE RISERVATO - DOSSIER SICUREZZA MI-MB", border=False, ln=True, align="R")
        self.ln(5)

def crea_pdf_intelligence(dati, osint):
    pdf = IntelligencePDF()
    pdf.add_page()
    
    # Titolo
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 15, f"ANALISI TERRITORIALE: {dati['comune'].upper()}", ln=True, align="L")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 5, f"Data Generazione: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)

    # Sezione 1: Inquadramento
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 1. INQUADRAMENTO GEOGRAFICO E AUTORITA'", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(2)
    corpo_1 = (f"Target: {dati['indirizzo']}\n"
               f"Provincia: {dati['provincia']}\n"
               f"Competenza Primaria: Prefettura di {'Milano' if 'Milano' in dati['provincia'] else 'Monza e Brianza'}\n"
               f"Coordinate Target: {dati['lat']}, {dati['lon']}")
    pdf.multi_cell(0, 8, corpo_1)

    # Sezione 2: Analisi OSINT
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 2. RILEVAZIONI DA FONTI APERTE (OSINT)", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(2)
    if osint:
        for item in osint:
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(0, 7, f"• {item['titolo']}")
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(0, 5, f"  URL: {item['link'][:80]}...", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
    else:
        pdf.cell(0, 10, "Nessuna criticità immediata rilevata nelle ultime scansioni.", ln=True)

    # Sezione 3: Valutazione Argomentata
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 3. VALUTAZIONE SINTETICA DELL'ANALISTA", ln=True, fill=True)
    pdf.set_font("Arial", "I", 11)
    pdf.ln(2)
    valutazione = (f"L'area di {dati['comune']} ricade in un quadrante monitorato per 'sicurezza partecipata'. "
                   "La densità di presidi istituzionali è coerente con il profilo di rischio provinciale. "
                   "Si raccomanda la verifica delle ordinanze sindacali vigenti per restrizioni specifiche.")
    pdf.multi_cell(0, 8, valutazione)

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- INTERFACCIA STREAMLIT ---
st.title("🛡️ Intelligence Sicurezza Territoriale")
st.markdown("### Focus Province: Milano, Monza e della Brianza")

with st.sidebar:
    st.header("Ricerca Target")
    indirizzo = st.text_input("Inserisci Indirizzo e Comune:", "Via Dante, Sesto San Giovanni")
    st.info("Esempio: Via Roma 1, Monza")
    pulsante = st.button("ESEGUI SCANSIONE")

if pulsante:
    with st.spinner("Interrogazione database istituzionali in corso..."):
        geolocator = Nominatim(user_agent=f"intel_agent_{int(time.time())}")
        location = geolocator.geocode(indirizzo, addressdetails=True, timeout=10)

        if location:
            info = location.raw['address']
            comune = info.get('city') or info.get('town') or info.get('village') or info.get('suburb')
            provincia = info.get('county', '')

            if any(p in provincia for p in ["Milano", "Monza"]):
                dati_finali = {
                    "indirizzo": indirizzo, "comune": comune, "provincia": provincia,
                    "lat": location.latitude, "lon": location.longitude
                }
                
                # Scansione Notizie
                risultati_osint = esegui_scansione_osint(comune, provincia)
                
                # Layout Dashboard
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Mappa Tattica - {comune}")
                    m = folium.Map(location=[location.latitude, location.longitude], zoom_start=15)
                    folium.Marker([location.latitude, location.longitude], tooltip="Target").add_to(m)
                    st_folium(m, width="100%", height=400)
                
                with col2:
                    st.subheader("Highlight Intelligence")
                    st.write(f"**Comune:** {comune}")
                    st.write(f"**Provincia:** {provincia}")
                    st.write(f"**Fonti individuate:** {len(risultati_osint)}")
                    
                    pdf_data = crea_pdf_intelligence(dati_finali, risultati_osint)
                    st.download_button(
                        label="📥 SCARICA REPORT COMPLETO (PDF)",
                        data=pdf_data,
                        file_name=f"Intelligence_{comune}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                
                st.divider()
                st.subheader("Dettaglio Riscontri OSINT")
                for r in risultati_osint:
                    st.markdown(f"🔗 [{r['titolo']}]({r['link']})")
            else:
                st.error("Errore: Il target si trova fuori dalle province di Milano e Monza Brianza.")
        else:
            st.error("Indirizzo non identificato. Riprova con maggiore precisione.")        # Filtro geografico MI e MB
        aree_abilitate = ["Milano", "Monza e della Brianza", "Monza e Brianza"]
        if not any(area in provincia for area in aree_abilitate):
            return f"Fuori zona (Rilevato: {provincia})"

        return {
            "indirizzo": indirizzo,
            "comune": comune,
            "provincia": provincia,
            "lat": location.latitude,
            "lon": location.longitude,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    except Exception as e:
        return f"Errore tecnico: {e}"

def genera_pdf_professionale(dati):
    pdf = FPDF()
    pdf.add_page()

    # Intestazione Intelligence
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(20, 40, 80) # Blu scuro istituzionale
    pdf.cell(0, 15, "DOSSIER SICUREZZA TERRITORIALE", ln=True, align="C")

    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(100)
    pdf.cell(0, 5, f"RIF: {dati['data']} | AMBITO: {dati['provincia'].upper()}", ln=True, align="C")
    pdf.ln(10)

    # Blocco Target
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0)
    pdf.cell(0, 10, f" 1. LOCALIZZAZIONE TARGET", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(3)
    testo_loc = (f"Indirizzo: {dati['indirizzo']}\n"
                 f"Comune: {dati['comune']}\n"
                 f"Provincia: {dati['provincia']}\n"
                 f"Coordinate: {dati['lat']}, {dati['lon']}")
    pdf.multi_cell(0, 8, testo_loc)

    # Blocco Analisi Istituzionale
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 2. QUADRO AUTORITÀ COMPETENTI", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    prefettura = "Milano (C.so Monforte/Via Vivaio)" if "Milano" in dati['provincia'] else "Monza (Via della Signora)"
    testo_enti = (f"- Prefettura di riferimento: {prefettura}\n"
                  f"- Area Questura: Provinciale {dati['provincia']}\n"
                  f"- Vigilanza Urbana: Comando Polizia Locale di {dati['comune']}")
    pdf.multi_cell(0, 8, testo_enti)

    # Blocco Valutazione Argomentata
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 3. ANALISI PRELIMINARE OSINT", ln=True, fill=True)
    pdf.set_font("Arial", "I", 11)
    valutazione = (f"L'area del comune di {dati['comune']} è soggetta alle direttive del Comitato Provinciale "
                   "per l'Ordine e la Sicurezza Pubblica. Si segnala il monitoraggio attivo tramite sistemi "
                   "di videosorveglianza integrata e protocolli di sicurezza partecipata.")
    pdf.multi_cell(0, 8, valutazione)

    nome_file = f"Report_Intelligence_{dati['comune']}.pdf"
    pdf.output(nome_file)
    return nome_file

print("✅ Sistema di Intelligence configurato correttamente.")

# --- CONFIGURAZIONE TARGET ---
indirizzo_target = "Piazza del Duomo, Milano" # Inserisci l'indirizzo desiderato qui
# -----------------------------

risultato = analizzatore_intelligence(indirizzo_target)

if isinstance(risultato, dict):
    # 1. Generazione Mappa
    print(f"🌍 Generazione mappa tattica per {risultato['comune']}...")
    mappa = folium.Map(location=[risultato['lat'], risultato['lon']], zoom_start=16, tiles="OpenStreetMap")
    folium.Marker(
        [risultato['lat'], risultato['lon']],
        popup=indirizzo_target,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(mappa)

    # 2. Creazione PDF
    file_pdf = genera_pdf_professionale(risultato)
    print(f"📄 Report Intelligence creato con successo: {file_pdf}")
    print("📂 Puoi scaricarlo cliccando sull'icona della cartella a sinistra.")

    display(mappa)
else:
    print(f"⚠️ Attenzione: {risultato}")
