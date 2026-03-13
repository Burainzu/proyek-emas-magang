import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai
import json
import requests
from bs4 import BeautifulSoup

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Gold AI Analytics", page_icon="🪙", layout="wide")

# 2. INJEKSI CUSTOM CSS
st.markdown("""
<style>
    h1 { color: #FACC15 !important; font-weight: 800; letter-spacing: -1px; }
    h2, h3 { color: #E2E8F0 !important; }
    
    /* Kartu Metrik Atas */
    div[data-testid="metric-container"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Kartu Analisis AI */
    .ai-card {
        background-color: #0F172A;
        border: 1px solid #38BDF8;
        padding: 20px;
        border-radius: 10px;
        height: 100%;
        box-shadow: 0 4px 10px rgba(56, 189, 248, 0.1);
    }
    .ai-card h4 { color: #38BDF8; margin-top: 0; margin-bottom: 15px; font-size: 18px; border-bottom: 1px solid #1E293B; padding-bottom: 10px;}
    .ai-card p { color: #CBD5E1; font-size: 14px; line-height: 1.6; }
    
    /* Tombol AI */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FACC15 0%, #EAB308 100%);
        color: #0F172A;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.title("🪙 AI Gold Analytics & Prediction")
st.markdown("---")

# 3. FUNGSI MENGAMBIL BERITA (SCRAPING)
@st.cache_data(ttl=3600)
def get_market_news():
    try:
        # Mengambil data dari halaman berita logammulia.com
        url = "https://www.logammulia.com/id/news"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        # Mencari kontainer artikel berita (struktur umum HTML web berita)
        articles = soup.find_all('div', class_='news-item')[:3] # Ambil 3 berita terbaru
        
        # Fallback jika struktur web logam mulia berbeda/berubah
        if not articles:
            articles = soup.find_all('a', class_='ng-binding')[:3]
            
        for art in articles:
            title = art.text.strip().replace('\n', ' ')
            if title and len(title) > 10:
                news_list.append(title)
                
        if not news_list:
             return ["Berita harian sedang diperbarui oleh sistem Logam Mulia.", "Sentimen pasar hari ini berfokus pada kebijakan suku bunga global."]
        return news_list
    except Exception as e:
        return ["Gagal menarik berita langsung. Server Logam Mulia menolak koneksi bot.", "Gunakan analisis teknikal sebagai acuan utama hari ini."]

# 4. SIDEBAR PENGATURAN
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi Mesin")
    api_key = st.text_input("🔐 Gemini API Key", type="password")
    timeframe_option = st.selectbox("Pilih Time Frame Data:", ("Harian (1d)", "Mingguan (1wk)", "Bulanan (1mo)"))

interval_map = {"Harian (1d)": "1d", "Mingguan (1wk)": "1wk", "Bulanan (1mo)": "1mo"}
selected_interval = interval_map[timeframe_option]

# 5. FUNGSI DATA & KALKULASI MANUAL
@st.cache_data(ttl=3600)
def get_gold_data(interval):
    gold = yf.Ticker("GC=F")
    df = gold.history(period="2y", interval=interval) 
    if df.empty: return df

    df['Close_Antam_IDR'] = (df['Close'] / 31.103) * 15500 
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
    st.error("Gagal mengambil data. Periksa koneksi internet.")
else:
    latest_data = df.iloc[-1]
    
    # Menampilkan Berita Market di Atas
    st.info("📰 **Kilas Berita Pasar Hari Ini:**")
    berita = get_market_news()
    for b in berita:
        st.markdown(f"- {b}")
    st.markdown("---")
    
    # KARTU METRIK & CHART
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("XAU/USD (Dunia)", f"${latest_data['Close']:,.2f}")
    with col2: st.metric("Estimasi ANTAM", f"Rp {latest_data['Close_Antam_IDR']:,.0f}")
    with col3: st.metric("RSI (14)", f"{latest_data['RSI_14']:.2f}")
    with col4: st.metric("MACD Momentum", f"{latest_data['MACD_12_26_9']:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='XAU/USD'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='#38BDF8', width=2)))
    fig.update_layout(xaxis_rangeslider_visible=False, height=450, template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    # 6. INTEGRASI AI BERBASIS JSON & GRID SYSTEM
    st.markdown("---")
    
    if st.button("Generate Analisis AI & Sinyal Trading"):
        if not api_key:
            st.warning("⚠️ Masukkan API Key di pengaturan Sidebar sebelah kiri.")
        else:
            with st.spinner('Memproses algoritma AI...'):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    # PROMPT JSON: Memaksa AI hanya memuntahkan data mentah
                    prompt = f"""
                    Anda adalah analis kuantitatif. Evaluasi data Emas ini:
                    Harga: ${latest_data['Close']:.2f}, RSI: {latest_data['RSI_14']:.2f}, MACD: {latest_data['MACD_12_26_9']:.2f}.
                    
                    Keluarkan output HANYA dalam format JSON yang valid persis seperti struktur ini, tanpa ada teks pengantar atau penutup apapun:
                    {{
                        "rekomendasi": "BUY / SELL / HOLD",
                        "teknikal": "Tulis 2 kalimat analisis indikator teknikal dari data di atas.",
                        "fundamental": "Tulis 2 kalimat sentimen makro ekonomi yang relevan hari ini.",
                        "alasan_keputusan": "Jelaskan dengan tajam mengapa Anda memilih rekomendasi tersebut."
                    }}
                    """
                    
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    
                    # Parsing & Membersihkan output AI menjadi dictionary Python
                    raw_response = response.text.strip()
                    if raw_response.startswith("```json"):
                        raw_response = raw_response.replace("```json", "").replace("```", "").strip()
                    
                    ai_data = json.loads(raw_response)
                    
                    # REKOMENDASI UTAMA DI ATAS
                    st.markdown("<br>", unsafe_allow_html=True)
                    warna_rek = "#10B981" if "BUY" in ai_data['rekomendasi'] else "#EF4444" if "SELL" in ai_data['rekomendasi'] else "#F59E0B"
                    st.markdown(f"<h2 style='text-align: center; color: {warna_rek} !important; font-size: 40px;'>🔴 KEPUTUSAN: {ai_data['rekomendasi']}</h2>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # GRID SYSTEM: 3 KARTU BERJAJAR HORIZONTAL
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown(f"""
                        <div class="ai-card">
                            <h4>📈 Analisis Teknikal</h4>
                            <p>{ai_data['teknikal']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c2:
                        st.markdown(f"""
                        <div class="ai-card">
                            <h4>🌍 Faktor Fundamental</h4>
                            <p>{ai_data['fundamental']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c3:
                        st.markdown(f"""
                        <div class="ai-card">
                            <h4>⚖️ Dasar Keputusan</h4>
                            <p>{ai_data['alasan_keputusan']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Terjadi kesalahan saat mengurai data AI. Pastikan API key benar. Detail: {e}")