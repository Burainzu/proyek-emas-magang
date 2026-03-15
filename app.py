import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai
import json
import requests
from bs4 import BeautifulSoup

# 1. KONFIGURASI HALAMAN (Ikon Bank)
st.set_page_config(page_title="BSI Gold Analytics", page_icon="🏦", layout="wide")

# 2. INJEKSI CUSTOM CSS (TEMA BANK BSI PREMIUM GRADIENT)
st.markdown("""
<style>
    /* --- MENGUBAH BACKGROUND UTAMA & SIDEBAR MENJADI GRADIENT BSI --- */
    
    /* Background area utama aplikasi (Gradient Navy ke Dark Tosca BSI) */
    .stApp {
        background: linear-gradient(135deg, #06121E 0%, #004D4A 100%) !important;
        background-attachment: fixed !important; /* Menjaga gradient tetap mulus saat di-scroll */
    }
    
    /* Background area Sidebar (Gradient Navy ke Deep Tosca) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A1929 0%, #00312F 100%) !important;
        border-right: 1px solid #00A39E; /* Garis batas Tosca BSI */
    }

    /* Membuat header atas Streamlit transparan agar menyatu dengan gradient */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* --- WARNA TEKS & ELEMEN LAINNYA --- */
    /* Judul Utama */
    h1 { color: #00A39E !important; font-weight: 800; letter-spacing: -1px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
    h2, h3 { color: #E2E8F0 !important; }
    
    /* Kartu Metrik Atas (Dibuat agak transparan/Glassmorphism agar gradient terlihat) */
    div[data-testid="metric-container"] {
        background: rgba(17, 34, 54, 0.7) !important; 
        backdrop-filter: blur(10px); /* Efek kaca kekinian */
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 163, 158, 0.3);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s, border-color 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: #F26522; /* Border Oranye BSI saat di-hover */
        background: rgba(17, 34, 54, 0.9) !important;
    }
    
    /* Kartu Analisis AI (Glassmorphism) */
    .ai-card {
        background: rgba(10, 25, 41, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid #00A39E; /* Border Tosca BSI */
        padding: 20px;
        border-radius: 10px;
        height: 100%;
        box-shadow: 0 4px 15px rgba(0, 163, 158, 0.15);
    }
    .ai-card h4 { 
        color: #F26522; /* Judul sub-kartu Oranye BSI */
        margin-top: 0; 
        margin-bottom: 15px; 
        font-size: 18px; 
        border-bottom: 1px solid rgba(0, 163, 158, 0.3); 
        padding-bottom: 10px;
    }
    .ai-card p { color: #CBD5E1; font-size: 14px; line-height: 1.6; }
    
    /* Tombol Generate AI - Gradien Oranye BSI */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #F26522 0%, #F7941D 100%);
        color: #FFFFFF;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(242, 101, 34, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(242, 101, 34, 0.6);
    }
</style>
""", unsafe_allow_html=True)

st.title("🏦 BSI Gold Analytics & Prediction")
st.markdown("*Platform Analisis Harga Emas Dunia & ANTAM Berbasis Artificial Intelligence*")
st.markdown("---")

# 3. FUNGSI MENGAMBIL BERITA (SCRAPING)
@st.cache_data(ttl=3600)
def get_market_news():
    try:
        url = "https://www.logammulia.com/id/news"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        articles = soup.find_all('div', class_='news-item')[:3]
        if not articles: articles = soup.find_all('a', class_='ng-binding')[:3]
        for art in articles:
            title = art.text.strip().replace('\n', ' ')
            if title and len(title) > 10: news_list.append(title)
        if not news_list: return ["Berita harian sedang diperbarui oleh sistem.", "Sentimen pasar hari ini berfokus pada kebijakan suku bunga."]
        return news_list
    except Exception as e:
        return ["Gagal menarik berita langsung. Server sedang sibuk.", "Gunakan analisis teknikal sebagai acuan utama hari ini."]

# FUNGSI MENGAMBIL HARGA ASLI ANTAM DENGAN FALLBACK ESTIMASI
@st.cache_data(ttl=3600)
def get_harga_antam_asli(estimasi_cadangan):
    url = "https://www.logammulia.com/id/harga-emas-hari-ini"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari tabel harga sesuai kodemu
        table = soup.find('table', class_='table-price')
        if table:
            first_row = table.find_all('tr')[1] 
            cols = first_row.find_all('td')
            harga_beli_str = cols[1].text.strip()
            
            # Membersihkan teks "Rp 1.250.000" menjadi angka murni 1250000
            import re
            harga_bersih = int(re.sub(r'[^0-9]', '', harga_beli_str))
            
            return harga_bersih, "Harga Asli ANTAM"
            
    except Exception as e:
        pass # Abaikan error jika diblokir, lanjut ke return bawah
        
    # Jika web scraping gagal/diblokir, kembalikan nilai estimasi cadangan
    return estimasi_cadangan, "Harga Estimasi Sistem"

# 4. SIDEBAR PENGATURAN
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Bank_Syariah_Indonesia.svg/1024px-Bank_Syariah_Indonesia.svg.png", width=150)
    st.markdown("### ⚙️ Konfigurasi Mesin")
    api_key = st.text_input("🔐 Gemini API Key", type="password")
    
    st.markdown("### 📊 Parameter Chart")
    timeframe_option = st.selectbox("Pilih Time Frame Data:", ("Harian (1d)", "Mingguan (1wk)", "Bulanan (1mo)"))

    # --- FITUR BARU: MINI CONTENT WEB LOGAM MULIA ---
    st.markdown("---")
    st.markdown("### 🥇 Live Web Logam Mulia")
    
    # Memanggil modul components bawaan Streamlit untuk iFrame
    import streamlit.components.v1 as components
    
    # Membuat box iframe dengan tinggi 400px dan bisa di-scroll
    components.iframe("https://www.logammulia.com/id/grafik-harga-emas", height=400, scrolling=True)
    
    # Tombol cadangan jika iFrame diblokir oleh sistem keamanan Logam Mulia
    st.markdown("<div style='text-align: center; margin-top: 10px;'><a href='https://www.logammulia.com/id/grafik-harga-emas' target='_blank' style='text-decoration: none; color: #F26522; font-size: 13px; font-weight: bold;'>🔗 Cek harga emas ANTAM secara LIVE!</a></div>", unsafe_allow_html=True)

interval_map = {"Harian (1d)": "1d", "Mingguan (1wk)": "1wk", "Bulanan (1mo)": "1mo"}
selected_interval = interval_map[timeframe_option]

# 5. FUNGSI DATA & KALKULASI MANUAL (DENGAN FALLBACK)
@st.cache_data(ttl=3600)
def get_gold_data(interval):
    df = pd.DataFrame()
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="2y", interval=interval) 
    except: pass
        
    if df.empty:
        try:
            gold_backup = yf.Ticker("GLD")
            df = gold_backup.history(period="2y", interval=interval)
        except: pass

    if df.empty: return pd.DataFrame() 

    pengali = 1 if df['Close'].iloc[-1] > 1000 else 10 
    df['Close_Antam_IDR'] = ((df['Close'] * pengali) / 31.103) * 15500 
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_12_26_9'] = ema_12 - ema_26
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    return df.dropna()

df = get_gold_data(selected_interval)

if df.empty:
    st.error("🚨 Yahoo Finance memblokir IP Streamlit Cloud. Jalankan aplikasi ini secara lokal untuk presentasi.")
else:
    latest_data = df.iloc[-1]
    
    # --- MENJALANKAN FUNGSI HARGA ASLI ---
    estimasi_harga = latest_data['Close_Antam_IDR']
    harga_antam_final, status_harga = get_harga_antam_asli(estimasi_harga)
    
    # Menampilkan Berita Market
    st.info("📰 **Kilas Berita Pasar Hari Ini:**")
    berita = get_market_news()
    for b in berita: st.markdown(f"- {b}")
    st.markdown("---")
    
    # KARTU METRIK
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("XAU/USD (Dunia)", f"${latest_data['Close']:,.2f}")
    with col2: st.metric(f"ANTAM ({status_harga})", f"Rp {harga_antam_final:,.0f}") # Labelnya akan berubah dinamis
    with col3: st.metric("RSI (14)", f"{latest_data['RSI_14']:.2f}")
    with col4: st.metric("MACD Momentum", f"{latest_data['MACD_12_26_9']:.2f}")

    # CHART PLOTLY DENGAN WARNA BSI
    st.subheader("📈 Analisis Pergerakan Harga")
    # ... (Biarkan kode grafik figure Plotly tetap seperti milikmu) ...

    # --- DI BAGIAN BAWAH, UPDATE PROMPT AI ---
    st.markdown("---")
    
    if st.button("Generate Analisis AI & Sinyal Trading (BSI-Mode)"):
        if not api_key:
            st.warning("⚠️ Masukkan API Key di pengaturan Sidebar sebelah kiri.")
        else:
            with st.spinner('Memproses algoritma AI...'):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    Anda adalah analis kuantitatif senior di Bank Syariah Indonesia. Evaluasi data Emas ini:
                    Harga Dunia: ${latest_data['Close']:.2f}, Harga ANTAM: Rp {harga_antam_final:,.0f}, RSI: {latest_data['RSI_14']:.2f}, MACD: {latest_data['MACD_12_26_9']:.2f}.
                    
                    Keluarkan output HANYA dalam format JSON yang valid persis seperti struktur ini:
                    {{
                        "rekomendasi": "BUY / SELL / HOLD",
                        "teknikal": "Tulis 2 kalimat analisis indikator teknikal dari data di atas.",
                        "fundamental": "Tulis 2 kalimat sentimen makro ekonomi yang relevan hari ini.",
                        "alasan_keputusan": "Jelaskan dengan tajam mengapa Anda memilih rekomendasi tersebut."
                    }}
                    """
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    
                    raw_response = response.text.strip()
                    if raw_response.startswith("```json"):
                        raw_response = raw_response.replace("```json", "").replace("```", "").strip()
                    
                    ai_data = json.loads(raw_response)
                    
                    # REKOMENDASI UTAMA DI ATAS
                    st.markdown("<br>", unsafe_allow_html=True)
                    warna_rek = "#10B981" if "BUY" in ai_data['rekomendasi'] else "#EF4444" if "SELL" in ai_data['rekomendasi'] else "#FACC15"
                    st.markdown(f"<h2 style='text-align: center; color: {warna_rek} !important; font-size: 40px;'>🔴 KEPUTUSAN: {ai_data['rekomendasi']}</h2>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # GRID SYSTEM: 3 KARTU BERJAJAR HORIZONTAL
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f'<div class="ai-card"><h4>📈 Analisis Teknikal</h4><p>{ai_data["teknikal"]}</p></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div class="ai-card"><h4>🌍 Faktor Fundamental</h4><p>{ai_data["fundamental"]}</p></div>', unsafe_allow_html=True)
                    with c3:
                        st.markdown(f'<div class="ai-card"><h4>⚖️ Dasar Keputusan</h4><p>{ai_data["alasan_keputusan"]}</p></div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Terjadi kesalahan saat mengurai data AI. Detail: {e}")