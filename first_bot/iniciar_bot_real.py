#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para iniciar o Bot de Trading em modo real.

Este script configura o ambiente e inicializa o bot em modo real,
executando operações reais com dinheiro real.
"""

import os
import sys
import logging
import time
from datetime import datetime
import hashlib

def executar_bot_real(config):
    """
    Executa o bot de trading em modo real.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('menu_bot_ml')
    
    logger.info("Iniciando bot em modo REAL...")
    print("\n" + "="*60)
    print("   BOT DE TRADING - MODO REAL")
    print("   ⚠️ OPERAÇÕES REAIS ⚠️")
    print("="*60)
    print(f"Par de trading: {config.get('TRADING_PAIR', 'BTCUSDT')}")
    print(f"Tamanho da posição: {config.get('POSITION_SIZE', '10.0')}")
    print(f"Intervalo: {config.get('CANDLE_INTERVAL', '1h')}")
    print("="*60)
    
    # Verificar API keys
    api_key = config.get('API_KEY', '')
    api_secret = config.get('API_SECRET', '')
    
    if api_key == 'sua_api_key_aqui' or api_secret == 'seu_api_secret_aqui':
        print("\n⚠️ ATENÇÃO! As chaves da API não foram configuradas corretamente.")
        print("Por favor, configure suas chaves da API no arquivo .env e tente novamente.")
        logger.error("Tentativa de iniciar bot em modo real sem chaves API configuradas.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Definir modo real
    os.environ['SIMULATION_MODE'] = 'FALSE'
    
    # Confirmar execução com o usuário
    print("\n⚠️ ATENÇÃO! Você está prestes a iniciar o bot em MODO REAL!")
    print("Isso significa que o bot executará operações reais com seu dinheiro.")
    print("O bot operará de acordo com as configurações definidas no arquivo .env.")
    
    # Primeira confirmação
    confirmacao1 = input("\nEntendo os riscos e desejo continuar a execução em MODO REAL? (s/N): ")
    if confirmacao1.lower() != 's':
        logger.info("Execução em modo real cancelada pelo usuário (primeira confirmação).")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Segunda confirmação com código de segurança
    codigo_seguranca = hashlib.md5(f"{api_key[:5]}{datetime.now().strftime('%Y%m%d')}".encode()).hexdigest()[:6]
    print("\nPor segurança adicional, por favor digite o código a seguir:")
    print(f"Código: {codigo_seguranca}")
    
    confirmacao2 = input("Digite o código de segurança exatamente como mostrado: ")
    if confirmacao2 != codigo_seguranca:
        logger.info("Execução em modo real cancelada pelo usuário (código de segurança inválido).")
        print("\nCódigo de segurança inválido. Execução cancelada.")
        input("\nPressione Enter para retornar ao menu principal...")
        return
    
    # Iniciar monitor de recursos
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
        
        # Confirmação final
        print("\n⚠️ CONFIRMAÇÃO FINAL ⚠️")
        print(f"Bot: {tipo_bot}")
        print(f"Par: {config.get('TRADING_PAIR', 'BTCUSDT')}")
        print(f"Valor de operação: {config.get('POSITION_SIZE', '10.0')} USDT")
        print(f"Modo: REAL - Executará operações reais!")
        
        confirmacao_final = input("\nEsta é a última confirmação. Iniciar bot AGORA? (s/N): ")
        if confirmacao_final.lower() != 's':
            logger.info("Execução em modo real cancelada pelo usuário (confirmação final).")
            if usando_monitor:
                monitor.parar()
            input("\nPressione Enter para retornar ao menu principal...")
            return
        
        # Iniciar bot
        print("\nIniciando bot em MODO REAL...\n")
        print("⚠️ EXECUTANDO OPERAÇÕES REAIS ⚠️")
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
        logger.error(f"Erro ao executar o bot em MODO REAL: {e}", exc_info=True)
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
        
        # Aviso importante ao final
        print("\n⚠️ ATENÇÃO! O bot foi encerrado.")
        print("Verifique suas posições na Binance para garantir que tudo esteja correto.")
        
        input("\nPressione Enter para retornar ao menu principal...")

if __name__ == "__main__":
    print("Este script deve ser executado a partir do menu principal.")
    print("Execute: python menu_bot_ml.py") 