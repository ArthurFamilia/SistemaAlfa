#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para otimização de parâmetros dos indicadores técnicos.

Este script utiliza otimização bayesiana para encontrar os melhores
parâmetros para os indicadores técnicos utilizados pelo bot.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime

def otimizar_parametros(config):
    """
    Otimiza os parâmetros dos indicadores técnicos.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Iniciando otimização de parâmetros...")
    print("\n" + "="*60)
    print("   OTIMIZAÇÃO DE PARÂMETROS")
    print("="*60)
    
    # Verificar se o arquivo de otimização bayesiana existe
    try:
        from src.ml.otimizacao_bayesiana import OtimizadorBayesiano, criar_espaco_busca_adx
    except ImportError:
        logger.error("Módulo de otimização bayesiana não encontrado.")
        print("\nErro: Módulo de otimização bayesiana não encontrado.")
        print("Verifique se o arquivo src/ml/otimizacao_bayesiana.py existe.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Verificar se backtest.py existe
    if not os.path.exists('backtest.py'):
        logger.error("Arquivo backtest.py não encontrado.")
        print("\nErro: arquivo backtest.py não encontrado no diretório atual.")
        print("Por favor, verifique se o arquivo existe na raiz do projeto.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Obter parâmetros
    par = config.get('TRADING_PAIR', 'BTCUSDT')
    timeframe = config.get('CANDLE_INTERVAL', '1h')
    dias = int(config.get('HISTORICO_DIAS', 60))
    position_size = float(config.get('POSITION_SIZE', 10.0))
    
    # Exibir configurações
    print(f"Par de trading: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    print(f"Tamanho da posição: {position_size}")
    
    # Perguntar se deseja personalizar os parâmetros
    personalizar = input("\nDeseja personalizar os parâmetros de otimização? (s/N): ")
    
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
        
        try:
            novo_position_size = input(f"Tamanho da posição [{position_size}]: ").strip()
            position_size = float(novo_position_size) if novo_position_size else position_size
        except ValueError:
            print("Valor inválido para tamanho da posição. Usando o valor padrão.")
        
        print("\nParâmetros atualizados:")
        print(f"Par de trading: {par}")
        print(f"Timeframe: {timeframe}")
        print(f"Dias de histórico: {dias}")
        print(f"Tamanho da posição: {position_size}")
    
    # Criar diretório para resultados se não existir
    os.makedirs('resultados/otimizacao', exist_ok=True)
    os.makedirs('modelos/otimizador', exist_ok=True)
    
    # Timestamp para identificar os resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Importar módulos necessários
        print("\nImportando módulos necessários...")
        from backtest import Backtest
        
        # Configurar função objetivo para otimização
        def funcao_objetivo(**params):
            """
            Função objetivo para otimização bayesiana.
            
            Args:
                params: Parâmetros a serem avaliados
                
            Returns:
                float: Valor negativo da expectativa matemática (para minimização)
            """
            try:
                # Executar backtest com os parâmetros fornecidos
                backtest = Backtest(dias_historico=dias)
                resultado = backtest.executar(
                    par=par,
                    timeframe=timeframe,
                    position_size=position_size,
                    **params  # Passar parâmetros para otimização
                )
                
                # Obter métrica para otimização
                expectativa = resultado.get('expectativa_matematica', 0)
                
                # Retornar valor negativo para minimização (otimizador minimiza por padrão)
                return -expectativa
            except Exception as e:
                # Em caso de erro, retornar um valor muito alto para penalizar
                logger.error(f"Erro na avaliação dos parâmetros: {e}")
                return 1000.0  # Valor alto para ser descartado pelo otimizador
        
        # Configurar parâmetros da otimização
        print("\nConfigurando parâmetros da otimização...")
        
        # Número de avaliações
        try:
            n_calls = int(input("Número de avaliações a realizar [30]: ").strip() or "30")
            if n_calls < 10:
                n_calls = 10
                print("Valor mínimo é 10. Usando 10.")
            elif n_calls > 100:
                print("Aviso: Valores altos podem levar muito tempo para completar.")
                confirmar = input("Deseja continuar com um número elevado de avaliações? (s/N): ")
                if confirmar.lower() != 's':
                    n_calls = 50
                    print(f"Usando valor mais moderado: {n_calls}")
        except ValueError:
            n_calls = 30
            print("Valor inválido. Usando valor padrão de 30 avaliações.")
        
        # Confirmação final
        print("\nConfiguração da otimização:")
        print(f"Par: {par}")
        print(f"Timeframe: {timeframe}")
        print(f"Dias de histórico: {dias}")
        print(f"Avaliações: {n_calls}")
        print("\nAVISO: Esse processo pode demorar bastante tempo dependendo do")
        print("número de avaliações e dos dias de histórico escolhidos.")
        
        confirmar = input("\nDeseja iniciar a otimização? (s/N): ")
        if confirmar.lower() != 's':
            print("Otimização cancelada pelo usuário.")
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        # Criar espaço de busca para ADX
        print("\nCriando espaço de busca para parâmetros...")
        espaco_busca = criar_espaco_busca_adx()
        
        # Exibir espaço de busca
        print("\nEspaço de busca criado:")
        for param in espaco_busca:
            nome = param.name
            if hasattr(param, 'bounds'):
                bounds = param.bounds
                print(f"  {nome}: entre {bounds[0]} e {bounds[1]}")
            elif hasattr(param, 'categories'):
                categories = param.categories
                print(f"  {nome}: {categories}")
            else:
                print(f"  {nome}")
        
        # Iniciar processo de otimização
        print(f"\nIniciando otimização bayesiana com {n_calls} avaliações...")
        print("Por favor, aguarde. Este processo pode demorar vários minutos.")
        
        inicio = datetime.now()
        
        # Criar e executar otimizador
        otimizador = OtimizadorBayesiano(
            funcao_objetivo=funcao_objetivo,
            espaco_busca=espaco_busca,
            n_calls=n_calls,
            diretorio_resultados=f'resultados/otimizacao/otim_{par}_{timeframe}_{timestamp}'
        )
        
        # Executar otimização
        print("\nExecutando otimização...")
        melhores_parametros = otimizador.otimizar(verbose=True)
        
        # Salvar resultados
        print("\nSalvando resultados da otimização...")
        
        # Salvar em arquivo específico
        caminho_resultados = f'resultados/otimizacao/otim_{par}_{timeframe}_{timestamp}.json'
        
        with open(caminho_resultados, 'w') as f:
            json.dump({
                'parametros': melhores_parametros,
                'data_otimizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'par': par,
                'timeframe': timeframe,
                'dias_historico': dias,
                'n_calls': n_calls
            }, f, indent=2)
        
        # Salvar também na localização padrão para o bot
        caminho_padrao = os.getenv('PARAMS_OTIMIZADOS', 'modelos/otimizador/params_otimizados.json')
        
        with open(caminho_padrao, 'w') as f:
            json.dump({
                'parametros': melhores_parametros,
                'data_otimizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'par': par,
                'timeframe': timeframe,
                'dias_historico': dias,
                'n_calls': n_calls
            }, f, indent=2)
        
        # Executar backtest com os melhores parâmetros
        print("\nExecutando backtest com os parâmetros otimizados...")
        backtest = Backtest(dias_historico=dias)
        resultado_otimizado = backtest.executar(
            par=par,
            timeframe=timeframe,
            position_size=position_size,
            **melhores_parametros
        )
        
        # Resumo da otimização
        fim = datetime.now()
        duracao = fim - inicio
        horas, resto = divmod(duracao.total_seconds(), 3600)
        minutos, segundos = divmod(resto, 60)
        
        print("\n" + "="*60)
        print("   OTIMIZAÇÃO CONCLUÍDA")
        print("="*60)
        print(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}")
        print(f"Avaliações realizadas: {n_calls}")
        print(f"Tempo de otimização: {int(horas)}h {int(minutos)}m {int(segundos)}s")
        print(f"Resultados salvos em: {caminho_resultados}")
        print(f"Parâmetros também salvos em: {caminho_padrao}")
        
        print("\nMelhores parâmetros encontrados:")
        for param, valor in melhores_parametros.items():
            print(f"  {param}: {valor}")
        
        print("\nDesempenho com parâmetros otimizados:")
        for metrica, valor in [
            ("Total de operações", resultado_otimizado.get('total_operacoes', 0)),
            ("Taxa de acerto", f"{resultado_otimizado.get('taxa_acerto', 0):.2f}%"),
            ("Expectativa matemática", f"{resultado_otimizado.get('expectativa_matematica', 0):.4f}"),
            ("Lucro total", f"{resultado_otimizado.get('lucro_total', 0):.2f}"),
            ("Drawdown máximo", f"{resultado_otimizado.get('max_drawdown', 0):.2f} ({resultado_otimizado.get('drawdown_percentual', 0):.2f}%)")
        ]:
            print(f"  {metrica}: {valor}")
        
        # Visualizar resultados
        visualizar = input("\nDeseja visualizar os resultados da otimização? (s/N): ").lower() == 's'
        
        if visualizar:
            try:
                print("\nGerando visualização...")
                otimizador.plotar_resultados()
                print("Visualização gerada. Verifique a janela de gráfico aberta.")
            except Exception as e:
                print(f"Erro ao gerar visualização: {e}")
        
        print("\nOtimização concluída com sucesso!")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários: {e}")
        print(f"\nErro ao importar módulos necessários: {e}")
        print("Verifique se todos os arquivos do projeto estão disponíveis.")
    except Exception as e:
        logger.error(f"Erro ao otimizar parâmetros: {e}", exc_info=True)
        print(f"\nErro ao otimizar parâmetros: {e}")
    
    input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 