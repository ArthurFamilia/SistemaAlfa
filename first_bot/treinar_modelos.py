#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para treinar modelos de Machine Learning do bot.

Este script contém funções para treinar o classificador de regimes
de mercado e o filtro de sinais utilizados pelo bot.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime

def treinar_classificador_regime(config):
    """
    Treina o modelo de classificação de regime de mercado.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Iniciando treinamento do classificador de regime de mercado...")
    print("\n" + "="*60)
    print("   TREINAMENTO - CLASSIFICADOR DE REGIME DE MERCADO")
    print("="*60)
    
    # Obter parâmetros
    par = config.get('TRADING_PAIR', 'BTCUSDT')
    timeframe = config.get('CANDLE_INTERVAL', '1h')
    dias = int(config.get('HISTORICO_DIAS', 90))  # Usar mais dias para treinamento
    
    # Exibir configurações
    print(f"Par de trading: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    
    # Perguntar se deseja personalizar os parâmetros
    personalizar = input("\nDeseja personalizar os parâmetros de treinamento? (s/N): ")
    
    if personalizar.lower() == 's':
        # Obter novos parâmetros
        novo_par = input(f"Par de trading [{par}]: ").strip()
        par = novo_par if novo_par else par
        
        novo_timeframe = input(f"Timeframe [{timeframe}]: ").strip()
        timeframe = novo_timeframe if novo_timeframe else timeframe
        
        try:
            novo_dias = input(f"Dias de histórico [{dias}]: ").strip()
            dias = int(novo_dias) if novo_dias else dias
        except ValueError:
            print("Valor inválido para dias. Usando o valor padrão.")
        
        print("\nParâmetros atualizados:")
        print(f"Par de trading: {par}")
        print(f"Timeframe: {timeframe}")
        print(f"Dias de histórico: {dias}")
    
    # Criar diretório para modelos se não existir
    os.makedirs('modelos/regimes', exist_ok=True)
    
    # Timestamp para nome do modelo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_modelo = f"classificador_regimes_{par}_{timeframe}_{timestamp}.joblib"
    caminho_modelo = os.path.join('modelos/regimes', nome_modelo)
    
    try:
        # Importar módulos necessários
        print("\nImportando módulos necessários...")
        
        try:
            from src.services.binance_service import BinanceService
            from src.utils.utils import calcular_indicadores_df
            from src.ml.classificador_regimes import ClassificadorRegimeMercado
        except ImportError as e:
            logger.error(f"Erro ao importar módulos necessários: {e}")
            print(f"\nErro ao importar módulos necessários: {e}")
            print("Verifique se todos os arquivos do projeto estão disponíveis.")
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        # Iniciar processo de treinamento
        print(f"\nIniciando treinamento para {par} ({timeframe}) - {dias} dias...")
        print("Este processo pode demorar alguns minutos, dependendo da quantidade de dados.")
        print("Por favor, aguarde...")
        
        inicio = datetime.now()
        
        # Obter dados históricos da Binance
        print("\nObtendo dados históricos da Binance...")
        binance_service = BinanceService()
        df = binance_service.get_historical_klines(
            symbol=par,
            interval=timeframe,
            start_str=f"{dias} days ago UTC"
        )
        
        if df is None or df.empty:
            logger.error("Não foi possível obter dados históricos da Binance.")
            print("\nErro: Não foi possível obter dados históricos da Binance.")
            print("Verifique sua conexão com a internet e tente novamente.")
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        print(f"Dados obtidos: {len(df)} registros")
        
        # Calcular indicadores
        print("\nCalculando indicadores técnicos...")
        df = calcular_indicadores_df(df)
        
        # Parâmetros do modelo
        print("\nConfigurando parâmetros do modelo...")
        try:
            n_clusters = int(input("Número de regimes a identificar [3]: ").strip() or "3")
            if n_clusters < 2:
                n_clusters = 2
                print("Valor mínimo é 2. Usando 2.")
            elif n_clusters > 10:
                n_clusters = 10
                print("Valor máximo é 10. Usando 10.")
        except ValueError:
            n_clusters = 3
            print("Valor inválido. Usando o valor padrão de 3 regimes.")
        
        # Inicializar e treinar o modelo
        print("\nIniciando treinamento do modelo...")
        classificador = ClassificadorRegimeMercado(n_clusters=n_clusters)
        classificador.treinar(df=df, verboso=True)
        
        # Salvar modelo
        print(f"\nSalvando modelo em: {caminho_modelo}")
        classificador.salvar_modelo(caminho_modelo)
        
        # Também salvar na localização padrão para uso pelo bot
        caminho_padrao = os.getenv('MODELO_CLASSIFICADOR', 'modelos/regimes/classificador_regimes.joblib')
        classificador.salvar_modelo(caminho_padrao)
        print(f"Modelo também salvo na localização padrão: {caminho_padrao}")
        
        # Resumo do treinamento
        fim = datetime.now()
        duracao = fim - inicio
        
        print("\n" + "="*60)
        print("   TREINAMENTO CONCLUÍDO")
        print("="*60)
        print(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}")
        print(f"Número de regimes: {n_clusters}")
        print(f"Registros processados: {len(df)}")
        print(f"Modelo salvo em: {caminho_modelo}")
        print(f"Tempo de treinamento: {duracao.total_seconds():.2f} segundos")
        
        # Mostrar distribuição de regimes
        if hasattr(classificador, 'distribuicao_regimes') and classificador.distribuicao_regimes is not None:
            print("\nDistribuição de regimes identificados:")
            for regime, contagem in classificador.distribuicao_regimes.items():
                percentual = (contagem / len(df)) * 100
                print(f"  Regime {regime}: {contagem} registros ({percentual:.2f}%)")
        
        # Visualizar resultados
        visualizar = input("\nDeseja visualizar os regimes identificados em um gráfico? (s/N): ").lower() == 's'
        
        if visualizar:
            try:
                print("\nGerando visualização...")
                classificador.visualizar(df, par=par, timeframe=timeframe)
                print("Visualização gerada. Verifique a janela de gráfico aberta.")
            except Exception as e:
                print(f"Erro ao gerar visualização: {e}")
        
        print("\nTreinamento concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao treinar classificador de regime: {e}", exc_info=True)
        print(f"\nErro ao treinar classificador de regime: {e}")
    
    input("\nPressione Enter para retornar ao menu principal...")

def treinar_filtro_sinais(config):
    """
    Treina o modelo de filtro de sinais de trading.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Iniciando treinamento do filtro de sinais...")
    print("\n" + "="*60)
    print("   TREINAMENTO - FILTRO DE SINAIS")
    print("="*60)
    
    # Obter parâmetros
    par = config.get('TRADING_PAIR', 'BTCUSDT')
    timeframe = config.get('CANDLE_INTERVAL', '1h')
    dias = int(config.get('HISTORICO_DIAS', 90))  # Usar mais dias para treinamento
    
    # Exibir configurações
    print(f"Par de trading: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    
    # Perguntar se deseja personalizar os parâmetros
    personalizar = input("\nDeseja personalizar os parâmetros de treinamento? (s/N): ")
    
    if personalizar.lower() == 's':
        # Obter novos parâmetros
        novo_par = input(f"Par de trading [{par}]: ").strip()
        par = novo_par if novo_par else par
        
        novo_timeframe = input(f"Timeframe [{timeframe}]: ").strip()
        timeframe = novo_timeframe if novo_timeframe else timeframe
        
        try:
            novo_dias = input(f"Dias de histórico [{dias}]: ").strip()
            dias = int(novo_dias) if novo_dias else dias
        except ValueError:
            print("Valor inválido para dias. Usando o valor padrão.")
        
        print("\nParâmetros atualizados:")
        print(f"Par de trading: {par}")
        print(f"Timeframe: {timeframe}")
        print(f"Dias de histórico: {dias}")
    
    # Verificar se backtest.py existe
    if not os.path.exists('backtest.py'):
        logger.error("Arquivo backtest.py não encontrado.")
        print("\nErro: arquivo backtest.py não encontrado no diretório atual.")
        print("Por favor, verifique se o arquivo existe na raiz do projeto.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Criar diretório para modelos se não existir
    os.makedirs('modelos/filtro_sinais', exist_ok=True)
    
    # Timestamp para nome do modelo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_modelo = f"filtro_sinais_{par}_{timeframe}_{timestamp}.joblib"
    caminho_modelo = os.path.join('modelos/filtro_sinais', nome_modelo)
    
    try:
        # Importar módulos necessários
        print("\nImportando módulos necessários...")
        
        try:
            from backtest import Backtest
            from src.ml.filtro_sinais import FiltroSinaisXGBoost
        except ImportError as e:
            logger.error(f"Erro ao importar módulos necessários: {e}")
            print(f"\nErro ao importar módulos necessários: {e}")
            print("Verifique se todos os arquivos do projeto estão disponíveis.")
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        # Iniciar processo de treinamento
        print(f"\nIniciando treinamento para {par} ({timeframe}) - {dias} dias...")
        print("Este processo tem duas etapas:")
        print("1. Executar backtest para gerar sinais de treinamento")
        print("2. Treinar o modelo de filtro com os sinais gerados")
        print("Por favor, aguarde...")
        
        inicio = datetime.now()
        
        # Executar backtest para obter dados de treinamento
        print("\nExecutando backtest para gerar sinais de treinamento...")
        backtest = Backtest(dias_historico=dias)
        resultado = backtest.executar(
            par=par,
            timeframe=timeframe,
            position_size=100.0  # Valor arbitrário para backtest
        )
        
        if not resultado or 'operacoes' not in resultado:
            logger.error("Backtest não retornou operações para treinamento.")
            print("\nErro: O backtest não retornou operações válidas para treinamento.")
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        operacoes = resultado.get('operacoes', [])
        print(f"Operações obtidas para treinamento: {len(operacoes)}")
        
        if len(operacoes) < 10:
            logger.warning("Poucas operações para treinamento efetivo.")
            print("\nAviso: Apenas {len(operacoes)} operações foram geradas para treinamento.")
            print("O ideal é ter pelo menos 50 operações para um treinamento efetivo.")
            continuar = input("Deseja continuar mesmo assim? (s/N): ")
            if continuar.lower() != 's':
                print("Treinamento cancelado pelo usuário.")
                input("\nPressione Enter para retornar ao menu principal...")
                return
        
        # Configurar e treinar o filtro
        print("\nConfigurando modelo de filtro...")
        try:
            test_size = float(input("Proporção de dados para teste (0.1-0.3) [0.2]: ").strip() or "0.2")
            if test_size < 0.1:
                test_size = 0.1
                print("Valor mínimo é 0.1 (10%). Usando 0.1.")
            elif test_size > 0.3:
                test_size = 0.3
                print("Valor máximo é 0.3 (30%). Usando 0.3.")
        except ValueError:
            test_size = 0.2
            print("Valor inválido. Usando o valor padrão de 0.2 (20%).")
        
        # Inicializar e treinar o modelo
        print("\nIniciando treinamento do filtro de sinais...")
        filtro = FiltroSinaisXGBoost(test_size=test_size)
        filtro.treinar(operacoes, par=par, timeframe=timeframe, verbose=True)
        
        # Salvar modelo
        print(f"\nSalvando modelo em: {caminho_modelo}")
        filtro.salvar_modelo(caminho_modelo)
        
        # Também salvar na localização padrão para uso pelo bot
        caminho_padrao = os.getenv('MODELO_FILTRO', 'modelos/filtro_sinais/filtro_sinais.joblib')
        filtro.salvar_modelo(caminho_padrao)
        print(f"Modelo também salvo na localização padrão: {caminho_padrao}")
        
        # Avaliar modelo
        print("\nAvaliando desempenho do modelo...")
        metricas = filtro.avaliar()
        
        # Resumo do treinamento
        fim = datetime.now()
        duracao = fim - inicio
        
        print("\n" + "="*60)
        print("   TREINAMENTO CONCLUÍDO")
        print("="*60)
        print(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}")
        print(f"Operações processadas: {len(operacoes)}")
        print(f"Proporção de teste: {test_size:.2f} ({int(len(operacoes) * test_size)} operações)")
        print(f"Modelo salvo em: {caminho_modelo}")
        print(f"Tempo de treinamento: {duracao.total_seconds():.2f} segundos")
        
        # Exibir métricas
        print("\nMétricas de desempenho do modelo:")
        for metrica, valor in metricas.items():
            if isinstance(valor, float):
                print(f"  {metrica}: {valor:.4f}")
            else:
                print(f"  {metrica}: {valor}")
        
        # Visualizar resultados
        visualizar = input("\nDeseja visualizar a importância das features? (s/N): ").lower() == 's'
        
        if visualizar:
            try:
                print("\nGerando visualização...")
                filtro.visualizar_importancia_features()
                print("Visualização gerada. Verifique a janela de gráfico aberta.")
            except Exception as e:
                print(f"Erro ao gerar visualização: {e}")
        
        print("\nTreinamento concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao treinar filtro de sinais: {e}", exc_info=True)
        print(f"\nErro ao treinar filtro de sinais: {e}")
    
    input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 