"""
Módulo para geração de gráficos do backtest.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class BacktestPlotter:
    """
    Classe responsável por gerar gráficos para análise do backtest.
    """
    
    def __init__(self, operacoes, resultados, periodo_dias):
        """
        Inicializa o plotter.
        
        Args:
            operacoes (list): Lista de operações do backtest
            resultados (dict): Dicionário com resultados do backtest
            periodo_dias (int): Período do backtest em dias
        """
        self.operacoes = operacoes
        self.resultados = resultados
        self.periodo_dias = periodo_dias
        
        # Criar diretório para os gráficos se não existir
        if not os.path.exists('graficos'):
            os.makedirs('graficos')
    
    def calcular_curva_capital(self):
        """
        Calcula a curva de capital ao longo do tempo.
        
        Returns:
            DataFrame: DataFrame com a curva de capital
        """
        # Criar DataFrame com as operações
        df = pd.DataFrame(self.operacoes)
        
        # Converter timestamp para datetime
        df['data'] = pd.to_datetime(df['data'])
        
        # Ordenar por data
        df = df.sort_values('data')
        
        # Calcular capital acumulado
        df['capital_acumulado'] = df['lucro_prejuizo'].cumsum()
        
        return df
    
    def calcular_drawdown(self):
        """
        Calcula o drawdown ao longo do tempo.
        
        Returns:
            DataFrame: DataFrame com o drawdown
        """
        df = self.calcular_curva_capital()
        
        # Calcular pico máximo
        df['pico_maximo'] = df['capital_acumulado'].expanding().max()
        
        # Calcular drawdown
        df['drawdown'] = df['pico_maximo'] - df['capital_acumulado']
        
        # Calcular drawdown percentual
        df['drawdown_pct'] = (df['drawdown'] / df['pico_maximo']) * 100
        
        return df
    
    def plot_curva_capital(self):
        """
        Gera gráfico da curva de capital.
        """
        df = self.calcular_curva_capital()
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['data'], df['capital_acumulado'], label='Capital Acumulado')
        
        plt.title('Curva de Capital')
        plt.xlabel('Data')
        plt.ylabel('Capital (USDT)')
        plt.grid(True)
        plt.legend()
        
        # Rotacionar labels do eixo x para melhor visualização
        plt.xticks(rotation=45)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        plt.savefig('graficos/curva_capital.png')
        plt.close()
    
    def plot_drawdown(self):
        """
        Gera gráfico do drawdown.
        """
        df = self.calcular_drawdown()
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['data'], df['drawdown_pct'], label='Drawdown', color='red')
        
        plt.title('Drawdown ao Longo do Tempo')
        plt.xlabel('Data')
        plt.ylabel('Drawdown (%)')
        plt.grid(True)
        plt.legend()
        
        # Rotacionar labels do eixo x para melhor visualização
        plt.xticks(rotation=45)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        plt.savefig('graficos/drawdown.png')
        plt.close()
    
    def plot_distribuicao_operacoes(self):
        """
        Gera gráfico de pizza com a distribuição de operações ganhas e perdidas.
        """
        total_ops = self.resultados['total_operacoes']
        ops_ganhas = self.resultados['operacoes_ganhas']
        ops_perdidas = self.resultados['operacoes_perdidas']
        
        # Calcular percentuais
        pct_ganhas = (ops_ganhas / total_ops) * 100
        pct_perdidas = (ops_perdidas / total_ops) * 100
        
        # Criar dados para o gráfico
        labels = ['Ganhas', 'Perdidas']
        sizes = [ops_ganhas, ops_perdidas]
        colors = ['#2ecc71', '#e74c3c']
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
        plt.title('Distribuição de Operações')
        
        # Salvar gráfico
        plt.savefig('graficos/distribuicao_operacoes.png')
        plt.close()
    
    def plot_distribuicao_lucro(self):
        """
        Gera gráfico de distribuição do lucro/prejuízo das operações.
        """
        # Extrair lucros/prejuízos
        lucros = [op['lucro_prejuizo'] for op in self.operacoes]
        
        plt.figure(figsize=(10, 6))
        sns.histplot(lucros, bins=30)
        
        plt.title('Distribuição de Lucro/Prejuízo por Operação')
        plt.xlabel('Lucro/Prejuízo (USDT)')
        plt.ylabel('Frequência')
        plt.grid(True)
        
        # Adicionar linha vertical em x=0
        plt.axvline(x=0, color='r', linestyle='--', alpha=0.5)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        plt.savefig('graficos/distribuicao_lucro.png')
        plt.close()
    
    def plot_sequencias(self):
        """
        Gera gráfico de sequências de ganhos e perdas.
        """
        # Criar DataFrame com as operações
        df = pd.DataFrame(self.operacoes)
        
        # Converter timestamp para datetime
        df['data'] = pd.to_datetime(df['data'])
        
        # Ordenar por data
        df = df.sort_values('data')
        
        # Calcular sequências
        df['sequencia'] = 0
        sequencia_atual = 0
        
        for i in range(len(df)):
            if df['lucro_prejuizo'].iloc[i] > 0:
                sequencia_atual = max(0, sequencia_atual + 1)
            else:
                sequencia_atual = min(0, sequencia_atual - 1)
            df['sequencia'].iloc[i] = sequencia_atual
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['data'], df['sequencia'], label='Sequência')
        
        plt.title('Sequências de Ganhos e Perdas')
        plt.xlabel('Data')
        plt.ylabel('Sequência')
        plt.grid(True)
        plt.legend()
        
        # Rotacionar labels do eixo x para melhor visualização
        plt.xticks(rotation=45)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        plt.savefig('graficos/sequencias.png')
        plt.close()
    
    def gerar_todos_graficos(self):
        """
        Gera todos os gráficos do backtest.
        """
        print("\nGerando gráficos do backtest...")
        
        self.plot_curva_capital()
        self.plot_drawdown()
        self.plot_distribuicao_operacoes()
        self.plot_distribuicao_lucro()
        self.plot_sequencias()
        
        print("Gráficos gerados com sucesso na pasta 'graficos'!") 