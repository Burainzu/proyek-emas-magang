import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Analisis Emas Cerdas", layout="wide")
st.title("📈 Prediksi & Analisis Harga Emas (XAU/USD & Estimasi ANTAM)")

# 2. SIDEBAR UNTUK PENGATURAN USER
st.sidebar.header("Pengaturan Analisis")
api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")

# Pilihan Timeframe
timeframe_option = st.sidebar.selectbox(
    "Pilih Time Frame:",
    ("Harian (1d)", "Mingguan (1wk)", "Bulanan (1mo)")
)

# Mapping pilihan UI ke format yfinance
interval_map = {"Harian (1d)": "1d", "Mingguan (1wk)": "1wk", "Bulanan (1mo)": "1mo"}
selected_interval = interval_map[timeframe_option]

# 3. FUNGSI MENGAMBIL DATA EMAS DUNIA & ESTIMASI ANTAM
@st.cache_data(ttl=3600)
def get_gold_data(interval):
    gold = yf.Ticker("GC=F")
    df = gold.history(period="2y", interval=interval) 
    
    if df.empty:
        return df

    # Estimasi Harga ANTAM
    df['Close_Antam_IDR'] = (df['Close'] / 31.103) * 15500 
    
    # --- KALKULASI INDIKATOR MANUAL (TANPA PANDAS-TA) ---
    
    # 1. Simple Moving Average (SMA)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # 2. MACD (Moving Average Convergence Divergence)
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_12_26_9'] = ema_12 - ema_26
    
    # 3. RSI (Relative Strength Index)
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
    # 5. MENAMPILKAN GRAFIK INTERAKTIF (PLOTLY)
    st.subheader(f"Grafik Pergerakan Harga Emas Dunia ({timeframe_option})")
    
    fig = go.Figure()
    # Candlestick chart
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Harga (USD)'))
    # Garis Moving Average
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='orange')))
    
    fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # 6. INTEGRASI AI UNTUK ANALISIS & REKOMENDASI (RESUME MENDETAIL)
    st.markdown("---")
    st.subheader("🧠 Analisis & Rekomendasi AI")
    
    if st.button("Mulai Analisis AI Sekarang"):
        if not api_key:
            st.warning("⚠️ Silakan masukkan API Key Gemini di menu sebelah kiri terlebih dahulu.")
        else:
            with st.spinner('AI sedang menganalisis data pasar dan indikator teknikal...'):
                try:
                    # Ambil data baris paling terakhir (hari/minggu/bulan ini)
                    latest_data = df.iloc[-1]
                    harga_usd = latest_data['Close']
                    harga_antam = latest_data['Close_Antam_IDR']
                    rsi_val = latest_data['RSI_14']
                    macd_val = latest_data['MACD_12_26_9']
                    
                    # Konfigurasi AI dengan library baru
                    client = genai.Client(api_key=api_key)
                    
                    # Menyusun Prompt (Menyuntikkan data real-time ke AI)
                    prompt = f"""
                    Anda adalah analis komoditas dan finansial senior. Berikan analisis teknikal dan fundamental 
                    mengenai prospek harga emas saat ini.
                    
                    Data teknikal saat ini (Timeframe: {timeframe_option}):
                    - Harga Emas Dunia: ${harga_usd:.2f} per Troy Ounce
                    - Estimasi Harga Emas ANTAM: Rp {harga_antam:,.0f} per Gram
                    - Indikator RSI (14): {rsi_val:.2f} (Keterangan: >70 Overbought, <30 Oversold)
                    - Indikator MACD: {macd_val:.2f}
                    
                    Tugas Anda:
                    1. Berikan resume analisis teknikal singkat dari data di atas.
                    2. Berikan narasi fundamental ekonomi makro singkat yang umumnya mempengaruhi harga emas saat ini.
                    3. Berikan rekomendasi tegas: BUY, SELL, atau HOLD untuk Emas ANTAM hari ini dan kedepannya, beserta alasan logisnya.
                    
                    Gunakan bahasa Indonesia yang profesional, formal, namun mudah dipahami. Gunakan format markdown (bulleting dan bold).
                    """
                    
                    # Memanggil model yang valid dari daftar CMD-mu
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    st.success("Analisis Selesai!")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memanggil AI: {e}")