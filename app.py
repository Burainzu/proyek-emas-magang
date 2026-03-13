import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai

# 1. KONFIGURASI HALAMAN (Harus paling atas)
st.set_page_config(page_title="Gold AI Analytics", page_icon="🪙", layout="wide")

# 2. INJEKSI CUSTOM CSS (Desain UI Modern)
st.markdown("""
<style>
    /* Mengubah font header menjadi warna Emas elegan */
    h1 {
        color: #FACC15 !important;
        font-weight: 800;
        letter-spacing: -1px;
    }
    h2, h3 {
        color: #E2E8F0 !important;
    }
    /* Mempercantik kotak Metrik (Harga, RSI, dll) menjadi bentuk Kartu */
    div[data-testid="metric-container"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: #FACC15;
    }
    /* Mempercantik tombol AI */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FACC15 0%, #EAB308 100%);
        color: #0F172A;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        box-shadow: 0 4px 15px rgba(250, 204, 21, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(250, 204, 21, 0.5);
    }
    /* Memperhalus garis pemisah */
    hr {
        border-color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# 3. HEADER & JUDUL UTAMA
st.title("🪙 AI Gold Analytics & Prediction")
st.markdown("*Platform Analisis Harga Emas Dunia & ANTAM Berbasis Artificial Intelligence*")
st.markdown("---")

# 4. SIDEBAR PENGATURAN MODERN
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/825/825583.png", width=80) # Ikon emas
    st.markdown("### ⚙️ Konfigurasi Mesin")
    api_key = st.text_input("🔐 Gemini API Key", type="password", help="Masukkan API Key yang aktif")
    
    st.markdown("### 📊 Parameter Chart")
    timeframe_option = st.selectbox(
        "Pilih Time Frame Data:",
        ("Harian (1d)", "Mingguan (1wk)", "Bulanan (1mo)")
    )

interval_map = {"Harian (1d)": "1d", "Mingguan (1wk)": "1wk", "Bulanan (1mo)": "1mo"}
selected_interval = interval_map[timeframe_option]

# 5. FUNGSI DATA & KALKULASI MANUAL (TANPA PANDAS-TA)
@st.cache_data(ttl=3600)
def get_gold_data(interval):
    gold = yf.Ticker("GC=F")
    df = gold.history(period="2y", interval=interval) 
    
    if df.empty:
        return df

    # Estimasi Harga ANTAM
    df['Close_Antam_IDR'] = (df['Close'] / 31.103) * 15500 
    
    # Simple Moving Average (SMA)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # MACD
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_12_26_9'] = ema_12 - ema_26
    
    # RSI
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
    # 6. KARTU METRIK DASHBOARD (UI BARU)
    latest_data = df.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="XAU/USD (Dunia)", value=f"${latest_data['Close']:,.2f}")
    with col2:
        st.metric(label="Estimasi ANTAM", value=f"Rp {latest_data['Close_Antam_IDR']:,.0f}")
    with col3:
        st.metric(label="RSI (14)", value=f"{latest_data['RSI_14']:.2f}", 
                  delta="Overbought" if latest_data['RSI_14'] > 70 else "Oversold" if latest_data['RSI_14'] < 30 else "Netral",
                  delta_color="inverse" if latest_data['RSI_14'] > 70 else "normal")
    with col4:
        st.metric(label="MACD Momentum", value=f"{latest_data['MACD_12_26_9']:.2f}",
                  delta="Bullish (Naik)" if latest_data['MACD_12_26_9'] > 0 else "Bearish (Turun)")
        
    st.markdown("---")

    # 7. CHART PLOTLY YANG LEBIH CLEAN
    st.subheader("📈 Analisis Pergerakan Harga")
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='XAU/USD'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20 (Cepat)', line=dict(color='#38BDF8', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50 (Lambat)', line=dict(color='#F472B6', width=2)))
    
    fig.update_layout(
        xaxis_rangeslider_visible=False, 
        height=500, 
        template="plotly_dark",
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)', # Background transparan menyatu dengan tema web
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) # Legenda rapi di atas
    )
    st.plotly_chart(fig, use_container_width=True)

    # 8. INTEGRASI AI YANG LEBIH RAPI
    st.markdown("---")
    st.subheader("🤖 AI Analytics Engine")
    st.info("Mesin AI akan membaca indikator teknikal terkini dan merangkumnya menjadi rekomendasi eksekusi pasar.")
    
    if st.button("Generate Rekomendasi (Gemini-2.5-Flash)"):
        if not api_key:
            st.warning("⚠️ Masukkan API Key di pengaturan Sidebar sebelah kiri.")
        else:
            with st.spinner('Menghubungkan ke satelit data & mesin Gemini AI...'):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    Anda adalah analis finansial Wall Street. 
                    Data teknikal Emas saat ini ({timeframe_option}):
                    - Harga Emas: ${latest_data['Close']:.2f}
                    - Estimasi ANTAM: Rp {latest_data['Close_Antam_IDR']:,.0f}
                    - RSI: {latest_data['RSI_14']:.2f}
                    - MACD: {latest_data['MACD_12_26_9']:.2f}
                    
                    Tugas Anda:
                    1. Berikan resume teknikal dan fundamental singkat.
                    2. Berikan rekomendasi tegas: BUY, SELL, atau HOLD untuk emas ANTAM.
                    
                    Gunakan bahasa Indonesia yang profesional, tebal pada kata kunci, dan rapi.
                    """
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    # Menampilkan hasil di dalam kotak yang elegan
                    with st.container():
                        st.success("✅ Analisis Berhasil Diperbarui")
                        st.markdown(f"> {response.text}")
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memanggil AI: Cek kembali API Key Anda. Detail error: {e}")