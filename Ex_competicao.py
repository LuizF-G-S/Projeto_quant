import requests
import yfinance as yf
import pandas as pd
import numpy as np


caminho_ibov = 'D:/Python/Projects/Task2/Task2/Ações_anuais.xlsx' # <- Mudar caminho, para o caminho onde se encontra o arquivo excel com os dados dos ativos;

caminho_arquivo = 'C:/Users/joaov/Downloads/Dados_Economatica.csv' # <- Mudar caminho para o arquivo com os dados da Economatica sobre PL;

df_ibov = pd.read_excel(caminho_ibov, engine='openpyxl', header=None)

# Obter os anos e as ações
anos = df_ibov.iloc[0].tolist()  # Primeira linha contém os anos
acoes = df_ibov.iloc[1:].dropna() .values.tolist()  # O restante contém as ações

# Criar um dicionário com anos como chaves e listas de ações como valores
dic_ibov = {}
for i, ano in enumerate(anos):
    dic_ibov[ano] = [acao[i] for acao in acoes]
    

dic_price_ibov = {}

for ano, acao in dic_ibov.items():
    dic_price_ibov[ano] = yf.download(acao, start=f'{ano}-01-01', end = f'{ano}-12-31')[['Open', 'Close', 'Adj Close', 'Volume']]
    
for ano, acoes in dic_ibov.items():
    for acao in acoes:
        for coluna in ['Open', 'Close', 'Adj Close', 'Volume']:
        # Verificar se o DataFrame correspondente em dic_price_ibov tem valores nulos na coluna 'Open'
            if dic_price_ibov[ano][coluna][acao].isnull().sum() > 0:
                # Remover valores nulos da coluna 'Open' para a ação específica
                dic_price_ibov[ano][coluna][acao].dropna(inplace=True)


dic_days_ibov = {}
for ano in dic_price_ibov.keys():
    l = []
    limite = 0.20
    for acao in dic_price_ibov[ano]['Open']:
        if dic_price_ibov[ano]['Open'][acao].isna().mean() < limite:
           l.append((acao,len(dic_price_ibov[ano]['Open'][acao])))

    dic_days_ibov[ano] = l

# Ativos que possuem participação no IBOVESPA em mais de 80% dos dias no IBOVESPA;    
ativos_filtrados = {}
for ano in dic_days_ibov:
    ativos = []
    for acao in dic_days_ibov[ano]:
        ativos.append(acao[0])
    
    ativos_filtrados[ano] = ativos

# Dados dos ativos;
dic_price_filtered = {}   
for ano in ativos_filtrados:
    acao = ativos_filtrados[ano]
    dic_price_filtered[ano] = yf.download(acao, start=f'{ano}-01-01', end = f'{ano}-12-31')[['Open', 'Close', 'Adj Close', 'Volume']]
 
    
# Obersavando os ativos que restaram que ainda possuem alguns dados faltantes, para fúturo tratamento;
dic_nan_actions = {}
for ano in dic_price_filtered:
    for acao in dic_price_filtered[ano]['Open']:
        dic_nan_actions[ano] = {key: value for key, value in dic_price_filtered[ano].items() if any(np.isnan(val) for val in value)}


# Indo para a parte do patrimônio Líquido;
dic_pl = pd.read_csv(caminho_arquivo)

# Criando um dicionário que irá conter as ações, trimestre e Patrimônio líquido por ano;
dic_pl_anual = {}

for ano in ativos_filtrados:
    trimestres = []
    # Verificando para cada ação que fora filtrada anteriormente;
    for acao in ativos_filtrados[ano]:
        at = acao[0: -3] + '<XBSP>' # <- mudança necessário dado que a string de um documento para o outro é diferente;
        cont = 0

        # Pegando as informações por trimestre:
        for ativos in dic_pl['Ativo'] == at:
            if cont > 3:
                break
            
            else:
                if ano != '2024': #<- o Ano de 2024 é complicado de obter as informações inteiras;
                    if at != 'ASAI3<XBSP>' or ano == '2020': #<- essa ação tem um comportamento estranho;
                       indice_linha = dic_pl[(dic_pl['Ativo'] == at) & (dic_pl['Data'] == f'{cont + 1}T{ano}')].index[0]
                       trimestres.append((acao, f'{cont+1}T', dic_pl['Patrim Liq| Em moeda orig| em milhares| consolid:sim*'][indice_linha + cont]))
                       cont += 1
                    
                    elif at == 'ASAI3<XBSP>' and ano == '2019' and cont == 3:
                        indice_linha = dic_pl[(dic_pl['Ativo'] == at) & (dic_pl['Data'] == f'{cont + 1}T{ano}')].index[0]
                        trimestres.append((acao, f'{cont+1}T', dic_pl['Patrim Liq| Em moeda orig| em milhares| consolid:sim*'][indice_linha + cont]))
                        cont += 1
                    
                    elif at == 'ASAI3<XBSP>' and ano == '2021' and cont < 3:
                        indice_linha = dic_pl[(dic_pl['Ativo'] == at) & (dic_pl['Data'] == f'{cont + 1}T{ano}')].index[0]
                        trimestres.append((acao, f'{cont+1}T', dic_pl['Patrim Liq| Em moeda orig| em milhares| consolid:sim*'][indice_linha + cont]))
                        cont += 1   
                        
                    else:
                        pass
                    
                #else: #Parte do código que buscava lidar com o ano de 2024;
                #    if cont > 1:
                #        break
                #    else:
                #        indice_linha = dic_pl[(dic_pl['Ativo'] == at) & (dic_pl['Data'] == f'{cont + 1}T{ano}')].index[0]
                #        trimestres.append((acao, dic_pl['Patrim Liq| Em moeda orig| em milhares| consolid:sim*'][indice_linha + cont]))
                #        cont += 1

            
    dic_pl_anual[ano] = trimestres            
            
# Criando portifólios de acordo com o índice SML;
port_SML = {}
for ano in range(2010, 2024): # <- separando o portifólio por ano;
    port_SML[f'{ano}'] = {}
    
    for trimestre in range(1, 5): # <- separando o portifólio por trimestre
        tri_acoes = []
        tri_pl = []
        
        for x in dic_pl_anual[f'{ano}']: # <- Verificando as ações elegíveis para cada trimestre;
            if x[1] == f'{trimestre}T':
                
                if x[2] == '-': # <- algumas ações não apresentam um Patrimônio Líquido em certos trimestre;
                    pass
                
                else: # <- algumas ações possuem PL, porém só começa a participar do mesmo no meio ou fim do trimestre;
                    if trimestre == 1 and ano == 2011 and (x[0] in ['AZZA3.SA', 'B3SA3.SA']):
                        pass
                    
                    elif trimestre == 1 and ano == 2012 and x[0] == 'COGN3.SA':
                        pass
                    
                    elif trimestre == 1 and ano == 2018 and x[0] == 'VBBR3.SA':
                        pass
                    
                    elif trimestre == 1 and ano == 2020 and x[0] == 'LWSA3.SA':
                        pass
                    
                    elif trimestre == 1 and ano == 2021 and (x[0] in ['ASAI3.SA', 'VAMO3.SA']):
                        pass
                    
                    else:
                      tri_acoes.append(x[0])
                      tri_pl.append(float(x[2]))
        
        # Separando os ativos de empresas Pequenas(SMALL) das grandes(LARGER): 50% de cada lado;
        quartil_50 = int(len(tri_acoes)/2)
        
        maiores_indices = sorted(range(len(tri_pl)), key = lambda i: tri_pl[i])[: quartil_50]
        menores_indices = sorted(range(len(tri_pl)), key = lambda i: tri_pl[i], reverse = True)[: quartil_50]
        
        # Criando subgrupos dessas empresas: 33% de cada lado;
        # Das empresas pequenas(SMALL): com alto PL(HIGH), PL médio(MEDIUM) e baixo PL(LOW);
        # Das empresas grandes(LARGER): com alto PL(HIGH), PL médio (MEDIUM) e baixo PL(LOW);
        tercil_33_50 = int(quartil_50/3)
        
        
        SmallHigh_indices = menores_indices[ -tercil_33_50 : ]
        SmallMedium_indices = menores_indices[ tercil_33_50 : -tercil_33_50 ]
        SmallLow_indices = menores_indices[ : tercil_33_50]
        
        LargerHigh_indices = maiores_indices[ : tercil_33_50 ]
        LargerMedium_indices = maiores_indices[ tercil_33_50 : -tercil_33_50 ]
        LargerLow_indices = maiores_indices[ -tercil_33_50 : ]
        
        # Obtendo as datas de inicio e fim do trimestre;
        if trimestre == 1:
            last_day = 31
            dia_inicial = dic_price_filtered[f'{ano}'].index[0]
            
            while last_day > 27:
                if f'{ano}-03-{last_day} 00:00:00' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                   dia_final = f'{ano}-03-{last_day} 00:00:00'
                   break
                   
                else:
                    last_day -= 1
        
        elif trimestre == 2 or trimestre == 3:
            last_day = 31
            first_day = 1 
            mes_inicial = 4 + 3*(trimestre - 2)
            mes_final = 6 + 3*(trimestre - 2)
            
            while first_day < 10:
                if f'{ano}-0{mes_inicial}-0{first_day} 00:00:00' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                    dia_inicial = f'{ano}-0{mes_inicial}-0{first_day} 00:00:00'
                    break
                
                else:
                    first_day += 1
            
            while last_day > 27:
                if f'{ano}-0{mes_final}-0{first_day}' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                   dia_final = f'{ano}-0{mes_final}-0{first_day} 00:00:00'
                   break
               
                else:
                    last_day -= 1
        
        else:
            dia_final = dic_price_filtered[f'{ano}'].index[-1]
            first_day = 1 
            
            while first_day < 10:
                if f'{ano}-10-0{first_day} 00:00:00' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                    dia_inicial = f'{ano}-10-0{first_day} 00:00:00'
                    break
                
                else:
                    first_day += 1
        
        # Calculando o retorno de cada subgrupo de ativos;
        retorno = {}
        for subgrupo in ['SmallLow', 'SmallMedium', 'SmallHigh', 'LargerLow', 'LargerMedium', 'LargerHigh']:
            valor_do_retorno = 0
            if subgrupo == 'SmallLow':
                tickers = [tri_acoes[i] for i in SmallLow_indices]
                
            elif subgrupo == 'SmallMedium':
                tickers = [tri_acoes[i] for i in SmallMedium_indices]
                
            elif subgrupo == 'SmallHigh':
                tickers = [tri_acoes[i] for i in SmallHigh_indices]
                
            elif subgrupo == 'LargerLow':
                tickers = [tri_acoes[i] for i in LargerLow_indices]
                
            elif subgrupo == 'LargerMedium':
                tickers = [tri_acoes[i] for i in LargerMedium_indices]
                
            elif subgrupo == 'LargerHigh':
                tickers = [tri_acoes[i] for i in LargerHigh_indices]
                
            for ticker in tickers:
                valor_do_retorno += (1/len(tickers))*((dic_price_filtered[f'{ano}']['Adj Close'][ticker][dia_final] / dic_price_filtered[f'{ano}']['Adj Close'][ticker][dia_inicial]) - 1)
                
            retorno[subgrupo] = valor_do_retorno
        
        # Calculando o índice SML (Small Minus Larger);
        SML = ((retorno['SmallLow'] + retorno['SmallMedium'] + retorno['SmallHigh']) / 3) - ((retorno['LargerLow'] + retorno['LargerMedium'] + retorno['LargerHigh']) / 3)
        
        # Obtendo o portifólio dado o valor do índice;
        if SML > 0:
           port_SML[f'{ano}'][f'{trimestre}T'] = (SML, [tri_acoes[i] for i in menores_indices])
           
        elif SML < 0:
            port_SML[f'{ano}'][f'{trimestre}T'] = (SML, [tri_acoes[i] for i in maiores_indices])
            
        else:
            port_SML[f'{ano}'][f'{trimestre}T'] = (SML, 'Problemas no cálculo')


# Criando portifólios de acordo com o índice HML;
port_HML = {}
for ano in range(2010, 2024): # <- separando o portifólio por ano;
    port_HML[f'{ano}'] = {}
    
    for trimestre in range(1, 5): # <- separando o portifólio por trimestre
        tri_acoes = []
        tri_pl = []
        
        for x in dic_pl_anual[f'{ano}']: # <- Verificando as ações elegíveis para cada trimestre;
            if x[1] == f'{trimestre}T':
                
                if x[2] == '-': # <- algumas ações não apresentam um Patrimônio Líquido em certos trimestre;
                    pass
                
                else: # <- algumas ações possuem PL, porém só começa a participar do mesmo no meio ou fim do trimestre;
                    if trimestre == 1 and ano == 2011 and (x[0] in ['AZZA3.SA', 'B3SA3.SA']):
                        pass
                    
                    elif trimestre == 1 and ano == 2012 and x[0] == 'COGN3.SA':
                        pass
                    
                    elif trimestre == 1 and ano == 2018 and x[0] == 'VBBR3.SA':
                        pass
                    
                    elif trimestre == 1 and ano == 2020 and x[0] == 'LWSA3.SA':
                        pass
                    
                    elif trimestre == 1 and ano == 2021 and (x[0] in ['ASAI3.SA', 'VAMO3.SA']):
                        pass
                    
                    else:
                      tri_acoes.append(x[0])
                      tri_pl.append(float(x[2]))
        
        # Separando os ativos de empresas com alto patrimônio (HIGH), das com médio patrimônio (MEDIUM) e das com baixo(LOW): 33% para cada grupo;            
        tercil_33 = int(len(tri_acoes)/3)
        
        maiores_indices = sorted(range(len(tri_pl)), key = lambda i: tri_pl[i])[: tercil_33]
        menores_indices = sorted(range(len(tri_pl)), key = lambda i: tri_pl[i], reverse = True)[: tercil_33]
        
        # Criando subgrupos dessas empresas: 50% de cada lado; (só vamos utilizar a HIGH e LOW)
        # Das empresas HIGH: Larger e Small;
        # Das empresas LOW: Larger e Small;
        quartil_50_33 = int(tercil_33/2)
        
        
        SmallHigh_indices = menores_indices[ -quartil_50_33 : ]
        
        SmallLow_indices = menores_indices[ : quartil_50_33]
        
        LargerHigh_indices = maiores_indices[ : quartil_50_33 ]
        
        LargerLow_indices = maiores_indices[ -quartil_50_33 : ]
        
        # Obtendo as datas de inicio e fim do trimestre;
        if trimestre == 1:
            last_day = 31
            dia_inicial = dic_price_filtered[f'{ano}'].index[0]
            
            while last_day > 27:
                if f'{ano}-03-{last_day} 00:00:00' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                   dia_final = f'{ano}-03-{last_day} 00:00:00'
                   break
                   
                else:
                    last_day -= 1
        
        elif trimestre == 2 or trimestre == 3:
            last_day = 31
            first_day = 1 
            mes_inicial = 4 + 3*(trimestre - 2)
            mes_final = 6 + 3*(trimestre - 2)
            
            while first_day < 10:
                if f'{ano}-0{mes_inicial}-0{first_day} 00:00:00' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                    dia_inicial = f'{ano}-0{mes_inicial}-0{first_day} 00:00:00'
                    break
                
                else:
                    first_day += 1
            
            while last_day > 27:
                if f'{ano}-0{mes_final}-0{first_day}' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                   dia_final = f'{ano}-0{mes_final}-0{first_day} 00:00:00'
                   break
               
                else:
                    last_day -= 1
        
        else:
            dia_final = dic_price_filtered[f'{ano}'].index[-1]
            first_day = 1 
            
            while first_day < 10:
                if f'{ano}-10-0{first_day} 00:00:00' in dic_price_filtered[f'{ano}']['Open']['ABEV3.SA'].keys():
                    dia_inicial = f'{ano}-10-0{first_day} 00:00:00'
                    break
                
                else:
                    first_day += 1
        
        # Calculando o retorno de cada subgrupo de ativos;    
        retorno = {}
        for subgrupo in ['SmallLow', 'SmallHigh', 'LargerLow', 'LargerHigh']:
            valor_do_retorno = 0
            if subgrupo == 'SmallLow':
                tickers = [tri_acoes[i] for i in SmallLow_indices]
                
                
            elif subgrupo == 'SmallHigh':
                tickers = [tri_acoes[i] for i in SmallHigh_indices]
                
                
            elif subgrupo == 'LargerLow':
                tickers = [tri_acoes[i] for i in LargerLow_indices]
                
        
            elif subgrupo == 'LargerHigh':
                tickers = [tri_acoes[i] for i in LargerHigh_indices]
                
                
            for ticker in tickers:
                valor_do_retorno += (1/len(tickers))*((dic_price_filtered[f'{ano}']['Adj Close'][ticker][dia_final] / dic_price_filtered[f'{ano}']['Adj Close'][ticker][dia_inicial]) - 1)
                
            retorno[subgrupo] = valor_do_retorno
        
        # Calculando o índice HML (High Minus Low);    
        HML = ((retorno['LargerHigh'] + retorno['SmallHigh']) / 2) - ((retorno['SmallLow'] + retorno['LargerLow'] ) / 2)
        
        # Obtendo o portifólio dado o valor do índice;
        if HML > 0:
           port_HML[f'{ano}'][f'{trimestre}T'] = (HML, [tri_acoes[i] for i in menores_indices])
           
        elif HML < 0:
            port_HML[f'{ano}'][f'{trimestre}T'] = (HML, [tri_acoes[i] for i in maiores_indices])
            
        else:
            port_HML[f'{ano}'][f'{trimestre}T'] = (HML, 'Problemas no cálculo')



