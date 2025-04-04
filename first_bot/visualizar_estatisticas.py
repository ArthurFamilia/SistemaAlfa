#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para visualizar estatísticas de backtests.

Este script permite visualizar os resultados dos backtests realizados,
incluindo métricas de desempenho, operações e gráficos.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime

def ver_estatisticas():
    """
    Exibe estatísticas dos backtests realizados.
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Visualizando estatísticas de backtests...")
    print("\n" + "="*60)
    print("   ESTATÍSTICAS DE BACKTESTS")
    print("="*60)
    
    # Verificar diretório de resultados
    diretorio = 'resultados/backtests'
    if not os.path.exists(diretorio):
        logger.warning(f"Diretório de backtests não encontrado: {diretorio}")
        print(f"Diretório de backtests não encontrado: {diretorio}")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Listar arquivos de backtest
    arquivos = os.listdir(diretorio)
    arquivos_backtest = [a for a in arquivos if a.startswith('backtest_') and a.endswith('.json')]
    
    if not arquivos_backtest:
        logger.warning("Nenhum arquivo de backtest encontrado.")
        print("Nenhum arquivo de backtest encontrado.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Ordenar por data (mais recentes primeiro)
    arquivos_backtest.sort(reverse=True)
    
    # Exibir lista de backtests disponíveis
    print("\nBacktests disponíveis:")
    for i, arquivo in enumerate(arquivos_backtest[:10], 1):  # Mostrar apenas os 10 mais recentes
        # Extrair informações do nome do arquivo (backtest_PAR_TIMEFRAME_DATA.json)
        partes = arquivo.replace('backtest_', '').replace('.json', '').split('_')
        par = partes[0] if len(partes) > 0 else "Desconhecido"
        timeframe = partes[1] if len(partes) > 1 else "?"
        
        # Tentar extrair a data
        try:
            if len(partes) >= 4:
                data_str = f"{partes[2]}_{partes[3]}"
                data = datetime.strptime(data_str, '%Y%m%d_%H%M%S')
                data_formatada = data.strftime('%d/%m/%Y %H:%M')
            else:
                data_formatada = "Data desconhecida"
        except:
            data_formatada = "Data desconhecida"
        
        print(f"[{i}] {par}/{timeframe} - {data_formatada}")
    
    if len(arquivos_backtest) > 10:
        print(f"... mais {len(arquivos_backtest) - 10} backtest(s) disponíveis")
    
    # Solicitar escolha do usuário
    try:
        escolha = int(input("\nEscolha um backtest para visualizar [1]: ").strip() or "1")
        if escolha < 1 or escolha > len(arquivos_backtest):
            print(f"Opção inválida. Usando a opção 1.")
            escolha = 1
    except ValueError:
        print("Valor inválido. Usando a opção 1.")
        escolha = 1
    
    # Carregar arquivo escolhido
    arquivo_escolhido = arquivos_backtest[escolha - 1]
    caminho_arquivo = os.path.join(diretorio, arquivo_escolhido)
    
    try:
        print(f"\nCarregando arquivo: {arquivo_escolhido}")
        with open(caminho_arquivo, 'r') as f:
            dados = json.load(f)
        
        # Extrair metadados do nome do arquivo
        partes = arquivo_escolhido.replace('backtest_', '').replace('.json', '').split('_')
        par = partes[0] if len(partes) > 0 else "Desconhecido"
        timeframe = partes[1] if len(partes) > 1 else "?"
        
        # Verificar formato dos dados
        if isinstance(dados, dict):
            # Formato mais recente (dicionário com métricas)
            print("\n" + "="*60)
            print(f"   RESULTADOS DO BACKTEST: {par}/{timeframe}")
            print("="*60)
            
            # Métricas de desempenho
            if 'metricas' in dados:
                print("\nMétricas de desempenho:")
                for metrica, valor in dados['metricas'].items():
                    # Formatar valores conforme o tipo
                    if isinstance(valor, (int, float)):
                        if metrica.endswith('percentual'):
                            print(f"  {metrica}: {valor:.2f}%")
                        else:
                            print(f"  {metrica}: {valor:.4f}")
                    else:
                        print(f"  {metrica}: {valor}")
            
            # Resumo de operações
            if 'resumo' in dados:
                print("\nResumo de operações:")
                for chave, valor in dados['resumo'].items():
                    print(f"  {chave}: {valor}")
            
            # Operações
            if 'operacoes' in dados and isinstance(dados['operacoes'], list):
                total_operacoes = len(dados['operacoes'])
                print(f"\nTotal de operações: {total_operacoes}")
                
                # Perguntar se deseja ver detalhes das operações
                ver_operacoes = input("\nDeseja ver detalhes das operações? (s/N): ").lower() == 's'
                
                if ver_operacoes and total_operacoes > 0:
                    print("\n" + "="*60)
                    print("   DETALHES DAS OPERAÇÕES")
                    print("="*60)
                    
                    # Número de operações para exibir
                    try:
                        num_exibir = int(input(f"Quantas operações deseja visualizar? (máx. {total_operacoes}) [10]: ").strip() or "10")
                        if num_exibir < 1:
                            num_exibir = 10
                        if num_exibir > total_operacoes:
                            num_exibir = total_operacoes
                    except ValueError:
                        num_exibir = 10
                        if num_exibir > total_operacoes:
                            num_exibir = total_operacoes
                    
                    # Exibir operações
                    for i, op in enumerate(dados['operacoes'][:num_exibir], 1):
                        resultado = op.get('resultado', 0)
                        resultado_str = f"{resultado:.2f}" if resultado >= 0 else f"{resultado:.2f}"
                        
                        print(f"\nOperação #{i}:")
                        print(f"  Tipo: {op.get('tipo', 'N/A')}")
                        print(f"  Entrada: {op.get('preco_entrada', 0):.4f}")
                        print(f"  Saída: {op.get('preco_saida', 0):.4f}")
                        print(f"  Resultado: {resultado_str}")
                        print(f"  Data entrada: {op.get('data_entrada', 'N/A')}")
                        print(f"  Data saída: {op.get('data_saida', 'N/A')}")
        
        elif isinstance(dados, list):
            # Formato antigo (lista de operações)
            total_operacoes = len(dados)
            ganhos = sum(1 for op in dados if op.get('resultado', 0) > 0)
            perdas = sum(1 for op in dados if op.get('resultado', 0) < 0)
            
            lucro_total = sum(op.get('resultado', 0) for op in dados)
            
            # Calcular métricas adicionais
            if ganhos > 0 and perdas > 0:
                media_ganhos = sum(op.get('resultado', 0) for op in dados if op.get('resultado', 0) > 0) / ganhos
                media_perdas = abs(sum(op.get('resultado', 0) for op in dados if op.get('resultado', 0) < 0) / perdas)
                relacao_lucro_prejuizo = media_ganhos / media_perdas if media_perdas > 0 else 0
                expectativa_matematica = (ganhos/total_operacoes * media_ganhos - perdas/total_operacoes * media_perdas) if total_operacoes > 0 else 0
            else:
                media_ganhos = 0
                media_perdas = 0
                relacao_lucro_prejuizo = 0
                expectativa_matematica = 0
            
            # Calcular drawdowns
            saldo = 0
            pico = 0
            drawdown_atual = 0
            max_drawdown = 0
            
            for op in dados:
                resultado = op.get('resultado', 0)
                saldo += resultado
                
                if saldo > pico:
                    pico = saldo
                    drawdown_atual = 0
                else:
                    drawdown_atual = pico - saldo
                    if drawdown_atual > max_drawdown:
                        max_drawdown = drawdown_atual
            
            drawdown_percentual = (max_drawdown / pico * 100) if pico > 0 else 0
            
            print("\n" + "="*60)
            print(f"   RESULTADOS DO BACKTEST: {par}/{timeframe}")
            print("="*60)
            print(f"Total de operações: {total_operacoes}")
            print(f"Operações vencedoras: {ganhos} ({ganhos/total_operacoes*100:.2f}% do total)")
            print(f"Operações perdedoras: {perdas} ({perdas/total_operacoes*100:.2f}% do total)")
            print(f"Taxa de acerto: {ganhos/total_operacoes*100:.2f}%")
            print(f"Lucro total: {lucro_total:.2f}")
            print(f"Média de ganhos: {media_ganhos:.2f}")
            print(f"Média de perdas: {media_perdas:.2f}")
            print(f"Relação lucro/prejuízo: {relacao_lucro_prejuizo:.2f}")
            print(f"Expectativa matemática: {expectativa_matematica:.4f}")
            print(f"Máximo drawdown: {max_drawdown:.2f} ({drawdown_percentual:.2f}%)")
            
            # Perguntar se deseja ver detalhes das operações
            ver_operacoes = input("\nDeseja ver detalhes das operações? (s/N): ").lower() == 's'
            
            if ver_operacoes and total_operacoes > 0:
                print("\n" + "="*60)
                print("   DETALHES DAS OPERAÇÕES")
                print("="*60)
                
                # Número de operações para exibir
                try:
                    num_exibir = int(input(f"Quantas operações deseja visualizar? (máx. {total_operacoes}) [10]: ").strip() or "10")
                    if num_exibir < 1:
                        num_exibir = 10
                    if num_exibir > total_operacoes:
                        num_exibir = total_operacoes
                except ValueError:
                    num_exibir = 10
                    if num_exibir > total_operacoes:
                        num_exibir = total_operacoes
                
                # Exibir operações
                for i, op in enumerate(dados[:num_exibir], 1):
                    resultado = op.get('resultado', 0)
                    resultado_str = f"{resultado:.2f}" if resultado >= 0 else f"{resultado:.2f}"
                    
                    print(f"\nOperação #{i}:")
                    print(f"  Tipo: {op.get('tipo', 'N/A')}")
                    print(f"  Entrada: {op.get('preco_entrada', 0):.4f}")
                    print(f"  Saída: {op.get('preco_saida', 0):.4f}")
                    print(f"  Resultado: {resultado_str}")
                    print(f"  Data entrada: {op.get('data_entrada', 'N/A')}")
                    print(f"  Data saída: {op.get('data_saida', 'N/A')}")
        
        # Perguntar se deseja visualizar gráficos
        visualizar_graficos = input("\nDeseja visualizar gráficos do backtest? (s/N): ").lower() == 's'
        
        if visualizar_graficos:
            try:
                print("\nGerando gráficos...")
                # Tenta importar o módulo de gráficos
                import backtest_plots
                backtest_plots.gerar_graficos(dados, arquivo_escolhido.replace('.json', ''))
                print("Gráficos gerados com sucesso!")
            except ImportError:
                print("Módulo backtest_plots não encontrado. Gráficos não puderam ser gerados.")
            except Exception as e:
                print(f"Erro ao gerar gráficos: {e}")
    
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        print(f"Erro: Arquivo não encontrado: {caminho_arquivo}")
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do arquivo: {caminho_arquivo}")
        print(f"Erro: O arquivo {arquivo_escolhido} não contém JSON válido.")
    except Exception as e:
        logger.error(f"Erro ao visualizar estatísticas: {e}", exc_info=True)
        print(f"Erro ao visualizar estatísticas: {e}")
    
    input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 