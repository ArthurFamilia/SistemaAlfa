#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para iniciar o Bot de Trading em modo simulado.

Este script configura o ambiente e inicializa o bot em modo simulado,
sem executar operações reais.
"""

import os
import sys
import logging
import time
from datetime import datetime

def executar_bot_simulado(config):
    """
    Executa o bot de trading em modo simulado.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Iniciando bot em modo SIMULADO...")
    print("\n" + "="*60)
    print("   BOT DE TRADING - MODO SIMULADO")
    print("="*60)
    print(f"Par de trading: {config.get('TRADING_PAIR', 'BTCUSDT')}")
    print(f"Tamanho da posição: {config.get('POSITION_SIZE', '10.0')}")
    print(f"Intervalo: {config.get('CANDLE_INTERVAL', '1h')}")
    print("="*60)
    
    # Definir modo de simulação
    os.environ['SIMULATION_MODE'] = 'TRUE'
    
    # Iniciar monitor de recursos (opcional)
    try:
        from monitoramento import MonitorRecursos
        monitor = MonitorRecursos(intervalo_segundos=30)
        monitor.iniciar()
        usando_monitor = True
    except ImportError:
        logger.warning("Módulo MonitorRecursos não encontrado.")
        usando_monitor = False
    
    # Importar e iniciar bot
    try:
        # Tenta importar o bot ML primeiro
        try:
            from src.bot_ml import TradingBotML
            bot = TradingBotML()
            tipo_bot = "ML"
        except ImportError:
            # Se não encontrar, tenta o bot padrão
            from src.bot import TradingBot
            bot = TradingBot()
            tipo_bot = "Padrão"
        
        logger.info(f"Bot inicializado com sucesso. Tipo: {tipo_bot}")
        print(f"Bot inicializado com sucesso. Tipo: {tipo_bot}")
        
        # Solicitar confirmação para iniciar
        confirmacao = input("\nO bot está pronto para ser iniciado em MODO SIMULADO.\n"
                           "Deseja iniciar o bot agora? (s/N): ")
        
        if confirmacao.lower() != 's':
            logger.info("Inicialização cancelada pelo usuário.")
            if usando_monitor:
                monitor.parar()
            return
        
        # Iniciar bot
        print("\nIniciando bot em MODO SIMULADO...\n")
        print("Pressione Ctrl+C para interromper a execução.")
        
        # Timestamp de início
        inicio = datetime.now()
        print(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Executar
        bot.run()
        
    except KeyboardInterrupt:
        print("\nBot interrompido pelo usuário.")
        logger.info("Bot interrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro ao executar o bot: {e}")
        logger.error(f"Erro ao executar o bot: {e}", exc_info=True)
    finally:
        # Parar monitor se estiver em uso
        if usando_monitor:
            monitor.parar()
            relatorio = monitor.exportar_relatorio()
            logger.info(f"Relatório de recursos exportado para: {relatorio}")
            print(f"Relatório de recursos exportado para: {relatorio}")
        
        # Exibir tempo de execução
        fim = datetime.now()
        duracao = fim - inicio
        horas, resto = divmod(duracao.total_seconds(), 3600)
        minutos, segundos = divmod(resto, 60)
        
        print(f"\nTempo de execução: {int(horas)}h {int(minutos)}m {int(segundos)}s")
        print(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Fim:    {fim.strftime('%Y-%m-%d %H:%M:%S')}")
        
        input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 