#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Menu principal para o Bot de Trading com ML.

Este script fornece uma interface para acessar as principais
funcionalidades do bot de trading com ML.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

def configurar_logger():
    """
    Configura o logger para o script do menu.
    """
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger('menu_bot_ml')
    logger.setLevel(logging.INFO)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('logs/menu_bot_ml.log')
    file_handler.setLevel(logging.INFO)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato para os logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def exibir_menu():
    """
    Exibe o menu de opções para o usuário.
    
    Returns:
        int: Opção escolhida pelo usuário
    """
    print("\n" + "="*60)
    print("   BOT DE TRADING COM MACHINE LEARNING")
    print("="*60)
    print("[1] Iniciar bot em modo simulado (sem operações reais)")
    print("[2] Iniciar bot em modo real (executa operações reais)")
    print("[3] Executar backtest")
    print("[4] Treinar modelo de classificação de regime de mercado")
    print("[5] Treinar modelo de filtro de sinais")
    print("[6] Otimizar parâmetros de indicadores")
    print("[7] Ver estatísticas do último backtest")
    print("[8] Monitorar recursos do sistema")
    print("[0] Sair")
    print("="*60)
    
    try:
        opcao = int(input("Escolha uma opção: "))
        return opcao
    except ValueError:
        return -1

def verificar_configuracao():
    """
    Verifica a configuração no arquivo .env e carrega as variáveis de ambiente.
    
    Returns:
        dict: Configurações carregadas do arquivo .env
    """
    logger = logging.getLogger('menu_bot_ml')
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar existência de chaves obrigatórias
    chaves_obrigatorias = [
        'API_KEY', 
        'API_SECRET',
        'TRADING_PAIR',
        'POSITION_SIZE',
        'CANDLE_INTERVAL'
    ]
    
    config = {}
    missing_keys = []
    
    for chave in chaves_obrigatorias:
        valor = os.getenv(chave)
        if not valor:
            missing_keys.append(chave)
        config[chave] = valor
    
    if missing_keys:
        logger.error(f"Configurações obrigatórias não encontradas: {', '.join(missing_keys)}")
        logger.error("Por favor, edite o arquivo .env e adicione as configurações faltantes.")
        return None
    
    logger.info("Configuração verificada e carregada.")
    return config

def main():
    """
    Função principal que inicia o menu.
    """
    # Configurar logger
    logger = configurar_logger()
    logger.info("Iniciando menu do Bot de Trading com ML")
    
    # Verificar configuração
    config = verificar_configuracao()
    if not config:
        logger.error("Falha na verificação da configuração. O script será encerrado.")
        sys.exit(1)
    
    # Loop principal
    while True:
        opcao = exibir_menu()
        
        if opcao == 0:  # Sair
            logger.info("Encerrando menu do Bot de Trading com ML")
            break
        
        elif opcao == 1:  # Iniciar bot em modo simulado
            logger.info("Iniciando bot em modo simulado...")
            # Será implementado em arquivo separado
            print("Bot em modo simulado será iniciado...")
            from iniciar_bot_simulado import executar_bot_simulado
            executar_bot_simulado(config)
        
        elif opcao == 2:  # Iniciar bot em modo real
            logger.info("Iniciando bot em modo real...")
            # Será implementado em arquivo separado
            print("Bot em modo real será iniciado...")
            from iniciar_bot_real import executar_bot_real
            executar_bot_real(config)
        
        elif opcao == 3:  # Executar backtest
            logger.info("Executando backtest...")
            # Será implementado em arquivo separado
            print("Backtest será executado...")
            from executar_backtest import executar_backtest
            executar_backtest(config)
        
        elif opcao == 4:  # Treinar classificador de regime
            logger.info("Treinando classificador de regime...")
            # Será implementado em arquivo separado
            print("Classificador de regime será treinado...")
            from treinar_modelos import treinar_classificador_regime
            treinar_classificador_regime(config)
        
        elif opcao == 5:  # Treinar filtro de sinais
            logger.info("Treinando filtro de sinais...")
            # Será implementado em arquivo separado
            print("Filtro de sinais será treinado...")
            from treinar_modelos import treinar_filtro_sinais
            treinar_filtro_sinais(config)
        
        elif opcao == 6:  # Otimizar parâmetros
            logger.info("Otimizando parâmetros...")
            # Será implementado em arquivo separado
            print("Parâmetros serão otimizados...")
            from otimizar_parametros import otimizar_parametros
            otimizar_parametros(config)
        
        elif opcao == 7:  # Ver estatísticas
            logger.info("Visualizando estatísticas...")
            # Será implementado em arquivo separado
            print("Estatísticas serão exibidas...")
            from visualizar_estatisticas import ver_estatisticas
            ver_estatisticas()
        
        elif opcao == 8:  # Monitorar recursos
            logger.info("Monitorando recursos...")
            # Será implementado em arquivo separado
            print("Recursos serão monitorados...")
            from monitorar_recursos import monitorar_recursos
            monitorar_recursos()
        
        else:
            print("Opção inválida. Por favor, tente novamente.")
        
        # Pequena pausa antes de mostrar o menu novamente
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Erro não tratado: {e}", exc_info=True)
        print(f"Ocorreu um erro: {e}")
        
        # Tentar continuar ou perguntar se deve encerrar
        try:
            continuar = input("\nDeseja continuar mesmo assim? (s/N): ")
            if continuar.lower() != 's':
                print("Encerrando programa.")
                sys.exit(1)
            else:
                print("Tentando continuar a execução...\n")
                main()
        except:
            sys.exit(1) 