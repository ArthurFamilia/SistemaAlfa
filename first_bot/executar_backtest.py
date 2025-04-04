#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar backtests do bot de trading.

Este script permite realizar backtests com diferentes configurações
e visualizar os resultados.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime

def executar_backtest(config):
    """
    Executa um backtest com as configurações fornecidas.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Iniciando backtest...")
    print("\n" + "="*60)
    print("   BACKTEST - ESTRATÉGIA DE TRADING")
    print("="*60)
    
    # Obter parâmetros do backtest
    par = config.get('TRADING_PAIR', 'BTCUSDT')
    timeframe = config.get('CANDLE_INTERVAL', '1h')
    dias = int(config.get('HISTORICO_DIAS', 30))
    position_size = float(config.get('POSITION_SIZE', 10.0))
    
    # Exibir configurações padrão
    print(f"Par de trading: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    print(f"Tamanho da posição: {position_size}")
    print("="*60)
    
    # Perguntar se deseja personalizar os parâmetros
    personalizar = input("\nDeseja personalizar os parâmetros do backtest? (s/N): ")
    
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
    
    # Verificar se backtest.py existe
    if not os.path.exists('backtest.py'):
        logger.error("Arquivo backtest.py não encontrado.")
        print("\nErro: arquivo backtest.py não encontrado no diretório atual.")
        print("Por favor, verifique se o arquivo existe na raiz do projeto.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Perguntar se deseja visualizar os gráficos
    visualizar_graficos = input("\nDeseja visualizar gráficos após o backtest? (s/N): ").lower() == 's'
    
    # Importar backtest
    try:
        print("\nImportando módulo de backtest...")
        from backtest import Backtest
        
        # Criar diretório de resultados se não existir
        os.makedirs('resultados/backtests', exist_ok=True)
        
        # Timestamp para identificar os resultados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_resultado = f"backtest_{par}_{timeframe}_{timestamp}"
        
        # Iniciar backtest
        print(f"\nIniciando backtest para {par} ({timeframe}) - {dias} dias...")
        print("Este processo pode demorar alguns minutos, dependendo da quantidade de dados.")
        print("Por favor, aguarde...")
        
        inicio = datetime.now()
        
        # Executar backtest
        backtest = Backtest(dias_historico=dias)
        resultado = backtest.executar(
            par=par,
            timeframe=timeframe,
            position_size=position_size
        )
        
        # Verificar resultados
        if not resultado:
            logger.error("Backtest falhou ao retornar resultados.")
            print("\nErro: O backtest não retornou resultados válidos.")
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        # Salvar resultados
        caminho_resultado = f"resultados/backtests/{nome_resultado}.json"
        
        with open(caminho_resultado, 'w') as f:
            json.dump(resultado.get('operacoes', []), f, indent=2)
        
        # Resumo dos resultados
        fim = datetime.now()
        duracao = fim - inicio
        
        print("\n" + "="*60)
        print("   RESULTADOS DO BACKTEST")
        print("="*60)
        print(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}")
        print(f"Total de operações: {resultado.get('total_operacoes', 0)}")
        print(f"Operações vencedoras: {resultado.get('operacoes_vencedoras', 0)}")
        print(f"Operações perdedoras: {resultado.get('operacoes_perdedoras', 0)}")
        print(f"Taxa de acerto: {resultado.get('taxa_acerto', 0):.2f}%")
        print(f"Lucro total: {resultado.get('lucro_total', 0):.2f}")
        print(f"Expectativa matemática: {resultado.get('expectativa_matematica', 0):.4f}")
        print(f"Fator de lucro: {resultado.get('fator_lucro', 0):.2f}")
        print(f"Maior drawdown: {resultado.get('max_drawdown', 0):.2f} ({resultado.get('drawdown_percentual', 0):.2f}%)")
        print("-"*60)
        print(f"Tempo de execução: {duracao.total_seconds():.2f} segundos")
        print(f"Resultados salvos em: {caminho_resultado}")
        print("="*60)
        
        # Visualizar gráficos se solicitado
        if visualizar_graficos:
            print("\nGerando gráficos...")
            try:
                # Tenta importar o módulo de gráficos
                import backtest_plots
                backtest_plots.gerar_graficos(resultado, nome_resultado)
                print("Gráficos gerados com sucesso!")
            except ImportError:
                print("Módulo backtest_plots não encontrado. Gráficos não puderam ser gerados.")
            except Exception as e:
                print(f"Erro ao gerar gráficos: {e}")
        
        # Perguntar se deseja exportar relatório detalhado
        exportar_relatorio = input("\nDeseja exportar um relatório detalhado? (s/N): ").lower() == 's'
        
        if exportar_relatorio:
            try:
                caminho_relatorio = f"resultados/backtests/{nome_resultado}_relatorio.txt"
                
                with open(caminho_relatorio, 'w') as f:
                    f.write("="*60 + "\n")
                    f.write("   RELATÓRIO DETALHADO DO BACKTEST\n")
                    f.write("="*60 + "\n")
                    f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}\n\n")
                    
                    # Métricas principais
                    f.write("MÉTRICAS PRINCIPAIS:\n")
                    f.write(f"Total de operações: {resultado.get('total_operacoes', 0)}\n")
                    f.write(f"Operações vencedoras: {resultado.get('operacoes_vencedoras', 0)}\n")
                    f.write(f"Operações perdedoras: {resultado.get('operacoes_perdedoras', 0)}\n")
                    f.write(f"Taxa de acerto: {resultado.get('taxa_acerto', 0):.2f}%\n")
                    f.write(f"Lucro total: {resultado.get('lucro_total', 0):.2f}\n")
                    f.write(f"Expectativa matemática: {resultado.get('expectativa_matematica', 0):.4f}\n")
                    f.write(f"Fator de lucro: {resultado.get('fator_lucro', 0):.2f}\n")
                    f.write(f"Maior drawdown: {resultado.get('max_drawdown', 0):.2f} ({resultado.get('drawdown_percentual', 0):.2f}%)\n\n")
                    
                    # Detalhes das operações
                    f.write("DETALHES DAS OPERAÇÕES:\n")
                    for i, op in enumerate(resultado.get('operacoes', []), 1):
                        f.write(f"Operação #{i}:\n")
                        f.write(f"  Tipo: {op.get('tipo', 'N/A')}\n")
                        f.write(f"  Entrada: {op.get('preco_entrada', 0):.2f}\n")
                        f.write(f"  Saída: {op.get('preco_saida', 0):.2f}\n")
                        f.write(f"  Resultado: {op.get('resultado', 0):.2f}\n")
                        f.write(f"  Data entrada: {op.get('data_entrada', 'N/A')}\n")
                        f.write(f"  Data saída: {op.get('data_saida', 'N/A')}\n")
                        f.write("\n")
                
                print(f"Relatório detalhado salvo em: {caminho_relatorio}")
            
            except Exception as e:
                print(f"Erro ao exportar relatório: {e}")
        
        print("\nBacktest concluído com sucesso!")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulo de backtest: {e}")
        print(f"\nErro ao importar módulo de backtest: {e}")
    except Exception as e:
        logger.error(f"Erro ao executar backtest: {e}", exc_info=True)
        print(f"\nErro ao executar backtest: {e}")
    
    input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 