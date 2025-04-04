"""
Módulo para geração de gráficos dos resultados do backtest.

Este módulo fornece funções para visualizar os resultados do backtest
através de diversos gráficos que mostram o desempenho da estratégia,
incluindo lucro/perda por operação, curva de capital, drawdown e
gráficos técnicos com ADX.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
import seaborn as sns
import os

# Configuração de estilo para os gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('viridis')

def criar_pasta_graficos():
    """Cria a pasta para salvar os gráficos se ela não existir."""
    if not os.path.exists('graficos'):
        os.makedirs('graficos')

def plotar_lucro_prejuizo_operacoes(operacoes):
    """
    Gera um gráfico de barras mostrando o lucro/prejuízo de cada operação.
    
    Args:
        operacoes (list): Lista de dicionários com dados das operações
    """
    criar_pasta_graficos()
    
    # Preparar dados
    datas = []
    lucros = []
    cores = []
    
    for op in operacoes:
        if 'timestamp' in op and 'lucro_prejuizo' in op and op['lucro_prejuizo'] is not None:
            try:
                if isinstance(op['timestamp'], str):
                    data = datetime.fromisoformat(op['timestamp'])
                else:
                    data = op['timestamp']
                
                datas.append(data)
                lucro = float(op['lucro_prejuizo'])
                lucros.append(lucro)
                
                if lucro >= 0:
                    cores.append('green')
                else:
                    cores.append('red')
            except (ValueError, TypeError) as e:
                print(f"Erro ao processar operação: {e}")
                continue
    
    if not datas or not lucros:
        print("Dados insuficientes para gerar gráfico de lucro/prejuízo")
        return
    
    # Calcular métricas
    total_operacoes = len(lucros)
    operacoes_lucrativas = sum(1 for l in lucros if l > 0)
    operacoes_perdedoras = sum(1 for l in lucros if l < 0)
    lucro_total = sum(lucros)
    lucro_medio = lucro_total / total_operacoes if total_operacoes > 0 else 0
    
    # Calcular Gain/Loss Ratio
    ganhos = [l for l in lucros if l > 0]
    perdas = [abs(l) for l in lucros if l < 0]
    gain_loss_ratio = (sum(ganhos) / len(ganhos)) / (sum(perdas) / len(perdas)) if perdas and ganhos else 0
    
    # Calcular Sharpe Ratio
    retornos = pd.Series(lucros)
    retorno_medio = retornos.mean()
    desvio_padrao = retornos.std()
    taxa_livre_risco = 0.02  # 2% ao ano
    sharpe_ratio = ((retorno_medio - taxa_livre_risco) / desvio_padrao) * np.sqrt(252) if desvio_padrao != 0 else 0
    
    # Criar figura
    plt.figure(figsize=(15, 8))
    plt.bar(range(len(lucros)), lucros, color=cores)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Configurar eixos e título
    plt.title('Lucro/Prejuízo por Operação', fontsize=16, pad=20)
    plt.xlabel('Número da Operação', fontsize=12)
    plt.ylabel('Lucro/Prejuízo (USDT)', fontsize=12)
    
    # Adicionar métricas detalhadas
    info_text = (
        f"Métricas de Performance:\n"
        f"------------------------\n"
        f"Total de Operações: {total_operacoes}\n"
        f"Operações Lucrativas: {operacoes_lucrativas} ({operacoes_lucrativas/total_operacoes*100:.1f}%)\n"
        f"Operações Perdedoras: {operacoes_perdedoras} ({operacoes_perdedoras/total_operacoes*100:.1f}%)\n"
        f"Lucro Total: {lucro_total:.2f} USDT\n"
        f"Lucro Médio: {lucro_medio:.2f} USDT\n\n"
        f"Métricas de Risco:\n"
        f"------------------------\n"
        f"Gain/Loss Ratio: {gain_loss_ratio:.2f}\n"
        f"Índice Sharpe: {sharpe_ratio:.2f}\n"
        f"Maior Ganho: {max(lucros):.2f} USDT\n"
        f"Maior Perda: {min(lucros):.2f} USDT\n"
        f"Desvio Padrão: {desvio_padrao:.2f}"
    )
    
    plt.annotate(info_text, xy=(0.02, 0.98), xycoords='axes fraction', 
                fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8),
                va='top')
    
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('graficos/lucro_prejuizo_operacoes.png', dpi=300, bbox_inches='tight')
    plt.close()

def plotar_curva_capital(operacoes):
    """
    Plota a curva de capital ao longo do tempo e o drawdown.
    """
    criar_pasta_graficos()
    
    # Preparar dados
    capital_timeline = []
    datas = []
    capital_atual = 1000  # Capital inicial
    
    for op in operacoes:
        if 'timestamp' in op and 'lucro_prejuizo' in op and op['lucro_prejuizo'] is not None:
            try:
                if isinstance(op['timestamp'], str):
                    data = datetime.fromisoformat(op['timestamp'])
                else:
                    data = op['timestamp']
                
                lucro = float(op['lucro_prejuizo'])
                capital_atual += lucro
                
                datas.append(data)
                capital_timeline.append(capital_atual)
            except (ValueError, TypeError) as e:
                print(f"Erro ao processar operação para curva de capital: {e}")
                continue
    
    if not datas or not capital_timeline:
        print("Dados insuficientes para gerar curva de capital")
        return
    
    # Criar DataFrame
    df_capital = pd.DataFrame({
        'data': datas,
        'capital': capital_timeline
    }).set_index('data')
    
    df_capital = df_capital.sort_index()
    
    # Calcular drawdown
    df_capital['pico_anterior'] = df_capital['capital'].cummax()
    df_capital['drawdown'] = (df_capital['capital'] - df_capital['pico_anterior']) / df_capital['pico_anterior'] * 100
    
    # Calcular métricas adicionais
    retorno_total = ((capital_atual - 1000) / 1000) * 100
    drawdown_maximo = abs(df_capital['drawdown'].min())
    volatilidade = df_capital['capital'].pct_change().std() * np.sqrt(252)
    
    # Calcular CAGR (Compound Annual Growth Rate)
    dias_total = (df_capital.index[-1] - df_capital.index[0]).days
    cagr = ((capital_atual / 1000) ** (365 / dias_total) - 1) * 100 if dias_total > 0 else 0
    
    # Criar figura com subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[3, 1])
    
    # Plotar curva de capital
    ax1.plot(df_capital.index, df_capital['capital'], 'b-', linewidth=2)
    ax1.set_title('Curva de Capital e Métricas de Performance', fontsize=16, pad=20)
    ax1.set_ylabel('Capital (USDT)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Adicionar métricas no gráfico
    info_text = (
        f"Métricas de Performance:\n"
        f"------------------------\n"
        f"Capital Inicial: 1000 USDT\n"
        f"Capital Final: {capital_atual:.2f} USDT\n"
        f"Retorno Total: {retorno_total:.2f}%\n"
        f"CAGR: {cagr:.2f}%\n"
        f"Drawdown Máximo: {drawdown_maximo:.2f}%\n"
        f"Volatilidade Anual: {volatilidade*100:.2f}%\n"
        f"Índice de Calmar: {abs(retorno_total/drawdown_maximo) if drawdown_maximo != 0 else 0:.2f}"
    )
    
    ax1.annotate(info_text, xy=(0.02, 0.98), xycoords='axes fraction',
                fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8),
                va='top')
    
    # Plotar drawdown
    ax2.fill_between(df_capital.index, df_capital['drawdown'], 0, color='red', alpha=0.3)
    ax2.plot(df_capital.index, df_capital['drawdown'], 'r-', linewidth=1.5)
    ax2.set_title('Drawdown (%)', fontsize=14)
    ax2.set_ylabel('Drawdown (%)', fontsize=12)
    ax2.set_xlabel('Data', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Formatação do eixo X
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('graficos/curva_capital.png', dpi=300, bbox_inches='tight')
    plt.close()

def plotar_indicadores_adx(df):
    """
    Plota os valores de ADX, DI+ e DI- ao longo do tempo.
    
    Args:
        df (DataFrame): DataFrame com os dados dos indicadores
    """
    criar_pasta_graficos()
    
    # Verificar se o DataFrame tem os dados necessários
    if 'adx' not in df.columns or 'di_plus' not in df.columns or 'di_minus' not in df.columns:
        print("DataFrame não contém os indicadores ADX necessários")
        return
    
    # Limitar a quantidade de dados para melhorar a legibilidade
    # Usar apenas os últimos 100 períodos
    if len(df) > 100:
        print(f"Limitando gráfico de ADX para os últimos 100 períodos (de {len(df)} totais)")
        df_plot = df.iloc[-100:].copy()
    else:
        df_plot = df.copy()
    
    # Criar figura
    plt.figure(figsize=(12, 6))
    
    # Plotar ADX, DI+ e DI- com cores diferentes
    plt.plot(df_plot.index, df_plot['adx'], label='ADX', color='blue', linewidth=2)
    plt.plot(df_plot.index, df_plot['di_plus'], label='DI+', color='green', linewidth=1.5)
    plt.plot(df_plot.index, df_plot['di_minus'], label='DI-', color='red', linewidth=1.5)
    
    # Adicionar linha horizontal no threshold do ADX (geralmente 20)
    plt.axhline(y=20, color='gray', linestyle='--', alpha=0.7, label='Threshold (20)')
    
    # Configurar eixos e título
    plt.title('Indicadores ADX, DI+ e DI- (últimos 100 períodos)', fontsize=16)
    plt.xlabel('Data', fontsize=12)
    plt.ylabel('Valor', fontsize=12)
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Formatação da data no eixo x
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    
    # Ajustar layout para garantir que todas as informações estejam visíveis
    plt.tight_layout()
    
    # Salvar gráfico
    plt.savefig('graficos/indicadores_adx.png')
    plt.close()

def plotar_distribuicao_retornos(operacoes):
    """
    Plota a distribuição dos retornos das operações.
    """
    criar_pasta_graficos()
    
    retornos = []
    for op in operacoes:
        if 'lucro_prejuizo' in op and op['lucro_prejuizo'] is not None:
            try:
                retorno = float(op['lucro_prejuizo'])
                retornos.append(retorno)
            except (ValueError, TypeError):
                continue
    
    if not retornos:
        print("Sem dados de retorno válidos para gerar a distribuição")
        return
    
    retornos_array = np.array(retornos)
    
    # Calcular métricas estatísticas
    media = np.mean(retornos_array)
    mediana = np.median(retornos_array)
    desvio_padrao = np.std(retornos_array)
    skewness = pd.Series(retornos_array).skew()
    kurtosis = pd.Series(retornos_array).kurtosis()
    
    # Calcular VaR e CVaR
    var_95 = np.percentile(retornos_array, 5)  # 95% VaR
    cvar_95 = np.mean(retornos_array[retornos_array <= var_95])  # 95% CVaR
    
    # Criar figura
    plt.figure(figsize=(15, 8))
    
    # Plotar histograma com KDE
    sns.histplot(retornos_array, kde=True, bins=30)
    
    # Adicionar linhas verticais
    plt.axvline(x=0, color='black', linestyle='--', alpha=0.7)
    plt.axvline(x=media, color='red', linestyle='-', alpha=0.7, label=f'Média: {media:.2f}')
    plt.axvline(x=var_95, color='orange', linestyle='--', alpha=0.7, label=f'VaR 95%: {var_95:.2f}')
    
    # Configurar gráfico
    plt.title('Distribuição dos Retornos e Métricas de Risco', fontsize=16, pad=20)
    plt.xlabel('Retorno (USDT)', fontsize=12)
    plt.ylabel('Frequência', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Adicionar métricas estatísticas
    stats_text = (
        f"Métricas Estatísticas:\n"
        f"------------------------\n"
        f"Média: {media:.2f}\n"
        f"Mediana: {mediana:.2f}\n"
        f"Desvio Padrão: {desvio_padrao:.2f}\n"
        f"Skewness: {skewness:.2f}\n"
        f"Kurtosis: {kurtosis:.2f}\n\n"
        f"Métricas de Risco:\n"
        f"------------------------\n"
        f"VaR 95%: {var_95:.2f}\n"
        f"CVaR 95%: {cvar_95:.2f}\n"
        f"Razão de Sortino: {(media / np.std(retornos_array[retornos_array < 0])) if len(retornos_array[retornos_array < 0]) > 0 else 0:.2f}"
    )
    
    plt.annotate(stats_text, xy=(0.02, 0.98), xycoords='axes fraction',
                fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8),
                va='top')
    
    plt.tight_layout()
    plt.savefig('graficos/distribuicao_retornos.png', dpi=300, bbox_inches='tight')
    plt.close()

def gerar_todos_graficos(df, operacoes):
    """
    Gera todos os gráficos para análise do backtest.
    """
    criar_pasta_graficos()
    
    print("Gerando gráficos de análise do backtest...")
    
    plotar_lucro_prejuizo_operacoes(operacoes)
    plotar_curva_capital(operacoes)
    plotar_indicadores_adx(df)
    plotar_distribuicao_retornos(operacoes)
    
    print("Gráficos gerados com sucesso na pasta 'graficos/'")

def calcular_metricas_risco(self, operations, capital_inicial=1000):
    """
    Calcula métricas de risco e retorno do backtest.
    
    Args:
        operations (list): Lista de operações realizadas
        capital_inicial (float): Capital inicial do backtest
        
    Returns:
        dict: Dicionário com as métricas calculadas
    """
    try:
        if not operations:
            return None
            
        # Calcular retornos por operação
        retornos = [op['Profit/Loss'] / capital_inicial for op in operations]
        
        # Métricas básicas
        total_ops = len(operations)
        ops_gain = sum(1 for op in operations if op['Result'] == 'Gain')
        ops_loss = sum(1 for op in operations if op['Result'] == 'Stop')
        
        win_rate = ops_gain / total_ops if total_ops > 0 else 0
        
        # Métricas de lucro/prejuízo
        lucro_total = sum(op['Profit/Loss'] for op in operations)
        lucro_medio = lucro_total / total_ops if total_ops > 0 else 0
        
        ganhos = [op['Profit/Loss'] for op in operations if op['Result'] == 'Gain']
        perdas = [op['Profit/Loss'] for op in operations if op['Result'] == 'Stop']
        
        ganho_medio = sum(ganhos) / len(ganhos) if ganhos else 0
        perda_media = sum(perdas) / len(perdas) if perdas else 0
        
        # Gain/Loss Ratio
        gain_loss_ratio = abs(ganho_medio / perda_media) if perda_media != 0 else float('inf')
        
        # Profit Factor
        profit_factor = abs(sum(ganhos) / sum(perdas)) if sum(perdas) != 0 else float('inf')
        
        # Drawdown
        capital = capital_inicial
        capital_maximo = capital_inicial
        drawdown_atual = 0
        drawdown_maximo = 0
        drawdown_duracao = 0
        drawdown_duracao_maxima = 0
        dias_recuperacao = 0
        
        capital_curve = [capital_inicial]
        drawdown_curve = [0]
        
        for op in operations:
            capital += op['Profit/Loss']
            capital_curve.append(capital)
            
            if capital > capital_maximo:
                capital_maximo = capital
                drawdown_atual = 0
                drawdown_duracao = 0
            else:
                drawdown_atual = (capital_maximo - capital) / capital_maximo
                drawdown_duracao += 1
                
            if drawdown_atual > drawdown_maximo:
                drawdown_maximo = drawdown_atual
                drawdown_duracao_maxima = drawdown_duracao
                
            drawdown_curve.append(drawdown_atual * 100)  # Em percentual
            
            # Calcular dias de recuperação
            if capital < capital_inicial:
                dias_recuperacao += 1
                
        # Retorno total e anualizado
        retorno_total = (capital - capital_inicial) / capital_inicial
        dias_totais = (operations[-1]['ExitDate'] - operations[0]['EntryDate']).days
        retorno_anualizado = (1 + retorno_total) ** (365 / dias_totais) - 1 if dias_totais > 0 else 0
        
        # Volatilidade e Sharpe Ratio
        retornos_array = np.array(retornos)
        volatilidade_diaria = np.std(retornos_array)
        volatilidade_anual = volatilidade_diaria * np.sqrt(252)
        
        taxa_livre_risco = 0.06  # 6% ao ano
        excess_return = retorno_anualizado - taxa_livre_risco
        sharpe_ratio = excess_return / volatilidade_anual if volatilidade_anual != 0 else 0
        
        # Métricas de risco ajustado
        sortino_ratio = excess_return / (np.std(retornos_array[retornos_array < 0]) * np.sqrt(252)) if len(retornos_array[retornos_array < 0]) > 0 else 0
        calmar_ratio = retorno_anualizado / drawdown_maximo if drawdown_maximo != 0 else 0
        
        # Métricas de consistência
        ops_consecutivas_gain = 0
        ops_consecutivas_loss = 0
        max_ops_consecutivas_gain = 0
        max_ops_consecutivas_loss = 0
        
        atual_consecutivas_gain = 0
        atual_consecutivas_loss = 0
        
        for op in operations:
            if op['Result'] == 'Gain':
                atual_consecutivas_gain += 1
                atual_consecutivas_loss = 0
                max_ops_consecutivas_gain = max(max_ops_consecutivas_gain, atual_consecutivas_gain)
            else:
                atual_consecutivas_loss += 1
                atual_consecutivas_gain = 0
                max_ops_consecutivas_loss = max(max_ops_consecutivas_loss, atual_consecutivas_loss)
                
        return {
            'Total de Operações': total_ops,
            'Operações Gain': ops_gain,
            'Operações Loss': ops_loss,
            'Win Rate': win_rate,
            'Gain/Loss Ratio': gain_loss_ratio,
            'Profit Factor': profit_factor,
            'Lucro Total': lucro_total,
            'Lucro Médio': lucro_medio,
            'Ganho Médio': ganho_medio,
            'Perda Média': perda_media,
            'Retorno Total': retorno_total,
            'Retorno Anualizado': retorno_anualizado,
            'Volatilidade Anual': volatilidade_anual,
            'Sharpe Ratio': sharpe_ratio,
            'Sortino Ratio': sortino_ratio,
            'Calmar Ratio': calmar_ratio,
            'Drawdown Máximo': drawdown_maximo,
            'Duração Drawdown Máximo': drawdown_duracao_maxima,
            'Dias para Recuperação': dias_recuperacao,
            'Máximo Gains Consecutivos': max_ops_consecutivas_gain,
            'Máximo Losses Consecutivos': max_ops_consecutivas_loss,
            'Capital Final': capital,
            'Capital Curve': capital_curve,
            'Drawdown Curve': drawdown_curve
        }
        
    except Exception as e:
        print(f"Erro ao calcular métricas: {str(e)}")
        return None

def plotar_metricas(self, metricas, nome_estrategia="Backtest"):
    """
    Plota gráficos com as métricas do backtest.
    
    Args:
        metricas (dict): Dicionário com as métricas calculadas
        nome_estrategia (str): Nome da estratégia para os títulos
    """
    try:
        if not metricas:
            print("Sem métricas para plotar")
            return
            
        plt.style.use('seaborn')
        
        # Configurações gerais
        plt.rcParams['figure.figsize'] = [12, 8]
        plt.rcParams['font.size'] = 10
        
        # 1. Gráfico de Curva de Capital e Drawdown
        fig, (ax1, ax2) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]}, figsize=(12, 8))
        
        # Curva de Capital
        ax1.plot(metricas['Capital Curve'], label='Capital', color='blue')
        ax1.set_title(f'Curva de Capital - {nome_estrategia}')
        ax1.set_ylabel('Capital')
        ax1.grid(True)
        ax1.legend()
        
        # Drawdown
        ax2.fill_between(range(len(metricas['Drawdown Curve'])), 
                        metricas['Drawdown Curve'], 
                        0, 
                        color='red', 
                        alpha=0.3, 
                        label='Drawdown')
        ax2.set_title('Drawdown (%)')
        ax2.set_ylabel('Drawdown %')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('curva_capital_drawdown.png')
        plt.close()
        
        # 2. Gráfico de Métricas de Risco
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Sharpe, Sortino e Calmar Ratios
        ratios = ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']
        valores = [metricas[r] for r in ratios]
        axes[0, 0].bar(ratios, valores)
        axes[0, 0].set_title('Métricas de Risco Ajustado')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Win Rate e Profit Factor
        metricas_eficiencia = ['Win Rate', 'Profit Factor']
        valores = [metricas['Win Rate'], min(metricas['Profit Factor'], 5)]  # Limitando PF para visualização
        axes[0, 1].bar(metricas_eficiencia, valores)
        axes[0, 1].set_title('Métricas de Eficiência')
        
        # Retornos
        retornos = ['Retorno Total', 'Retorno Anualizado']
        valores = [metricas[r] for r in retornos]
        axes[1, 0].bar(retornos, valores)
        axes[1, 0].set_title('Retornos')
        
        # Operações
        ops = ['Total de Operações', 'Operações Gain', 'Operações Loss']
        valores = [metricas[o] for o in ops]
        axes[1, 1].bar(ops, valores)
        axes[1, 1].set_title('Operações')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('metricas_risco.png')
        plt.close()
        
        # 3. Gráfico de Distribuição de Retornos
        plt.figure(figsize=(12, 6))
        retornos = [(op['Profit/Loss'] / op['EntryPrice']) for op in self.operations]
        plt.hist(retornos, bins=50, edgecolor='black')
        plt.title('Distribuição dos Retornos')
        plt.xlabel('Retorno por Operação')
        plt.ylabel('Frequência')
        plt.grid(True)
        plt.savefig('distribuicao_retornos.png')
        plt.close()
        
        # 4. Texto com Resumo das Métricas
        with open('resumo_metricas.txt', 'w') as f:
            f.write(f"Resumo do Backtest - {nome_estrategia}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Métricas de Performance:\n")
            f.write(f"Retorno Total: {metricas['Retorno Total']:.2%}\n")
            f.write(f"Retorno Anualizado: {metricas['Retorno Anualizado']:.2%}\n")
            f.write(f"Volatilidade Anual: {metricas['Volatilidade Anual']:.2%}\n")
            f.write(f"Sharpe Ratio: {metricas['Sharpe Ratio']:.2f}\n")
            f.write(f"Sortino Ratio: {metricas['Sortino Ratio']:.2f}\n")
            f.write(f"Calmar Ratio: {metricas['Calmar Ratio']:.2f}\n\n")
            
            f.write("Métricas de Risco:\n")
            f.write(f"Drawdown Máximo: {metricas['Drawdown Máximo']:.2%}\n")
            f.write(f"Duração do Drawdown Máximo: {metricas['Duração Drawdown Máximo']} períodos\n")
            f.write(f"Dias para Recuperação: {metricas['Dias para Recuperação']} dias\n\n")
            
            f.write("Métricas Operacionais:\n")
            f.write(f"Total de Operações: {metricas['Total de Operações']}\n")
            f.write(f"Win Rate: {metricas['Win Rate']:.2%}\n")
            f.write(f"Gain/Loss Ratio: {metricas['Gain/Loss Ratio']:.2f}\n")
            f.write(f"Profit Factor: {metricas['Profit Factor']:.2f}\n")
            f.write(f"Ganho Médio: {metricas['Ganho Médio']:.2f}\n")
            f.write(f"Perda Média: {metricas['Perda Média']:.2f}\n")
            f.write(f"Máximo Gains Consecutivos: {metricas['Máximo Gains Consecutivos']}\n")
            f.write(f"Máximo Losses Consecutivos: {metricas['Máximo Losses Consecutivos']}\n")
            
    except Exception as e:
        print(f"Erro ao plotar métricas: {str(e)}") 