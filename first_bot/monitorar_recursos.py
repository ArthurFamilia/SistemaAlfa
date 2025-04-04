#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para monitorar recursos do sistema.

Este script monitora e exibe informações sobre os recursos do sistema,
como CPU, memória, disco e rede durante a execução do bot.
"""

import os
import sys
import logging
import time
from datetime import datetime

def monitorar_recursos():
    """
    Monitora os recursos do sistema e exibe em tempo real.
    """
    logger = logging.getLogger('menu_bot_ml')
    
    try:
        # Importar o módulo de monitoramento
        from monitoramento import MonitorRecursos
        
        logger.info("Iniciando monitoramento de recursos...")
        print("\n" + "="*60)
        print("   MONITORAMENTO DE RECURSOS DO SISTEMA")
        print("="*60)
        print("Pressione Ctrl+C para interromper o monitoramento.")
        print("="*60)
        
        # Criar diretório para relatórios
        os.makedirs('logs/sistema', exist_ok=True)
        
        # Timestamp para o arquivo de relatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"logs/sistema/monitor_{timestamp}.log"
        
        # Configurar intervalo de monitoramento
        try:
            intervalo = float(input("\nIntervalo de atualização em segundos [1.0]: ").strip() or "1.0")
            if intervalo < 0.1:
                intervalo = 0.1
                print("Intervalo mínimo é 0.1 segundos. Usando 0.1.")
        except ValueError:
            intervalo = 1.0
            print("Valor inválido. Usando intervalo padrão de 1 segundo.")
        
        # Duração do monitoramento
        try:
            duracao = int(input("Duração do monitoramento em minutos [0 para ilimitado]: ").strip() or "0")
        except ValueError:
            duracao = 0
            print("Valor inválido. Usando duração ilimitada.")
        
        # Iniciar monitor
        monitor = MonitorRecursos(
            intervalo_segundos=intervalo,
            arquivo_log=nome_arquivo,
            exibir_console=True
        )
        
        # Iniciar monitoramento
        monitor.iniciar()
        
        # Timestamp de início
        inicio = datetime.now()
        print(f"\nMonitoramento iniciado em: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Intervalo de atualização: {intervalo} segundos")
        if duracao > 0:
            print(f"Duração programada: {duracao} minutos")
            print(f"O monitoramento será encerrado automaticamente às: {(inicio + datetime.timedelta(minutes=duracao)).strftime('%H:%M:%S')}")
        else:
            print("Duração: ilimitada (até interrupção manual)")
        
        print("\nColetando dados...")
        
        # Loop de monitoramento
        try:
            if duracao > 0:
                # Monitoramento com tempo limitado
                tempo_limite = duracao * 60  # Convertendo minutos para segundos
                tempo_decorrido = 0
                
                while tempo_decorrido < tempo_limite:
                    time.sleep(1)  # Verificar a cada segundo
                    tempo_decorrido += 1
                    
                    # Exibir tempo restante a cada 10 segundos
                    if tempo_decorrido % 10 == 0:
                        tempo_restante = tempo_limite - tempo_decorrido
                        minutos_restantes = tempo_restante // 60
                        segundos_restantes = tempo_restante % 60
                        print(f"Tempo restante: {minutos_restantes:02d}:{segundos_restantes:02d}")
                
                print("\nTempo limite atingido. Encerrando monitoramento...")
                
            else:
                # Monitoramento sem tempo limite (até Ctrl+C)
                contador = 0
                while True:
                    time.sleep(1)
                    contador += 1
                    
                    # Exibir tempo decorrido a cada 60 segundos
                    if contador % 60 == 0:
                        minutos_decorridos = contador // 60
                        print(f"Monitoramento em andamento há {minutos_decorridos} minutos...")
        
        except KeyboardInterrupt:
            print("\nMonitoramento interrompido pelo usuário.")
        
        finally:
            # Parar monitoramento
            monitor.parar()
            
            # Gerar relatório final
            relatorio = monitor.exportar_relatorio()
            
            # Exibir resumo
            fim = datetime.now()
            duracao_total = fim - inicio
            horas, resto = divmod(duracao_total.total_seconds(), 3600)
            minutos, segundos = divmod(resto, 60)
            
            print("\n" + "="*60)
            print("   RESUMO DO MONITORAMENTO")
            print("="*60)
            print(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Fim: {fim.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duração: {int(horas)}h {int(minutos)}m {int(segundos)}s")
            print(f"Intervalo de coleta: {intervalo} segundos")
            print(f"Arquivo de log: {nome_arquivo}")
            print(f"Relatório gerado: {relatorio}")
            print("="*60)
            
            # Perguntar se deseja visualizar estatísticas
            visualizar = input("\nDeseja visualizar estatísticas do monitoramento? (s/N): ").lower() == 's'
            
            if visualizar:
                # Obter estatísticas resumidas
                estatisticas = monitor.obter_estatisticas()
                
                if estatisticas:
                    print("\n" + "="*60)
                    print("   ESTATÍSTICAS DE RECURSOS")
                    print("="*60)
                    
                    # CPU
                    print("\nUSO DE CPU:")
                    print(f"  Média: {estatisticas['cpu']['media']:.2f}%")
                    print(f"  Máximo: {estatisticas['cpu']['maximo']:.2f}%")
                    print(f"  Mínimo: {estatisticas['cpu']['minimo']:.2f}%")
                    
                    # Memória
                    print("\nUSO DE MEMÓRIA:")
                    print(f"  Média: {estatisticas['memoria']['media']:.2f}%")
                    print(f"  Máximo: {estatisticas['memoria']['maximo']:.2f}%")
                    print(f"  Mínimo: {estatisticas['memoria']['minimo']:.2f}%")
                    print(f"  Média (MB): {estatisticas['memoria']['media_mb']:.2f} MB")
                    
                    # Disco
                    print("\nUSO DE DISCO:")
                    print(f"  Uso: {estatisticas['disco']['uso']:.2f}%")
                    print(f"  Total: {estatisticas['disco']['total_gb']:.2f} GB")
                    print(f"  Disponível: {estatisticas['disco']['disponivel_gb']:.2f} GB")
                    
                    # Rede (se disponível)
                    if 'rede' in estatisticas:
                        print("\nRede:")
                        print(f"  Bytes enviados: {estatisticas['rede']['bytes_enviados']}")
                        print(f"  Bytes recebidos: {estatisticas['rede']['bytes_recebidos']}")
                    
                    print("="*60)
                else:
                    print("Nenhuma estatística disponível para exibição.")
            
            # Perguntar se deseja gerar gráficos
            gerar_graficos = input("\nDeseja gerar gráficos dos recursos? (s/N): ").lower() == 's'
            
            if gerar_graficos:
                try:
                    resultado = monitor.gerar_graficos()
                    if resultado:
                        print(f"Gráficos gerados com sucesso: {resultado}")
                    else:
                        print("Não foi possível gerar os gráficos.")
                except Exception as e:
                    print(f"Erro ao gerar gráficos: {e}")
    
    except ImportError:
        logger.error("Módulo MonitorRecursos não encontrado.")
        print("\nErro: Módulo MonitorRecursos não encontrado.")
        print("Verifique se o arquivo monitoramento.py está disponível.")
    except Exception as e:
        logger.error(f"Erro ao monitorar recursos: {e}", exc_info=True)
        print(f"\nErro ao monitorar recursos: {e}")
    
    input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 