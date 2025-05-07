import streamlit as st
import pandas as pd
from binance.client import Client
from datetime import datetime
import pytz
import time

# Configuração
api_key = "fKgCRTDFr9xyDHCWkSTx1DIJITjTVR8IgAh3UJvWvZfkeHbRdCbts3uW64z3tELB"
api_secret = "eyMfdT3CbS1JiTGrKnu3fzG6sVcnRwklE3598s4RigmPeFqSSwesdkC74Ni4N5ux"
client = Client(api_key, api_secret)

def get_custom_utc():
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    utc_decrescente = 12 - agora.hour - (1 if agora.minute >= 30 else 0)
    return f"UTC+{utc_decrescente} (Binance)"

def get_top_5_high_volume_gainers():
    try:
        # Pega top 50 ativos por volume 24h
        tickers = client.get_ticker()
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        top_volume = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)[:50]
        
        data = []
        for pair in top_volume:
            try:
                # Filtra apenas ativos em alta (>1%)
                if float(pair['priceChangePercent']) <= 1:
                    continue
                    
                klines = client.get_klines(symbol=pair['symbol'], interval='5m', limit=2)
                if len(klines) < 2:
                    continue
                
                vol_now = float(klines[-1][5])
                vol_prev = float(klines[-2][5])
                vol_change = ((vol_now - vol_prev)/vol_prev)*100 if vol_prev > 0 else 0
                
                if vol_change >= 50:  # Volume crescente
                    data.append({
                        'Ativo': pair['symbol'],
                        'Preço': float(pair['lastPrice']),
                        'Δ Preço %': float(pair['priceChangePercent']),
                        'Δ Volume %': vol_change,
                        'Direção': 'LONG'
                    })
                    if len(data) >= 5:  # Limita a 5 ativos
                        break
                        
            except Exception as e:
                continue
                
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return pd.DataFrame()

# Interface
st.title("📈 Top 5 em Alta - Binance")
st.subheader(f"⏰ {get_custom_utc()} | 🕒 {datetime.now().strftime('%H:%M:%S')}")

df = get_top_5_high_volume_gainers()
if not df.empty:
    st.dataframe(
        df.style.applymap(
            lambda x: 'background-color: #d4edda',
            subset=['Direção']
        ).format({
            'Preço': '{:.6f}',
            'Δ Preço %': '{:.2f}%',
            'Δ Volume %': '{:.2f}%'
        }),
        hide_index=True
    )
    
    for _, row in df.iterrows():
        if row['Δ Volume %'] >= 100:
            st.success(f"🚀 {row['Ativo']} | {row['Preço']:.6f} (+{row['Δ Preço %']:.2f}%)")
else:
    st.warning("Aguardando oportunidades...")

time.sleep(15)  # Atualização mais rápida (15 segundos)
st.rerun()