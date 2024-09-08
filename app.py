import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.grid import grid

def build_sidebar():
    st.image('customcolor_logo_transparent_background.png')
    ticker_list = pd.read_csv("tickers_ibra.csv", index_col=0)
    tickers = st.multiselect(label="Selecione as Empresas", options=ticker_list, placeholder='Códigos')
    tickers = [t+".SA" for t in tickers]
    start_date = st.date_input("De", format="DD/MM/YYYY", value=datetime(2023,1,2))
    end_date = st.date_input("Até", format="DD/MM/YYYY",value=datetime.today())

    if tickers:
        prices = yf.download(tickers, start=start_date, end=end_date)["Adj Close"]
        if len(tickers) == 1:
            prices = prices.to_frame()
            prices.columns = [tickers[0].rstrip(".SA")]
                    
        prices.columns = prices.columns.str.rstrip(".SA")
        
        # Verificação dos dados do IBOV
        try:
            ibov_data = yf.download("^BVSP", start=start_date, end=end_date)["Adj Close"]
            if ibov_data.empty:
                st.error("Erro ao baixar dados do IBOV. Verifique se os dados estão disponíveis.")
                return tickers, None
            else:
                prices['IBOV'] = ibov_data
                return tickers, prices
        except Exception as e:
            st.error(f"Ocorreu um erro ao baixar dados do IBOV: {e}")
            return tickers, None
    return None, None

def build_main(tickers, prices):
    if prices is None:
        st.error("Não foi possível obter os dados necessários para construir a visualização.")
        return

    weights = np.ones(len(tickers))/len(tickers)
    prices['portifolio'] = prices.drop("IBOV", axis=1) @ weights
    norm_prices = 100 * prices / prices.iloc[0]
    returns = prices.pct_change()[1:]
    vols = returns.std()*np.sqrt(252)
    rets = (norm_prices.iloc[-1] - 100) / 100

    mygrid = grid(5 ,5 ,5 ,5 ,5 , 5, vertical_align="top")
    for t in prices.columns:
        c = mygrid.container(border=True)
        c.subheader(t, divider="red")
        colA, colB, colC = c.columns(3)
        if t == 'portifolio':
            colA.image('https://raw.githubusercontent.com/codigoquant/stock_dashboard/c9f45ca0748dd827fc13e29ee51a941a74dfad95/images/pie-chart-dollar-svgrepo-com.svg')
        elif t == 'IBOV':
            colA.image('https://raw.githubusercontent.com/codigoquant/stock_dashboard/c9f45ca0748dd827fc13e29ee51a941a74dfad95/images/pie-chart-svgrepo-com.svg')
        else:
            colA.image(f'https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/{t}.png', width=85)
        colB.metric(label="retorno", value=f"{rets[t]:.0%}")
        colC.metric(label="volatilidade", value=f"{vols[t]:.0%}")
        style_metric_cards(background_color='rgba(255,255,255,0)')

    col1, col2 = st.columns(2, gap='large')
    with col1:
        st.subheader("Desempenho Relativo")
        st.line_chart(norm_prices, height=600)

    with col2:
        st.subheader("Risco-Retorno")
        fig = px.scatter(
            x=vols,
            y=rets,
            text=vols.index,
            color=rets/vols,
            color_continuous_scale=px.colors.sequential.Bluered_r
        )
        fig.update_traces(
            textfont_color='white', 
            marker=dict(size=45),
            textfont_size=10,                  
        )
        fig.layout.yaxis.title = 'Retorno Total'
        fig.layout.xaxis.title = 'Volatilidade (anualizada)'
        fig.layout.height = 600
        fig.layout.xaxis.tickformat = ".0%"
        fig.layout.yaxis.tickformat = ".0%"        
        fig.layout.coloraxis.colorbar.title = 'Sharpe'
        st.plotly_chart(fig, use_container_width=True)

st.set_page_config(layout="wide")

with st.sidebar:
    tickers, prices = build_sidebar()

st.title('Python para Investidores')
if tickers:
    build_main(tickers, prices)
