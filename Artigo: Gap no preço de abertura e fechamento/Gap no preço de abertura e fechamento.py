import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np

#Obter os tickers
def get_assets_list():
    # Site a qual contém os símbolos dos ativos
    url = "https://br.tradingview.com/symbols/BMFBOVESPA-IBOV/components/"
    
    try:
       # Obter acesso ao site
       response = requests.get(url)

       # Caso não dê certo criar uma excessão
       response.raise_for_status()

       # Ler o HTML caso entrada afirmada
       soup = BeautifulSoup(response.text, "html.parser")
 
       # Encontrar entre todas as linha com termo chave
       rows = soup.find_all(
            "tr",
            {
               "class": "row-RdUXZpkv",
               "data-rowkey": lambda x: x and x.startswith("BMFBOVESPA"),
            },
          )

       # Extrair os símbolos de cada linha
       assets = [row["data-rowkey"][11:] + ".SA" for row in rows]

       return assets
   
    except requests.exceptions.RequestException as e:
       # Mostrar uma mensagem de erro, caso não consiga carregar o site
       st.error(f"Error loading asset list: {e}")

       return None    
    

def get_asset_stats(data):
    """
    Returns a dictionary with statistics of the input data.

    Parameters:
    data (pandas.Series or pandas.DataFrame): The input data.

    Returns:
    dict: A dictionary with the following keys: "Media" (mean), "Variancia" (variance),
    "Desvio_Padrao" (standard deviation), "Maximo" (maximum value), "Minimo" (minimum value).

    """
    # Calculate the statistics of the input data
    stats = {
        "Media": data.mean(),  # Calculate the mean
        "Variancia": data.var(),  # Calculate the variance
        "Desvio_ Padrao": data.std(),  # Calculate the standard deviation
        "Maximo": data.max(),  # Get the maximum value
        "Minimo": data.min(),  # Get the minimum value
    }

    return stats

def get_prices(tickers):
    prices = {}
    for ticker in tickers:
       stock = yf.Ticker(ticker)
       hist = stock.history(period="max")
       first_day = hist.index.min()
       
       data = yf.download(ticker, start = first_day)
       data.dropna(inplace=True)
       
       prices[f'{ticker}'] = data['Adj Close']
    return prices

def get_open_prices(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date)
    data.dropna(inplace=True)
    return data['Open']

def get_close_prices(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date)
    data.dropna(inplace=True)
    return data['Close']

def Long_and_short_index(valores, tamanho):
    # obtendo os maiores e menores desvio padrões para a estrategia Long & Short
    maiores = sorted(valores, reverse = True)[:tamanho]
    menores = sorted(valores, reverse = True)[-tamanho:]
    
    # buscando os indexes das maiores e menores volatilidades
    Long_index = []
    Short_index = []
    for i in maiores:
        for j in valores:
            if i == j:
                Long_index.append(valores[valores == j].index[0])
                
    for k in menores:
        for m in valores:
            if k == m:
                Short_index.append(valores[valores == m].index[0])            
    
    
    return Long_index, Short_index


ativos = get_assets_list()


precos = get_prices(ativos)
precos = pd.DataFrame(precos)
precos = precos.reset_index(drop=False)
precos = precos.drop(columns = ['ALOS3.SA'])

precos_anuais = {}

for y in range(23):
    dias = 252 + y*252
    precos_anuais[f'{2000 + y}'] = {}
    for i in precos:
        if i == 'Date':
            pass
        else:
            if len(precos[i]) > 6186 - dias:
               prices = {'Data': precos['Date'][ :252], f'{i}': precos[i][ :252]}
               prices = pd.DataFrame(prices)
               prices = prices.dropna(subset=[f'{i}'])
        
               precos_anuais[f'{2000 + y}'][f'{i}'] = prices
               
    precos = precos.drop(precos.index[ :252])
               

    
#preco_abertura = get_open_prices(ativos, '2001-01-01', '2022-12-31')

#preco_fechamento = get_close_prices(ativos, '2001-01-01', '2022-12-31')

#tercil = len(ativos)/3




    
Long, Short = Long_and_short_index(DP_assets, int(tercil))

