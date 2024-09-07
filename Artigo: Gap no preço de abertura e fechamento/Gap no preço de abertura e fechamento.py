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

def get_prices_and_volumn(tickers, start_date, end_date):
    prices = {}
    volumn = {}
    for ticker in tickers:
#           stock = yf.Ticker(ticker)
#           hist = stock.history(period="max")
#          first_day = hist.index.min()
       
           data = yf.download(ticker, start = start_date, end = end_date)
           data.dropna(inplace=True)
       
           if len(data) ==0:
               pass
           else:
               prices[f'{ticker}'] = data['Adj Close']
               volumn[f'{ticker}'] = data['Volume']
    
    return prices, volumn

def get_open_prices(tickers, start_date, end_date):
    open_prices = {}
    for ticker in tickers:
        data = yf.download(ticker, start=start_date, end = end_date)
        data.dropna(inplace=True)
        open_prices[f'{ticker}'] = data['Open']
    return open_prices

def get_close_prices(tickers, start_date, end_date):
    close_prices = {}
    for ticker in tickers:
        data = yf.download(ticker, start=start_date, end = end_date)
        data.dropna(inplace=True)
        close_prices[f'{ticker}'] = data['Close']
    return close_prices

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


def obter_patrimonio(arquivo):
    df = pd.read_csv(arquivo)
    
    PL_ativos = {}
    for i in range(int(len(df)/58)):
        ativo = df['Ativo'][i*58]
        
        Data = df['Data'][i*58: (i+1)*58]
        Data = Data.reset_index(drop=True)
        
        PL = df['Patrim Liq| Em moeda orig| em milhares| consolid:sim*'][i*58: (i+1)*58]
        PL = PL.reset_index(drop = True)
        
        PL_ativos[f'{ativo}'] = {'Data': Data,
                                 'PL': PL
                                 }
        PL_ativos[f'{ativo}'] = pd.DataFrame(PL_ativos[f'{ativo}'])
        PL_ativos[f'{ativo}']['PL'].replace('-', 0, inplace=True)
        
        for j in range(len(PL_ativos[f'{ativo}']['PL'])):
            PL_ativos[f'{ativo}']['PL'][j] = float(PL_ativos[f'{ativo}']['PL'][j])
         
            
    PL_anual = {}
    cont = 0    
    ativos = []
    for ativo in PL_ativos:
        ativos.append(ativo)


    for ano in range(15):
        a = 2010 + ano

        Pl = []

        for ativo in ativos:
            Pl.append(sum(PL_ativos[f'{ativo}']['PL'][cont*4: (cont+1)*4]))
        
        
        PL_anual[f'{a}'] = {'Ativos': ativos, 'Patrimônio': Pl}
        PL_anual[f'{a}'] = pd.DataFrame(PL_anual[f'{a}'])
        PL_anual[f'{a}'] = PL_anual[f'{a}'][(PL_anual[f'{a}'] != 0).all(axis=1)]
        PL_anual[f'{a}'] = PL_anual[f'{a}'].set_index('Ativos')
        
        cont += 1
    
    return PL_anual
            

#Pegando os tickers das ações da BVSP
ativos = get_assets_list()



#Caminho do arquivo para o patrimônio líquido
caminho_arquivo = 'C:/Users/joaov/Downloads/Dados_Economatica.csv'

#Obtendo o patrimônio líquido anual, a partir de 2010
pl = obter_patrimonio(caminho_arquivo)



dados = {}
for i in range(15):
    
    ano = 2010 + i
    
    #Obtendo os dados em relação ao preço de fechamento ajustado junto com os tickers do ano;
    precos, volume = get_prices_and_volumn(ativos, f'{ano}-01-01', f'{ano}-12-31')
    precos, volume = pd.DataFrame(precos), pd.DataFrame(volume)
    tickers = precos.columns
    
    #Pegando os preços de abertura no ano;
    #precos_abertura = pd.DataFrame(get_open_prices(tickers, f'{ano}-01-01', f'{ano}-12-31'))
    
    #Pegando os preços de fechamento no ano;
    #precos_fechamento = pd.DataFrame(get_close_prices(tickers, f'{ano}-01-01', f'{ano}-12-31'))
    
    #Obtendo a volatilidade de cada ativo composto pela Ibovespa;
    dp = get_asset_stats(precos)['Desvio_ Padrao']
    
    #Obtendo 5 ativos de maior volatilidade e 5 de menor volatilidade;
    dp = dp.sort_values(ascending = False)
    ativos_Mvolatilidade = dp[0:5].index
    ativos_mvolatilidade = dp[-5:].index
    
    #Obtendo o Patrimônio Líquido de cada empresa, dado o ano;
    ac = []
    p = []
    for ticker in tickers:
        for ind in pl[f'{ano}'].index:
            at = ind.split('<')[0]
            if f'{at}.SA' == ticker:
                ac.append( at + '.SA')
                p.append( pl[f'{ano}'].loc[f'{ind}','Patrimônio'])            
            else:
                pass
    PL = {
        'Ações': ac,
        'Patrimônio': p
        }
        
                
    
    
    #Agrupando as informações;
    valores = {
        'Preços Ajustados': precos,
        'Volume': volume,
        #'Preço de abertura': precos_abertura,
        #'Preço de fechamento': precos_fechamento,
        'Desvio_Padrão': dp,
        'Ativos mais volateis': ativos_Mvolatilidade,
        'Ativos menos volateis': ativos_mvolatilidade,
        'Patrimônio Líquido': PL
    }
    
    #Preenchendo nosso dataframe para cada ano;
    dados[f'{ano}'] = valores





#tercil = len(ativos)/3




    
#Long, Short = Long_and_short_index(DP_assets, int(tercil))

