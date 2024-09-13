import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np

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


def get_prices_and_volumn(ativos, ano):
    
    # Pegar os ativos de determinado ano;
    lista_de_ativos = ativos[ano].dropna()
    lista_de_ativos = lista_de_ativos.tolist()
    
    # Download dos dados referentes aos ativos;
    data = yf.download(lista_de_ativos, start = f'{ano}-01-01', end = f'{ano}-12-31')
    #data.dropna(inplace=True)

    # Pegando os preços ajustados no fim do dia;
    precos = data['Adj Close']
            
    # Calcula a soma anual do volume para o ativo atual
    volumn_sum = data['Volume'].sum()
    
    return precos, volumn_sum

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
            

# Se os seus dados começam a partir de 2000, o ano de referencia a ser utilizado é 2001, e assim por diante;
def SML(dados, ano_de_referencia): 
    
    SML = []
    
    # Definir a porcentagem limite de NaN permitida
    limite_nan = 0.80 * 258  # 80% de 258 dados
    
    # Fazendo cálculo Mensal do fator;
    for meses in range(12):
        
        MES = meses + 1
        
        if MES == 1:
           #Pegando os dados específicos do ano anterior;
           ano_anterior = ano_de_referencia - 1
           dates = dados[f'{ano_anterior}']
    
           dates_PL = dates['Patrimônio Líquido']
           dates_prices = dates['Preços Ajustados']
    

           # Remover colunas com mais de 80% de valores NaN
           dates_prices = dates_prices.dropna(thresh=258 - limite_nan, axis=1)           

           #Pegando o quartil de 50% para dividir os dados em 2 grupos, e 33% de cada grupo;
           quartil50 = int(len(dates_prices.columns)/2)
           tercil33 = int(quartil50/3)
    
           #Transformando os dados em relação ao Patrimônio líquido em dataframe, para manipulação;
           dates_PL = pd.DataFrame(dates_PL)
    
           #Obtendo os índices dos 50% maiores PL de ativos e 50% menores PL de ativos;
           index_L = dates_PL['Patrimônio'].nlargest(quartil50).index
           index_S = dates_PL['Patrimônio'].nsmallest(quartil50).index
    
           # Index corregidos, pelos ativos removidos por dados insuficientes;
           index_corregido_L = []   
           index_corregido_S = []  
    
           #Criando listas para separação dos ativos ( L: Largest; S: Smallest)
           port_L = []
           port_S = []
           for i in range(len(dates_PL['Ações'])):
               if i in index_L and dates_PL['Ações'][i] in dates_prices.columns: 
                   port_L.append(dates_PL['Ações'][i])
                   index_corregido_L.append(i)
               
               elif i in index_S and dates_PL['Ações'][i] in dates_prices.columns:
                   port_S.append(dates_PL['Ações'][i])
                   index_corregido_S.append(i)

          # Separando os grupos em subgrupos de P: Pequeno, M: Médio e H: Alto em relação ao 
          # Patrimônio Líquido, ou seja, com os dados já organizados de forma decrescente,
          # as empresas pequenas com menores PL's, são os primeiros dados, e as empresas
          # pequenas com altos PL's são os últimos, e vice-versa com as empresas de grande porte;
    
           SP_index = index_corregido_S[0: tercil33]
           SM_index = index_corregido_S[tercil33: (2*tercil33)]
        

           HM_index = index_corregido_L[tercil33 : (2*tercil33) ]
           HP_index = index_corregido_L[(2*tercil33):]

          # Com os index obtidos para cada grupo e subgrupo, é criado 3 listas que conterão
          # os ativos participantes de cada subgrupo;
        
           # Empresas pequenas:
           SP = [] # Pequena e baixo patrimônio;
           SM = [] # Pequena e patrimônio mêdio;
           SH = [] # Pequena e alto patrimônio;
           
           for i in index_corregido_S: # Vai rodar todos os números índices das empresas de porte pequeno;
               
                if i in SP_index: # Vai buscar se o index no momento também se encontra na lista de indices de empresas com pequeno porte e baixo PL;
                    SP.append(dates_PL['Ações'][i])
                       
                elif i in SM_index: # Mesma ideia da de cima, porém para empresas pequeans e médio PL;
                    SM.append(dates_PL['Ações'][i])
                           
                else: # Caso não esteja em nenhuma das duas opções de cima, a empresa é logo uma de pequeno porte com alto PL;
                    SH.append(dates_PL['Ações'][i])
               
           # Empresas grandes:
           HP = []
           HM = []
           HH = []

           for i in index_corregido_L: # Da mesma forma, rodará os números índices salvos das empresas de grande porte;
               if i in HP_index:
                  HP.append(dates_PL['Ações'][i])
                       
               elif i in HM_index:
                  HM.append(dates_PL['Ações'][i])
                       
               else:
                  HH.append(dates_PL['Ações'][i])
                       
           # Obtendo o peso de cada ativo, para cada portifólio criado; (Pesos iguais para cada ativo)        
           peso_SP = 1/len(SP) 
           peso_SM = 1/len(SM) 
           peso_SH = 1/len(SH) 
           peso_HP = 1/len(HP) 
           peso_HM = 1/len(HM) 
           peso_HH = 1/len(HH) 

           
           # Criando funções para o retorno médio de cada portifólio;
           cont = 1
           while cont < 10:
               if f'{ano_anterior}-12-0{cont} 00:00:00' in dates_prices.index:
                    primeiro_dia = f'{ano_anterior}-12-0{cont} 00:00:00'
                    break
               cont += 1
        
        
           ultimo_dia = dates_prices.index[-1] # Último dia de dezembro
           
           ret_SP = 0 # Retorno médio do portifólio de empresas de pequeno porte com baixo PL;
           for i in SP:
               ret_SP += peso_SP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                 
           ret_SM = 0 # Retorno médio do portifólio de empresas de pequeno porte com médio PL;
           for i in SM:
               ret_SM += peso_SM*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
              

           ret_SH = 0 # Retorno médio do portifólio de empresas de pequeno porte com alto PL;
           for i in SH:
               ret_SH += peso_SH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
          

           ret_HP = 0 # Retorno médio do portifólio de empresas de grande porte com baixo PL;
           for i in HP:
               ret_HP += peso_HP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                 
           ret_HM = 0 # Retorno médio do portifólio de empresas de grande porte com médio PL;
           for i in HM:
               ret_HM += peso_HM*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
              

           ret_HH = 0 # Retorno médio do portifólio de empresas de grande porte com alto PL;
           for i in HH:
               ret_HH += peso_HH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
              
           # Calculando o índice SML (Small Minus Larger);    
           SML.append(((ret_SP + ret_SM + ret_SH)/3)-((ret_HP + ret_HM + ret_HH)/3))
    

        elif 1 < MES < 11:
            #Pegando os dados específicos do ano;
            dates = dados[f'{ano_de_referencia}']
     
            dates_PL = dates['Patrimônio Líquido']
            dates_prices = dates['Preços Ajustados']
            
            # Remover colunas com mais de 80% de valores NaN
            dates_prices = dates_prices.dropna(thresh=258 - limite_nan, axis=1)           

            #Pegando o quartil de 50% para dividir os dados em 2 grupos, e 33% de cada grupo;
            quartil50 = int(len(dates_prices.columns)/2)
            tercil33 = int(quartil50/3)
     
            #Transformando os dados em relação ao Patrimônio líquido em dataframe, para manipulação;
            dates_PL = pd.DataFrame(dates_PL)
     
            #Obtendo os índices dos 50% maiores PL de ativos e 50% menores PL de ativos;
            index_L = dates_PL['Patrimônio'].nlargest(quartil50).index
            index_S = dates_PL['Patrimônio'].nsmallest(quartil50).index
     
            # Index corregidos, pelos ativos removidos por dados insuficientes;
            index_corregido_L = []   
            index_corregido_S = []  
     
            #Criando listas para separação dos ativos ( L: Largest; S: Smallest)
            port_L = []
            port_S = []
            for i in range(len(dates_PL['Ações'])):
                if i in index_L and dates_PL['Ações'][i] in dates_prices.columns: 
                    port_L.append(dates_PL['Ações'][i])
                    index_corregido_L.append(i)
                
                elif i in index_S and dates_PL['Ações'][i] in dates_prices.columns:
                    port_S.append(dates_PL['Ações'][i])
                    index_corregido_S.append(i)

           # Separando os grupos em subgrupos de P: Pequeno, M: Médio e H: Alto em relação ao 
           # Patrimônio Líquido, ou seja, com os dados já organizados de forma decrescente,
           # as empresas pequenas com menores PL's, são os primeiros dados, e as empresas
           # pequenas com altos PL's são os últimos, e vice-versa com as empresas de grande porte;
     
            SP_index = index_corregido_S[0: tercil33]
            SM_index = index_corregido_S[tercil33: (2*tercil33)]
         

            HM_index = index_corregido_L[tercil33 : (2*tercil33) ]
            HP_index = index_corregido_L[(2*tercil33):]

           # Com os index obtidos para cada grupo e subgrupo, é criado 3 listas que conterão
           # os ativos participantes de cada subgrupo;
         
            # Empresas pequenas:
            SP = [] # Pequena e baixo patrimônio;
            SM = [] # Pequena e patrimônio mêdio;
            SH = [] # Pequena e alto patrimônio;
            
            for i in index_corregido_S: # Vai rodar todos os números índices das empresas de porte pequeno;
                
                 if i in SP_index: # Vai buscar se o index no momento também se encontra na lista de indices de empresas com pequeno porte e baixo PL;
                     SP.append(dates_PL['Ações'][i])
                        
                 elif i in SM_index: # Mesma ideia da de cima, porém para empresas pequeans e médio PL;
                     SM.append(dates_PL['Ações'][i])
                            
                 else: # Caso não esteja em nenhuma das duas opções de cima, a empresa é logo uma de pequeno porte com alto PL;
                     SH.append(dates_PL['Ações'][i])
                
            # Empresas grandes:
            HP = []
            HM = []
            HH = []

            for i in index_corregido_L: # Da mesma forma, rodará os números índices salvos das empresas de grande porte;
                if i in HP_index:
                   HP.append(dates_PL['Ações'][i])
                        
                elif i in HM_index:
                   HM.append(dates_PL['Ações'][i])
                        
                else:
                   HH.append(dates_PL['Ações'][i])
                        
            # Obtendo o peso de cada ativo, para cada portifólio criado; (Pesos iguais para cada ativo)        
            peso_SP = 1/len(SP) 
            peso_SM = 1/len(SM) 
            peso_SH = 1/len(SH) 
            peso_HP = 1/len(HP) 
            peso_HM = 1/len(HM) 
            peso_HH = 1/len(HH)
            
            # Criando funções para o retorno médio de cada portifólio;
            cont = 1
            while cont < 10:
                if f'{ano_de_referencia}-0{MES - 1}-0{cont} 00:00:00' in dates_prices.index:
                     primeiro_dia = f'{ano_de_referencia}-0{MES - 1}-0{cont} 00:00:00'
                     break
                cont += 1
                
            cont = 0
            while cont < 4:
                dia = 31 - cont
                if f'{ano_de_referencia}-0{MES - 1}-{dia} 00:00:00' in dates_prices.index:
                     ultimo_dia = f'{ano_de_referencia}-0{MES - 1}-{dia} 00:00:00'
                     break
                cont += 1
        
        
            ret_SP = 0 # Retorno médio do portifólio de empresas de pequeno porte com baixo PL;
            for i in SP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SP += peso_SP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                  
            ret_SM = 0 # Retorno médio do portifólio de empresas de pequeno porte com médio PL;
            for i in SM:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SM += peso_SM*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
               

            ret_SH = 0 # Retorno médio do portifólio de empresas de pequeno porte com alto PL;
            for i in SH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SH += peso_SH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_HP = 0 # Retorno médio do portifólio de empresas de grande porte com baixo PL;
            for i in HP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HP += peso_HP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            ret_HM = 0 # Retorno médio do portifólio de empresas de grande porte com médio PL;
            for i in HM:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HM += peso_HM*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_HH = 0 # Retorno médio do portifólio de empresas de grande porte com alto PL;
            for i in HH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HH += peso_HH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            # Calculando o índice SML (Small Minus Larger);    
            SML.append(((ret_SP + ret_SM + ret_SH)/3)-((ret_HP + ret_HM + ret_HH)/3))
     
        elif MES >= 11:
            #Pegando os dados específicos do ano;
            dates = dados[f'{ano_de_referencia}']
     
            dates_PL = dates['Patrimônio Líquido']
            dates_prices = dates['Preços Ajustados']
            
            # Remover colunas com mais de 80% de valores NaN
            dates_prices = dates_prices.dropna(thresh=258 - limite_nan, axis=1)           

            #Pegando o quartil de 50% para dividir os dados em 2 grupos, e 33% de cada grupo;
            quartil50 = int(len(dates_prices.columns)/2)
            tercil33 = int(quartil50/3)
     
            #Transformando os dados em relação ao Patrimônio líquido em dataframe, para manipulação;
            dates_PL = pd.DataFrame(dates_PL)
     
            #Obtendo os índices dos 50% maiores PL de ativos e 50% menores PL de ativos;
            index_L = dates_PL['Patrimônio'].nlargest(quartil50).index
            index_S = dates_PL['Patrimônio'].nsmallest(quartil50).index
     
            # Index corregidos, pelos ativos removidos por dados insuficientes;
            index_corregido_L = []   
            index_corregido_S = []  
     
            #Criando listas para separação dos ativos ( L: Largest; S: Smallest)
            port_L = []
            port_S = []
            for i in range(len(dates_PL['Ações'])):
                if i in index_L and dates_PL['Ações'][i] in dates_prices.columns: 
                    port_L.append(dates_PL['Ações'][i])
                    index_corregido_L.append(i)
                
                elif i in index_S and dates_PL['Ações'][i] in dates_prices.columns:
                    port_S.append(dates_PL['Ações'][i])
                    index_corregido_S.append(i)

           # Separando os grupos em subgrupos de P: Pequeno, M: Médio e H: Alto em relação ao 
           # Patrimônio Líquido, ou seja, com os dados já organizados de forma decrescente,
           # as empresas pequenas com menores PL's, são os primeiros dados, e as empresas
           # pequenas com altos PL's são os últimos, e vice-versa com as empresas de grande porte;
     
            SP_index = index_corregido_S[0: tercil33]
            SM_index = index_corregido_S[tercil33: (2*tercil33)]
         

            HM_index = index_corregido_L[tercil33 : (2*tercil33) ]
            HP_index = index_corregido_L[(2*tercil33):]

           # Com os index obtidos para cada grupo e subgrupo, é criado 3 listas que conterão
           # os ativos participantes de cada subgrupo;
         
            # Empresas pequenas:
            SP = [] # Pequena e baixo patrimônio;
            SM = [] # Pequena e patrimônio mêdio;
            SH = [] # Pequena e alto patrimônio;
            
            for i in index_corregido_S: # Vai rodar todos os números índices das empresas de porte pequeno;
                
                 if i in SP_index: # Vai buscar se o index no momento também se encontra na lista de indices de empresas com pequeno porte e baixo PL;
                     SP.append(dates_PL['Ações'][i])
                        
                 elif i in SM_index: # Mesma ideia da de cima, porém para empresas pequeans e médio PL;
                     SM.append(dates_PL['Ações'][i])
                            
                 else: # Caso não esteja em nenhuma das duas opções de cima, a empresa é logo uma de pequeno porte com alto PL;
                     SH.append(dates_PL['Ações'][i])
                
            # Empresas grandes:
            HP = []
            HM = []
            HH = []

            for i in index_corregido_L: # Da mesma forma, rodará os números índices salvos das empresas de grande porte;
                if i in HP_index:
                   HP.append(dates_PL['Ações'][i])
                        
                elif i in HM_index:
                   HM.append(dates_PL['Ações'][i])
                        
                else:
                   HH.append(dates_PL['Ações'][i])
                        
            # Obtendo o peso de cada ativo, para cada portifólio criado; (Pesos iguais para cada ativo)        
            peso_SP = 1/len(SP) 
            peso_SM = 1/len(SM) 
            peso_SH = 1/len(SH) 
            peso_HP = 1/len(HP) 
            peso_HM = 1/len(HM) 
            peso_HH = 1/len(HH)
            
            # Criando funções para o retorno médio de cada portifólio;
            cont = 1
            while cont < 10:
                if f'{ano_de_referencia}-{MES - 1}-0{cont} 00:00:00' in dates_prices.index:
                     primeiro_dia = f'{ano_de_referencia}-{MES - 1}-0{cont} 00:00:00'
                     break
                cont += 1
                
            cont = 0
            while cont < 4:
                dia = 31 - cont
                if f'{ano_de_referencia}-{MES - 1}-{dia} 00:00:00' in dates_prices.index:
                     ultimo_dia = f'{ano_de_referencia}-{MES - 1}-{dia} 00:00:00'
                     break
                cont += 1
        
        
            ret_SP = 0 # Retorno médio do portifólio de empresas de pequeno porte com baixo PL;
            for i in SP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SP += peso_SP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            ret_SM = 0 # Retorno médio do portifólio de empresas de pequeno porte com médio PL;
            for i in SM:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SM += peso_SM*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_SH = 0 # Retorno médio do portifólio de empresas de pequeno porte com alto PL;
            for i in SH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SH += peso_SH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_HP = 0 # Retorno médio do portifólio de empresas de grande porte com baixo PL;
            for i in HP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HP += peso_HP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                  
            ret_HM = 0 # Retorno médio do portifólio de empresas de grande porte com médio PL;
            for i in HM:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HM += peso_HM*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_HH = 0 # Retorno médio do portifólio de empresas de grande porte com alto PL;
            for i in HH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HH += peso_HH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            # Calculando o índice SML (Small Minus Larger);    
            SML.append(((ret_SP + ret_SM + ret_SH)/3)-((ret_HP + ret_HM + ret_HH)/3))

              
    # Retornar o resultado;

    return SML


def HML(dados, ano_de_referencia): 
    
    HML = []
    
    # Definir a porcentagem limite de NaN permitida
    limite_nan = 0.80 * 258  # 80% de 258 dados
    
    # Fazendo cálculo Mensal do fator;
    for meses in range(12):
        
        MES = meses + 1
        if MES == 1:
            #Pegando os dados específicos do ano anterior;
            ano_anterior = ano_de_referencia - 1
            dates = dados[f'{ano_anterior}']
            dates_PL = dates['Patrimônio Líquido']
            dates_prices = dates['Preços Ajustados']

            # Remover colunas com mais de 80% de valores NaN
            dates_prices = dates_prices.dropna(thresh=258 - limite_nan, axis=1)


            #Pegando o quartil de 33% para dividir os dados em 3 grupos, e 50% de cada grupo;
            tercil33 = int(len(dates_prices.columns)/3)
            quartil50 = int(tercil33/2)
            
            #Transformando os dados em relação ao Patrimônio líquido em dataframe, para manipulação;
            dates_PL = pd.DataFrame(dates_PL)
            
            #Obtendo os índices dos 33% maiores PL de ativos, 33% menores PL de ativos e o restante é médiano;
            index_L = dates_PL['Patrimônio'].nlargest(tercil33).index
            index_S = dates_PL['Patrimônio'].nsmallest(tercil33).index
            index_M = []
            
            for i in dates_PL['Patrimônio'].index:
                if i not in index_L and i not in index_S:
                    index_M.append(i)
            
            # Index corregidos, pelos ativos removidos por dados insuficientes;
            index_corregido_L = []   
            index_corregido_S = []  
            index_corregido_M = [] 
            
            #Criando listas para separação dos ativos ( L: Largest; M: Modest; S: Smallest)
            port_L = []
            port_S = []
            port_M = []
            for i in range(len(dates_PL['Ações'])):
                if i in index_L and dates_PL['Ações'][i] in dates_prices.columns: 
                    port_L.append(dates_PL['Ações'][i])
                    index_corregido_L.append(i)
                       
                elif i in index_S and dates_PL['Ações'][i] in dates_prices.columns:
                    port_S.append(dates_PL['Ações'][i])
                    index_corregido_S.append(i)
                    
                elif i in index_M and dates_PL['Ações'][i] in dates_prices.columns:
                    port_M.append(dates_PL['Ações'][i])
                    index_corregido_M.append(i)

            # Separando os grupos em subgrupos de P: Pequeno e H: Alto em relação ao Patrimônio Líquido;
            # Ou seja, com os dados já organizados de forma decrescente, as empresas pequenas com menores PL's,
            # são os primeiros dados, e as empresas pequenas com altos PL's são os últimos, e vice-versa com as
            # empresas de grande porte;
            
            SP_index = index_corregido_S[0: quartil50]
            SH_index = index_corregido_S[quartil50: ]
                

            HH_index = index_corregido_L[ :quartil50]
            HP_index = index_corregido_L[quartil50:]

            # Com os index obtidos para cada grupo e subgrupo, é criado 2 listas que conterão os ativos
            # participantes de cada sugrupo;
                
            # Empresas pequenas:
            SP = [] # Pequena e baixo patrimônio;
            SH = [] # Pequena e alto patrimônio;

            for i in index_corregido_S: # Vai rodar todos os números índices das empresas de porte pequeno;
                
                 if i in SP_index: # Vai buscar se o index no momento também se encontra na lista de indices de empresas com pequeno porte e baixo PL;
                     SP.append(dates_PL['Ações'][i])
                        
                 elif i in SH_index: # Mesma ideia da de cima, porém para empresas pequeans e médio PL;
                     SH.append(dates_PL['Ações'][i])
                            
                
            # Empresas grandes:
            HP = []
            HH = []

            for i in index_corregido_L: # Da mesma forma, rodará os números índices salvos das empresas de grande porte;
                if i in HP_index:
                   HP.append(dates_PL['Ações'][i])
                                       
                elif i in HH_index:
                   HH.append(dates_PL['Ações'][i])
                        
            # Obtendo o peso de cada ativo, para cada portifólio criado; (Pesos iguais para cada ativo)        
            peso_SP = 1/len(SP) 
            peso_SH = 1/len(SH) 
            peso_HP = 1/len(HP) 
            peso_HH = 1/len(HH) 

            # Pegando os dados referentes ao preço em dezembro do ano anterior; 
            
            dates_prices = dates['Preços Ajustados']
            
            # Criando funções para o retorno médio de cada portifólio;
            
              # Obtendo as datas referente ao primeiro e último dia útil de dezembro do ano anterior; 
            cont = 1
            while cont < 10:
                
               if f'{ano_anterior}-12-0{cont} 00:00:00' in dates_prices.index:
                   primeiro_dia = f'{ano_anterior}-12-0{cont} 00:00:00'
                   break
               
               cont += 1
               
            ultimo_dia = dates_prices.index[-1] # Último dia de dezembro
            
            ret_SP = 0 # Retorno médio do portifólio de empresas de pequeno porte com baixo PL;
            for i in SP:
                ret_SP += peso_SP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                        
            ret_SH = 0 # Retorno médio do portifólio de empresas de pequeno porte com alto PL;
            for i in SH:
                ret_SH += peso_SH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
             

            ret_HP = 0 # Retorno médio do portifólio de empresas de grande porte com baixo PL;
            for i in HP:
                ret_HP += peso_HP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                        

            ret_HH = 0 # Retorno médio do portifólio de empresas de grande porte com alto PL;
            for i in HH:
                ret_HH += peso_HH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                 
            # Calculando o índice HML (High Minus Low);    
            HML.append(((ret_SH + ret_HH)/2)-((ret_HP + ret_SP)/2))
            
        elif 1 <  MES < 11:
            
            #Pegando os dados específicos do ano anterior;
            dates = dados[f'{ano_de_referencia}']
            dates_PL = dates['Patrimônio Líquido']
            dates_prices = dates['Preços Ajustados']

            # Remover colunas com mais de 80% de valores NaN
            dates_prices = dates_prices.dropna(thresh=258 - limite_nan, axis=1)


            #Pegando o quartil de 33% para dividir os dados em 3 grupos, e 50% de cada grupo;
            tercil33 = int(len(dates_prices.columns)/3)
            quartil50 = int(tercil33/2)
            
            #Transformando os dados em relação ao Patrimônio líquido em dataframe, para manipulação;
            dates_PL = pd.DataFrame(dates_PL)
            
            #Obtendo os índices dos 33% maiores PL de ativos, 33% menores PL de ativos e o restante é médiano;
            index_L = dates_PL['Patrimônio'].nlargest(tercil33).index
            index_S = dates_PL['Patrimônio'].nsmallest(tercil33).index
            index_M = []
            
            for i in dates_PL['Patrimônio'].index:
                if i not in index_L and i not in index_S:
                    index_M.append(i)
            
            # Index corregidos, pelos ativos removidos por dados insuficientes;
            index_corregido_L = []   
            index_corregido_S = []  
            index_corregido_M = [] 
            
            #Criando listas para separação dos ativos ( L: Largest; M: Modest; S: Smallest)
            port_L = []
            port_S = []
            port_M = []
            for i in range(len(dates_PL['Ações'])):
                if i in index_L and dates_PL['Ações'][i] in dates_prices.columns: 
                    port_L.append(dates_PL['Ações'][i])
                    index_corregido_L.append(i)
                       
                elif i in index_S and dates_PL['Ações'][i] in dates_prices.columns:
                    port_S.append(dates_PL['Ações'][i])
                    index_corregido_S.append(i)
                    
                elif i in index_M and dates_PL['Ações'][i] in dates_prices.columns:
                    port_M.append(dates_PL['Ações'][i])
                    index_corregido_M.append(i)

            # Separando os grupos em subgrupos de P: Pequeno e H: Alto em relação ao Patrimônio Líquido;
            # Ou seja, com os dados já organizados de forma decrescente, as empresas pequenas com menores PL's,
            # são os primeiros dados, e as empresas pequenas com altos PL's são os últimos, e vice-versa com as
            # empresas de grande porte;
            
            SP_index = index_corregido_S[0: quartil50]
            SH_index = index_corregido_S[quartil50: ]
                

            HH_index = index_corregido_L[ :quartil50]
            HP_index = index_corregido_L[quartil50:]

            # Com os index obtidos para cada grupo e subgrupo, é criado 2 listas que conterão os ativos
            # participantes de cada sugrupo;
                
            # Empresas pequenas:
            SP = [] # Pequena e baixo patrimônio;
            SH = [] # Pequena e alto patrimônio;

            for i in index_corregido_S: # Vai rodar todos os números índices das empresas de porte pequeno;
                
                 if i in SP_index: # Vai buscar se o index no momento também se encontra na lista de indices de empresas com pequeno porte e baixo PL;
                     SP.append(dates_PL['Ações'][i])
                        
                 elif i in SH_index: # Mesma ideia da de cima, porém para empresas pequeans e médio PL;
                     SH.append(dates_PL['Ações'][i])
                            
                
            # Empresas grandes:
            HP = []
            HH = []

            for i in index_corregido_L: # Da mesma forma, rodará os números índices salvos das empresas de grande porte;
                if i in HP_index:
                   HP.append(dates_PL['Ações'][i])
                                       
                elif i in HH_index:
                   HH.append(dates_PL['Ações'][i])
                        
            # Obtendo o peso de cada ativo, para cada portifólio criado; (Pesos iguais para cada ativo)        
            peso_SP = 1/len(SP) 
            peso_SH = 1/len(SH) 
            peso_HP = 1/len(HP) 
            peso_HH = 1/len(HH) 

        
            # Obtendo as datas referente ao primeiro e último dia útil de dezembro do ano anterior; 
            
            cont = 1
            while cont < 10:
                if f'{ano_de_referencia}-0{MES - 1}-0{cont} 00:00:00' in dates_prices.index:
                     primeiro_dia = f'{ano_de_referencia}-0{MES - 1}-0{cont} 00:00:00'
                     break
                cont += 1
               
            cont = 0
            while cont < 4:
                dia = 31 - cont
                if f'{ano_de_referencia}-0{MES - 1}-{dia} 00:00:00' in dates_prices.index:
                     ultimo_dia = f'{ano_de_referencia}-0{MES - 1}-{dia} 00:00:00'
                     break
                cont += 1
            
            ret_SP = 0 # Retorno médio do portifólio de empresas de pequeno porte com baixo PL;
            for i in SP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SP += peso_SP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                       
            ret_SH = 0 # Retorno médio do portifólio de empresas de pequeno porte com alto PL;
            for i in SH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SH += peso_SH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_HP = 0 # Retorno médio do portifólio de empresas de grande porte com baixo PL;
            for i in HP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HP += peso_HP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            ret_HH = 0 # Retorno médio do portifólio de empresas de grande porte com alto PL;
            for i in HH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HH += peso_HH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            # Calculando o índice HML (High Minus Low);    
            HML.append(((ret_SH + ret_HH)/2)-((ret_HP + ret_SP)/2))
            
        else:
            
            #Pegando os dados específicos do ano anterior;
            dates = dados[f'{ano_de_referencia}']
            dates_PL = dates['Patrimônio Líquido']
            dates_prices = dates['Preços Ajustados']

            # Remover colunas com mais de 80% de valores NaN
            dates_prices = dates_prices.dropna(thresh=258 - limite_nan, axis=1)


            #Pegando o quartil de 33% para dividir os dados em 3 grupos, e 50% de cada grupo;
            tercil33 = int(len(dates_prices.columns)/3)
            quartil50 = int(tercil33/2)
            
            #Transformando os dados em relação ao Patrimônio líquido em dataframe, para manipulação;
            dates_PL = pd.DataFrame(dates_PL)
            
            #Obtendo os índices dos 33% maiores PL de ativos, 33% menores PL de ativos e o restante é médiano;
            index_L = dates_PL['Patrimônio'].nlargest(tercil33).index
            index_S = dates_PL['Patrimônio'].nsmallest(tercil33).index
            index_M = []
            
            for i in dates_PL['Patrimônio'].index:
                if i not in index_L and i not in index_S:
                    index_M.append(i)
            
            # Index corregidos, pelos ativos removidos por dados insuficientes;
            index_corregido_L = []   
            index_corregido_S = []  
            index_corregido_M = [] 
            
            #Criando listas para separação dos ativos ( L: Largest; M: Modest; S: Smallest)
            port_L = []
            port_S = []
            port_M = []
            for i in range(len(dates_PL['Ações'])):
                if i in index_L and dates_PL['Ações'][i] in dates_prices.columns: 
                    port_L.append(dates_PL['Ações'][i])
                    index_corregido_L.append(i)
                       
                elif i in index_S and dates_PL['Ações'][i] in dates_prices.columns:
                    port_S.append(dates_PL['Ações'][i])
                    index_corregido_S.append(i)
                    
                elif i in index_M and dates_PL['Ações'][i] in dates_prices.columns:
                    port_M.append(dates_PL['Ações'][i])
                    index_corregido_M.append(i)

            # Separando os grupos em subgrupos de P: Pequeno e H: Alto em relação ao Patrimônio Líquido;
            # Ou seja, com os dados já organizados de forma decrescente, as empresas pequenas com menores PL's,
            # são os primeiros dados, e as empresas pequenas com altos PL's são os últimos, e vice-versa com as
            # empresas de grande porte;
            
            SP_index = index_corregido_S[0: quartil50]
            SH_index = index_corregido_S[quartil50: ]
                

            HH_index = index_corregido_L[ :quartil50]
            HP_index = index_corregido_L[quartil50:]

            # Com os index obtidos para cada grupo e subgrupo, é criado 2 listas que conterão os ativos
            # participantes de cada sugrupo;
                
            # Empresas pequenas:
            SP = [] # Pequena e baixo patrimônio;
            SH = [] # Pequena e alto patrimônio;

            for i in index_corregido_S: # Vai rodar todos os números índices das empresas de porte pequeno;
                
                 if i in SP_index: # Vai buscar se o index no momento também se encontra na lista de indices de empresas com pequeno porte e baixo PL;
                     SP.append(dates_PL['Ações'][i])
                        
                 elif i in SH_index: # Mesma ideia da de cima, porém para empresas pequeans e médio PL;
                     SH.append(dates_PL['Ações'][i])
                            
                
            # Empresas grandes:
            HP = []
            HH = []

            for i in index_corregido_L: # Da mesma forma, rodará os números índices salvos das empresas de grande porte;
                if i in HP_index:
                   HP.append(dates_PL['Ações'][i])
                                       
                elif i in HH_index:
                   HH.append(dates_PL['Ações'][i])
                        
            # Obtendo o peso de cada ativo, para cada portifólio criado; (Pesos iguais para cada ativo)        
            peso_SP = 1/len(SP) 
            peso_SH = 1/len(SH) 
            peso_HP = 1/len(HP) 
            peso_HH = 1/len(HH) 

        
            # Obtendo as datas referente ao primeiro e último dia útil de dezembro do ano anterior; 
            
            cont = 1
            while cont < 10:
                if f'{ano_de_referencia}-{MES - 1}-0{cont} 00:00:00' in dates_prices.index:
                     primeiro_dia = f'{ano_de_referencia}-{MES - 1}-0{cont} 00:00:00'
                     break
                cont += 1
               
            cont = 0
            while cont < 4:
                dia = 31 - cont
                if f'{ano_de_referencia}-{MES - 1}-{dia} 00:00:00' in dates_prices.index:
                     ultimo_dia = f'{ano_de_referencia}-{MES - 1}-{dia} 00:00:00'
                     break
                cont += 1
            
            ret_SP = 0 # Retorno médio do portifólio de empresas de pequeno porte com baixo PL;
            for i in SP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SP += peso_SP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                       
            ret_SH = 0 # Retorno médio do portifólio de empresas de pequeno porte com alto PL;
            for i in SH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_SH += peso_SH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])

            ret_HP = 0 # Retorno médio do portifólio de empresas de grande porte com baixo PL;
            for i in HP:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HP += peso_HP*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            ret_HH = 0 # Retorno médio do portifólio de empresas de grande porte com alto PL;
            for i in HH:
                if np.isnan(dates_prices[i].loc[f'{primeiro_dia}']) or np.isnan(dates_prices[i].loc[f'{ultimo_dia}']):
                    pass
                else:
                   ret_HH += peso_HH*((dates_prices[i].loc[f'{ultimo_dia}'] - dates_prices[i].loc[f'{primeiro_dia}'])/dates_prices[i].loc[f'{primeiro_dia}'])
                   
            # Calculando o índice HML (High Minus Low);    
            HML.append(((ret_SH + ret_HH)/2)-((ret_HP + ret_SP)/2))
    
    # Retornar o resultado;
    return HML


#Pegando os tickers das ações da BVSP de cada ano
ativos = pd.read_excel('D:/Python/Projects/Task2/Task2/Ações_anuais.xlsx') # <- Mudar caminho, para o caminho onde se encontra o arquivo excel com os dados dos ativos;



#Caminho do arquivo para o patrimônio líquido
caminho_arquivo = 'C:/Users/joaov/Downloads/Dados_Economatica.csv' # <- Mudar caminho para o arquivo com os dados da Economatica sobre PL;

#Obtendo o patrimônio líquido anual, a partir de 2010
pl = obter_patrimonio(caminho_arquivo)

#Organizando os dados;
dados = {}

for i in range(15):
    
    ano = 2010 + i
    
    #Obtendo os dados em relação ao preço de fechamento ajustado junto com os tickers do ano;
    precos, volume_anual = get_prices_and_volumn(ativos, f'{ano}')
    precos = pd.DataFrame(precos)
    
    #Obtendo as ações que fazem parte da ibovespa no ano dado;
    tickers = precos.columns
    
    #Obtendo volume anual de cada ação;

    
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
        'Volume': volume_anual,
        #'Preço de abertura': precos_abertura,
        #'Preço de fechamento': precos_fechamento,
        'Desvio_Padrão': dp,
        'Ativos mais volateis': ativos_Mvolatilidade,
        'Ativos menos volateis': ativos_mvolatilidade,
        'Patrimônio Líquido': PL
    }
    
    #Preenchendo nosso dataframe para cada ano;
    dados[f'{ano}'] = valores


indice_SML = []
for i in range(14):
    ano = 2011 + i
    indice_SML.append(SML(dados, ano))


indice_HML = []
for i in range(14):
    ano = 2011 + i
    indice_HML.append(HML(dados, ano))



#Long, Short = Long_and_short_index(DP_assets, int(tercil))

