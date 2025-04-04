#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuração Avançada para Bot de Trading

Este módulo permite configurações avançadas para:
- Backtest
- Minerador de estratégias
- Otimização bayesiana
- Configurações de indicadores técnicos
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union, Tuple, Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class ConfiguracaoAvancada:
    """
    Classe para configuração avançada do sistema de trading.
    
    Permite ao usuário definir parâmetros personalizados para backtests,
    mineração de estratégias e otimização bayesiana.
    """
    
    def __init__(self, logger=None):
        """
        Inicializa a configuração avançada.
        
        Args:
            logger: Logger para registrar informações (opcional)
        """
        # Configurar logger
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('config_avancada')
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        
        # Carregar configurações padrão
        self.carregar_configuracoes_padrao()
    
    def carregar_configuracoes_padrao(self):
        """Carrega as configurações padrão do arquivo .env e valores padrão."""
        # Configurações de backtest
        self.backtest_config = {
            'par': os.getenv('TRADING_PAIR', 'BTCUSDT'),
            'timeframe': os.getenv('CANDLE_INTERVAL', '1h'),
            'dias_historico': int(os.getenv('HISTORICO_DIAS', '30')),
            'position_size': float(os.getenv('POSITION_SIZE', '10.0')),
            'plotar_grafico': os.getenv('BACKTEST_PLOT', 'TRUE').upper() == 'TRUE',
            'salvar_resultados': os.getenv('BACKTEST_SAVE_RESULTS', 'TRUE').upper() == 'TRUE',
            'usar_dados_reais': True,
            'arquivo_dados': '',  # Caminho para arquivo CSV de dados (se usar_dados_reais=False)
            'data_inicio': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'data_fim': datetime.now().strftime('%Y-%m-%d'),
            'ignorar_periodos': [],  # Lista de períodos a ignorar (ex: finais de semana)
            'calcular_drawdown': True,
            'incluir_custos': True,
            'taxa_corretagem': 0.1,  # Em percentual
            'stop_loss_percentual': 2.0,
            'take_profit_percentual': 4.0,
            'trailing_stop': False,
            'trailing_stop_offset': 1.0
        }
        
        # Configurações do minerador de estratégias
        self.minerador_config = {
            'dias_historico': int(os.getenv('HISTORICO_DIAS', '30')),
            'pares': [os.getenv('TRADING_PAIR', 'BTCUSDT')],
            'timeframes': [os.getenv('CANDLE_INTERVAL', '1h')],
            'periodos_adx': [int(p) for p in os.getenv('ADX_PERIODS', '[8, 10, 12, 14]').strip('[]').split(',')],
            'limiares_adx': [float(t) for t in os.getenv('ADX_THRESHOLDS', '[22, 24, 26, 28, 30, 32]').strip('[]').split(',')],
            'periodos_di': [int(p) for p in os.getenv('DI_PLUS_PERIODS', '[8, 10, 12, 14]').strip('[]').split(',')],
            'limiares_di_plus': [float(t) for t in os.getenv('DI_PLUS_THRESHOLDS', '[5, 12.5, 20]').strip('[]').split(',')],
            'limiares_di_minus': [float(t) for t in os.getenv('DI_MINUS_THRESHOLDS', '[5, 12.5, 20]').strip('[]').split(',')],
            'multiplicadores_stop': [float(m) for m in os.getenv('STOP_MULTIPLIERS_BUY', '[1.5, 2.0, 2.5, 3.0]').strip('[]').split(',')],
            'multiplicadores_gain': [float(m) for m in os.getenv('GAIN_MULTIPLIERS_BUY', '[3.0, 4.0, 5.0, 6.0]').strip('[]').split(',')],
            'max_estrategias': 50,  # Número máximo de estratégias a testar
            'criterio_selecao': 'expectativa',  # expectativa, lucro_total, taxa_acerto, sharpe
            'num_resultados': 10,  # Número de melhores estratégias a mostrar
            'salvar_todas_estrategias': False,
            'salvar_apenas_lucrativas': True,
            'testar_robustez': True,  # Testar robustez em diferentes períodos
            'periodos_teste_robustez': ['1w', '2w', '1m'],  # Períodos para teste de robustez
            'indicadores_adicionais': [],  # Indicadores extras a considerar
            'usar_ml': True,  # Usar ML para classificar estratégias
            'usar_classificador_regimes': True  # Usar classificador de regimes
        }
        
        # Configurações da otimização bayesiana
        self.otimizacao_config = {
            'dias_historico': int(os.getenv('HISTORICO_DIAS', '60')),
            'par': os.getenv('TRADING_PAIR', 'BTCUSDT'),
            'timeframe': os.getenv('CANDLE_INTERVAL', '1h'),
            'n_calls': 30,  # Número de avaliações
            'n_random_starts': 10,  # Número de pontos aleatórios iniciais
            'espacos_busca': {
                'adx_period': (5, 20),
                'adx_threshold': (20.0, 40.0),
                'di_period': (5, 20),
                'di_threshold': (10.0, 30.0),
                'stop_multiplier': (1.0, 4.0),
                'gain_multiplier': (2.0, 8.0),
                'atr_period': (5, 20)
            },
            'espacos_categoricos': {
                'usar_trailing_stop': [True, False],
                'considerar_custo': [True, False]
            },
            'metrica_otimizacao': 'expectativa',  # expectativa, lucro_total, sharpe, sortino
            'numero_periodos_validacao': 3,  # Número de períodos para validação cruzada
            'usar_early_stopping': True,  # Parar otimização se não houver melhoria
            'early_stopping_rounds': 10,  # Número de rodadas sem melhoria para parar
            'salvar_historico_otimizacao': True,
            'plotar_grafico_convergencia': True
        }
        
        # Configurações dos indicadores técnicos
        self.indicadores_config = {
            'adx': {
                'period': int(os.getenv('ADX_PERIOD', '14')),
                'threshold': float(os.getenv('ADX_THRESHOLD', '25.0')),
                'previous_candles': int(os.getenv('ADX_PREVIOUS_CANDLES', '2'))
            },
            'di_plus': {
                'period': int(os.getenv('DI_PLUS_PERIOD', '14')),
                'threshold': float(os.getenv('DI_PLUS_THRESHOLD', '20.0'))
            },
            'di_minus': {
                'period': int(os.getenv('DI_MINUS_PERIOD', '14')),
                'threshold': float(os.getenv('DI_MINUS_THRESHOLD', '20.0'))
            },
            'atr': {
                'period': int(os.getenv('ATR_PERIOD', '14'))
            },
            'rsi': {
                'period': 14,
                'overbought': 70,
                'oversold': 30,
                'ativo': False
            },
            'macd': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'ativo': False
            },
            'bollinger': {
                'period': 20,
                'std_dev': 2.0,
                'ativo': False
            },
            'indicadores_personalizados': []
        }
    
    def modificar_config_backtest(self, **kwargs):
        """
        Modifica configurações de backtest.
        
        Args:
            **kwargs: Parâmetros a serem modificados
        """
        for key, value in kwargs.items():
            if key in self.backtest_config:
                self.backtest_config[key] = value
                self.logger.info(f"Configuração de backtest modificada: {key} = {value}")
            else:
                self.logger.warning(f"Configuração de backtest desconhecida: {key}")
    
    def modificar_config_minerador(self, **kwargs):
        """
        Modifica configurações do minerador de estratégias.
        
        Args:
            **kwargs: Parâmetros a serem modificados
        """
        for key, value in kwargs.items():
            if key in self.minerador_config:
                self.minerador_config[key] = value
                self.logger.info(f"Configuração do minerador modificada: {key} = {value}")
            else:
                self.logger.warning(f"Configuração do minerador desconhecida: {key}")
    
    def modificar_config_otimizacao(self, **kwargs):
        """
        Modifica configurações da otimização bayesiana.
        
        Args:
            **kwargs: Parâmetros a serem modificados
        """
        for key, value in kwargs.items():
            if key in self.otimizacao_config:
                self.otimizacao_config[key] = value
                self.logger.info(f"Configuração de otimização modificada: {key} = {value}")
            else:
                self.logger.warning(f"Configuração de otimização desconhecida: {key}")
    
    def modificar_config_indicadores(self, indicador, **kwargs):
        """
        Modifica configurações dos indicadores técnicos.
        
        Args:
            indicador: Nome do indicador (adx, di_plus, di_minus, atr, rsi, macd, bollinger)
            **kwargs: Parâmetros a serem modificados
        """
        if indicador in self.indicadores_config:
            for key, value in kwargs.items():
                if key in self.indicadores_config[indicador]:
                    self.indicadores_config[indicador][key] = value
                    self.logger.info(f"Configuração do indicador {indicador} modificada: {key} = {value}")
                else:
                    self.logger.warning(f"Configuração do indicador {indicador} desconhecida: {key}")
        else:
            self.logger.warning(f"Indicador desconhecido: {indicador}")
    
    def adicionar_indicador_personalizado(self, nome, parametros, funcao_calculo=None):
        """
        Adiciona um indicador técnico personalizado.
        
        Args:
            nome: Nome do indicador
            parametros: Dicionário com parâmetros do indicador
            funcao_calculo: Função para calcular o indicador (opcional)
        """
        indicador = {
            'nome': nome,
            'parametros': parametros,
            'funcao': funcao_calculo.__name__ if funcao_calculo else None
        }
        self.indicadores_config['indicadores_personalizados'].append(indicador)
        self.logger.info(f"Indicador personalizado adicionado: {nome}")
    
    def definir_espaco_busca_personalizado(self, parametro, intervalo, tipo='continuo'):
        """
        Define um espaço de busca personalizado para otimização bayesiana.
        
        Args:
            parametro: Nome do parâmetro
            intervalo: Tupla (min, max) ou lista de valores
            tipo: Tipo de espaço (continuo, inteiro, categorico)
        """
        if tipo == 'continuo' or tipo == 'inteiro':
            self.otimizacao_config['espacos_busca'][parametro] = intervalo
        elif tipo == 'categorico':
            self.otimizacao_config['espacos_categoricos'][parametro] = intervalo
        else:
            self.logger.warning(f"Tipo de espaço desconhecido: {tipo}")
        
        self.logger.info(f"Espaço de busca definido para {parametro}: {intervalo} ({tipo})")
    
    def salvar_configuracoes(self, arquivo):
        """
        Salva todas as configurações em um arquivo JSON.
        
        Args:
            arquivo: Caminho do arquivo para salvar as configurações
        """
        config = {
            'backtest': self.backtest_config,
            'minerador': self.minerador_config,
            'otimizacao': self.otimizacao_config,
            'indicadores': self.indicadores_config
        }
        
        with open(arquivo, 'w') as f:
            json.dump(config, f, indent=4)
        
        self.logger.info(f"Configurações salvas em: {arquivo}")
    
    def carregar_configuracoes(self, arquivo):
        """
        Carrega configurações de um arquivo JSON.
        
        Args:
            arquivo: Caminho do arquivo para carregar as configurações
        """
        try:
            with open(arquivo, 'r') as f:
                config = json.load(f)
            
            if 'backtest' in config:
                self.backtest_config.update(config['backtest'])
            
            if 'minerador' in config:
                self.minerador_config.update(config['minerador'])
            
            if 'otimizacao' in config:
                self.otimizacao_config.update(config['otimizacao'])
            
            if 'indicadores' in config:
                self.indicadores_config.update(config['indicadores'])
            
            self.logger.info(f"Configurações carregadas de: {arquivo}")
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {e}")
    
    def exportar_para_env(self, arquivo='.env.config'):
        """
        Exporta configurações para um arquivo .env.
        
        Args:
            arquivo: Caminho do arquivo .env para exportar configurações
        """
        with open(arquivo, 'w') as f:
            # Backtest configs
            f.write("# Configurações de backtest\n")
            f.write(f"TRADING_PAIR={self.backtest_config['par']}\n")
            f.write(f"CANDLE_INTERVAL={self.backtest_config['timeframe']}\n")
            f.write(f"HISTORICO_DIAS={self.backtest_config['dias_historico']}\n")
            f.write(f"POSITION_SIZE={self.backtest_config['position_size']}\n")
            f.write(f"BACKTEST_PLOT={'TRUE' if self.backtest_config['plotar_grafico'] else 'FALSE'}\n")
            f.write(f"BACKTEST_SAVE_RESULTS={'TRUE' if self.backtest_config['salvar_resultados'] else 'FALSE'}\n\n")
            
            # Indicadores
            f.write("# Configurações de indicadores\n")
            f.write(f"ADX_PERIOD={self.indicadores_config['adx']['period']}\n")
            f.write(f"ADX_THRESHOLD={self.indicadores_config['adx']['threshold']}\n")
            f.write(f"ADX_PREVIOUS_CANDLES={self.indicadores_config['adx']['previous_candles']}\n")
            f.write(f"DI_PLUS_PERIOD={self.indicadores_config['di_plus']['period']}\n")
            f.write(f"DI_PLUS_THRESHOLD={self.indicadores_config['di_plus']['threshold']}\n")
            f.write(f"DI_MINUS_PERIOD={self.indicadores_config['di_minus']['period']}\n")
            f.write(f"DI_MINUS_THRESHOLD={self.indicadores_config['di_minus']['threshold']}\n")
            f.write(f"ATR_PERIOD={self.indicadores_config['atr']['period']}\n\n")
            
            # Minerador
            f.write("# Configurações do minerador de estratégias\n")
            f.write(f"ADX_PERIODS={self.minerador_config['periodos_adx']}\n")
            f.write(f"ADX_THRESHOLDS={self.minerador_config['limiares_adx']}\n")
            f.write(f"DI_PLUS_PERIODS={self.minerador_config['periodos_di']}\n")
            f.write(f"DI_PLUS_THRESHOLDS={self.minerador_config['limiares_di_plus']}\n")
            f.write(f"DI_MINUS_THRESHOLDS={self.minerador_config['limiares_di_minus']}\n")
            f.write(f"STOP_MULTIPLIERS_BUY={self.minerador_config['multiplicadores_stop']}\n")
            f.write(f"GAIN_MULTIPLIERS_BUY={self.minerador_config['multiplicadores_gain']}\n\n")
            
            # Otimização
            f.write("# Configurações de otimização bayesiana\n")
            f.write(f"OTIMIZACAO_N_CALLS={self.otimizacao_config['n_calls']}\n")
            f.write(f"OTIMIZACAO_METRICA={self.otimizacao_config['metrica_otimizacao']}\n\n")
        
        self.logger.info(f"Configurações exportadas para: {arquivo}")

    def obter_config_backtest(self):
        """Retorna as configurações de backtest."""
        return self.backtest_config
    
    def obter_config_minerador(self):
        """Retorna as configurações do minerador de estratégias."""
        return self.minerador_config
    
    def obter_config_otimizacao(self):
        """Retorna as configurações da otimização bayesiana."""
        return self.otimizacao_config
    
    def obter_config_indicadores(self):
        """Retorna as configurações dos indicadores técnicos."""
        return self.indicadores_config

    def imprimir_configuracoes(self):
        """Imprime todas as configurações atuais."""
        print("\n=== CONFIGURAÇÕES DE BACKTEST ===")
        for key, value in self.backtest_config.items():
            print(f"{key}: {value}")
        
        print("\n=== CONFIGURAÇÕES DO MINERADOR DE ESTRATÉGIAS ===")
        for key, value in self.minerador_config.items():
            print(f"{key}: {value}")
        
        print("\n=== CONFIGURAÇÕES DE OTIMIZAÇÃO BAYESIANA ===")
        for key, value in self.otimizacao_config.items():
            print(f"{key}: {value}")
        
        print("\n=== CONFIGURAÇÕES DE INDICADORES TÉCNICOS ===")
        for indicador, config in self.indicadores_config.items():
            if indicador != 'indicadores_personalizados':
                print(f"\n{indicador.upper()}:")
                for param, valor in config.items():
                    print(f"  {param}: {valor}")
        
        if self.indicadores_config['indicadores_personalizados']:
            print("\nINDICADORES PERSONALIZADOS:")
            for ind in self.indicadores_config['indicadores_personalizados']:
                print(f"  {ind['nome']}: {ind['parametros']}")

# Função para criar uma instância da configuração avançada
def criar_configuracao():
    """Cria e retorna uma instância da configuração avançada."""
    return ConfiguracaoAvancada()

# Função para configuração interativa via console
def configuracao_interativa():
    """
    Executa um assistente interativo para configuração avançada.
    
    Returns:
        ConfiguracaoAvancada: Instância configurada
    """
    config = ConfiguracaoAvancada()
    
    print("\n===== ASSISTENTE DE CONFIGURAÇÃO AVANÇADA =====")
    print("Este assistente ajudará você a configurar o bot de trading.")
    
    # Configurar backtest
    print("\n--- CONFIGURAÇÃO DE BACKTEST ---")
    
    # Par de trading
    par = input(f"Par de trading [{config.backtest_config['par']}]: ")
    if par:
        config.modificar_config_backtest(par=par)
    
    # Timeframe
    timeframe = input(f"Timeframe [{config.backtest_config['timeframe']}]: ")
    if timeframe:
        config.modificar_config_backtest(timeframe=timeframe)
    
    # Dias históricos
    try:
        dias = input(f"Dias de histórico [{config.backtest_config['dias_historico']}]: ")
        if dias:
            config.modificar_config_backtest(dias_historico=int(dias))
    except ValueError:
        print("Valor inválido para dias históricos. Mantendo valor atual.")
    
    # Position size
    try:
        position_size = input(f"Position size [{config.backtest_config['position_size']}]: ")
        if position_size:
            config.modificar_config_backtest(position_size=float(position_size))
    except ValueError:
        print("Valor inválido para position size. Mantendo valor atual.")
    
    # Configurar indicadores
    print("\n--- CONFIGURAÇÃO DE INDICADORES ---")
    
    # ADX
    print("\nIndicador ADX:")
    try:
        adx_period = input(f"Período [{config.indicadores_config['adx']['period']}]: ")
        if adx_period:
            config.modificar_config_indicadores('adx', period=int(adx_period))
        
        adx_threshold = input(f"Limiar [{config.indicadores_config['adx']['threshold']}]: ")
        if adx_threshold:
            config.modificar_config_indicadores('adx', threshold=float(adx_threshold))
    except ValueError:
        print("Valor inválido para ADX. Mantendo valores atuais.")
    
    # Minerador de estratégias
    print("\n--- CONFIGURAÇÃO DO MINERADOR DE ESTRATÉGIAS ---")
    
    # Lista de thresholds ADX
    try:
        thresholds_str = input(f"Limiares ADX (separados por vírgula) {config.minerador_config['limiares_adx']}: ")
        if thresholds_str:
            limiares = [float(x.strip()) for x in thresholds_str.split(',')]
            config.modificar_config_minerador(limiares_adx=limiares)
    except ValueError:
        print("Formato inválido para limiares ADX. Mantendo valores atuais.")
    
    # Critério de seleção
    criterio = input(f"Critério de seleção (expectativa/lucro_total/taxa_acerto/sharpe) [{config.minerador_config['criterio_selecao']}]: ")
    if criterio in ['expectativa', 'lucro_total', 'taxa_acerto', 'sharpe']:
        config.modificar_config_minerador(criterio_selecao=criterio)
    
    # Otimização bayesiana
    print("\n--- CONFIGURAÇÃO DE OTIMIZAÇÃO BAYESIANA ---")
    
    # Número de chamadas
    try:
        n_calls = input(f"Número de avaliações [{config.otimizacao_config['n_calls']}]: ")
        if n_calls:
            config.modificar_config_otimizacao(n_calls=int(n_calls))
    except ValueError:
        print("Valor inválido para número de avaliações. Mantendo valor atual.")
    
    # Métrica de otimização
    metrica = input(f"Métrica de otimização (expectativa/lucro_total/sharpe/sortino) [{config.otimizacao_config['metrica_otimizacao']}]: ")
    if metrica in ['expectativa', 'lucro_total', 'sharpe', 'sortino']:
        config.modificar_config_otimizacao(metrica_otimizacao=metrica)
    
    # Salvar configurações
    salvar = input("\nDeseja salvar estas configurações? (s/n): ")
    if salvar.lower() == 's':
        arquivo = input("Nome do arquivo [config.json]: ") or "config.json"
        config.salvar_configuracoes(arquivo)
    
    print("\nConfiguração concluída!\n")
    return config

if __name__ == "__main__":
    # Executar configuração interativa quando o script é executado diretamente
    config = configuracao_interativa()
    config.imprimir_configuracoes() 