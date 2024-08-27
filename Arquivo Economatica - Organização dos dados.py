import pandas as pd

# Substitua 'arquivo.xlsx' pelo caminho do seu arquivo
caminho_do_arquivo = 'arquivo.xlsx'

# Lê o arquivo Excel
df = pd.read_excel(caminho_do_arquivo)

# Separando o arquivo Excel em diferentes dataframes específicos para cada coluna

Empresas = df['Ibovespa'][4:200] # -> Contém nomes das empresas, mudar de alguma forma para os tickers das mesmas

Valor = {}
PL = {}
Ativ_financeiros = {}

#Criando uma lista das datas
data = []

# Preenchendo os dataframes de acordo com as datas.
for i in range(300):
    
    # Número índice da coluna unnamed: número
    v = 2 + 4*i
    pl = 3 + 4*i
    af = 4 + 4*i
    
    # Salvando a data
    dia = df[f'Unnamed: {v}'][2]
    data.append(dia)
    
    # Pegando os valores nessa data
    Valor[f'{dia}'] = df[f'Unnamed: {v}'][4:200]
    PL[f'{dia}'] = df[f'Unnamed: {pl}'][4:200]
    Ativ_financeiros[f'{dia}'] = df[f'Unnamed: {af}'][4:200] 




# Organizando os dataframes em um único, criando subdivisões, a primeira contém os anos,
# a segunda o último dia do mês, e dentro das mesmas o nome das empresas, valor das ações, 
# Patrimônio Líquido e ativos financeiros;

Ibov= {}

# Indo de 2000 até 2020;
for t in range(21):
    Ibov[f'{2000 + t}'] = {}
    
    # Separando as datas de forma anual;
    for d in range(12):
    
        ativos = []
        Valores = []
        Patr_liq = []
        fin = []
           
        #Verificando para cada linha, se apresenta algum valor nessa data, caso não, pular o mesmo;
        for j in range(196):
            if pd.isna(Valor[f'{data[d + 12*t]}'][j+4]) and pd.isna(PL[f'{data[d + 12*t]}'][j+4]):
             
              pass
         
            else:
             
              ativos.append(Empresas[j+4])
              Valores.append(Valor[f'{data[d + 12*t]}'][j+4])
              Patr_liq.append(PL[f'{data[d + 12*t]}'][j+4])
              fin.append(Ativ_financeiros[f'{data[d + 12*t]}'][j+4])
           
          
       
            
       
       
        Ibov[f'{2000 + t}'][f'{data[d + 12*t]}'] = {'Ativos': ativos,
                                        'Valor': Valores,
                                        'PL': Patr_liq,
                                        'Ativos financeiros': fin}
        