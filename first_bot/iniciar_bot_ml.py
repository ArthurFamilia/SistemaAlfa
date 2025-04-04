#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para iniciar o Bot de Trading com ML.

Este script fornece uma interface centralizada para todas as funcionalidades
do bot de trading, incluindo execução, configuração, análise e monitoramento.
"""

import os
import sys
import logging
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Adicionar diretório raiz ao path para importações relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do projeto
try:
    from check_dependencies import verificar_dependencias, verificar_dependencias_ml
    from monitoramento import MonitorRecursos
    from src.bot_ml import TradingBotML
    # Substituído os módulos inexistentes pelos corretos
    # from src.backtest import Backtest, MineradorDeEstrategias
    from src.ml.classificador_regimes import ClassificadorRegimeMercado
    from src.ml.filtro_sinais import FiltroSinaisXGBoost
    from src.ml.otimizacao_bayesiana import OtimizadorBayesiano, criar_espaco_busca_adx
    from src.ml.strategy_miner_ml import MineradorEstrategiasML
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Verifique se todos os módulos estão instalados e se a estrutura do projeto está correta.")
    sys.exit(1)

# Configurar logger
def configurar_logger():
    """
    Configura o logger para o script de inicialização.
    """
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger('iniciar_bot_ml')
    logger.setLevel(logging.INFO)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('logs/iniciar_bot_ml.log')
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

# Verificar ambiente
def verificar_ambiente():
    """
    Verifica se o ambiente está configurado corretamente.
    
    Checa a existência de diretórios e arquivos necessários.
    """
    logger = logging.getLogger('iniciar_bot_ml')
    
    # Verificar diretórios necessários
    diretorios = [
        'logs',
        'modelos',
        'modelos/regimes',
        'modelos/filtro_sinais',
        'modelos/otimizador',
        'resultados',
        'resultados/backtests',
        'resultados/otimizacao'
    ]
    
    for diretorio in diretorios:
        if not os.path.exists(diretorio):
            logger.info(f"Criando diretório: {diretorio}")
            os.makedirs(diretorio, exist_ok=True)
    
    # Verificar arquivo .env
    if not os.path.exists('.env'):
        logger.warning("Arquivo .env não encontrado. Criando um arquivo de exemplo.")
        with open('.env', 'w') as f:
            f.write("""# Configurações do Bot de Trading com ML
# Preencha com suas configurações

# API Binance
API_KEY=sua_api_key_aqui
API_SECRET=seu_api_secret_aqui

# Configurações de negociação
TRADING_PAIR=BTCUSDT
POSITION_SIZE=10.0
CANDLE_INTERVAL=1h
HISTORICO_DIAS=30

# Configurações dos indicadores
ADX_PERIOD=14
ADX_THRESHOLD=25
DI_THRESHOLD=20

# Configurações de machine learning
MODELO_CLASSIFICADOR=modelos/regimes/classificador_regimes.joblib
MODELO_FILTRO=modelos/filtro_sinais/filtro_sinais.joblib
PARAMS_OTIMIZADOS=modelos/otimizador/params_otimizados.json

# Configurações de rede
MEDIR_REDE=True
SIMULAR_REDE=False
LATENCIA_BASE=50

# Configurações de logging
LOG_LEVEL=INFO
""")
    
    # Verificar módulos instalados
    verificar_dependencias()
    verificar_dependencias_ml()
    
    logger.info("Verificação do ambiente concluída.")

# Verificar configuração
def verificar_configuracao():
    """
    Verifica a configuração no arquivo .env e carrega as variáveis de ambiente.
    
    Returns:
        dict: Configurações carregadas do arquivo .env
    """
    logger = logging.getLogger('iniciar_bot_ml')
    
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
    
    # Verificar chaves da API
    if config['API_KEY'] == 'sua_api_key_aqui' or config['API_SECRET'] == 'seu_api_secret_aqui':
        logger.warning("As chaves da API não foram configuradas. O bot funcionará apenas em modo de teste.")
    
    # Verificar caminhos dos modelos
    modelo_classificador = os.getenv('MODELO_CLASSIFICADOR', 'modelos/regimes/classificador_regimes.joblib')
    modelo_filtro = os.getenv('MODELO_FILTRO', 'modelos/filtro_sinais/filtro_sinais.joblib')
    params_otimizados = os.getenv('PARAMS_OTIMIZADOS', 'modelos/otimizador/params_otimizados.json')
    
    config['MODELO_CLASSIFICADOR'] = modelo_classificador
    config['MODELO_FILTRO'] = modelo_filtro
    config['PARAMS_OTIMIZADOS'] = params_otimizados
    
    # Verificar se os modelos existem
    modelo_classificador_existe = os.path.exists(modelo_classificador)
    modelo_filtro_existe = os.path.exists(modelo_filtro)
    params_otimizados_existe = os.path.exists(params_otimizados)
    
    if not (modelo_classificador_existe and modelo_filtro_existe and params_otimizados_existe):
        logger.warning("Alguns modelos de ML não foram encontrados:")
        if not modelo_classificador_existe:
            logger.warning(f"  - Classificador de regime: {modelo_classificador}")
        if not modelo_filtro_existe:
            logger.warning(f"  - Filtro de sinais: {modelo_filtro}")
        if not params_otimizados_existe:
            logger.warning(f"  - Parâmetros otimizados: {params_otimizados}")
        logger.warning("Você precisa treinar os modelos antes de executar o bot em modo completo.")
    
    logger.info("Configuração verificada e carregada.")
    return config

# Limpar tela do terminal
def limpar_tela():
    """
    Limpa a tela do terminal para melhor visualização dos menus.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

# Exibir cabeçalho do menu
def exibir_cabecalho(titulo=None):
    """
    Exibe um cabeçalho formatado para o menu.
    
    Args:
        titulo (str, optional): Título a ser exibido no cabeçalho.
    """
    limpar_tela()
    print("\n" + "="*60)
    if titulo:
        print(f"   {titulo}")
    else:
        print("   BOT DE TRADING COM MACHINE LEARNING")
    print("="*60)

# Menu principal
def menu_principal(config):
    """
    Exibe o menu principal com todas as categorias disponíveis.
    
    Args:
        config (dict): Configurações do bot
    """
    exibir_cabecalho()
    
    print("[1] Operações do Bot")
    print("[2] Backtest e Análise")
    print("[3] Configurações")
    print("[4] Machine Learning")
    print("[5] Monitoramento")
    print("[6] Utilitários")
    print("[0] Sair")
    print("="*60)
    
    try:
        opcao = int(input("Escolha uma categoria: "))
        
        if opcao == 0:  # Sair
            return False
        elif opcao == 1:  # Operações do Bot
            submenu_operacoes(config)
        elif opcao == 2:  # Backtest e Análise
            submenu_backtest(config)
        elif opcao == 3:  # Configurações
            submenu_configuracoes(config)
        elif opcao == 4:  # Machine Learning
            submenu_ml(config)
        elif opcao == 5:  # Monitoramento
            submenu_monitoramento(config)
        elif opcao == 6:  # Utilitários
            submenu_utilitarios(config)
        else:
            print("Opção inválida!")
            time.sleep(1)
            
        return True
        
    except ValueError:
        print("Por favor, digite um número válido.")
        time.sleep(1)
        return True

# Submenu de Operações do Bot
def submenu_operacoes(config):
    """
    Exibe o submenu de operações do bot.
    
    Args:
        config (dict): Configurações do bot
    """
    while True:
        exibir_cabecalho("OPERAÇÕES DO BOT")
        
        print("[1] Iniciar bot em modo simulado")
        print("[2] Iniciar bot em modo real")
        print("[3] Ver status do bot")
        print("[4] Ver posições atuais")
        print("[5] Parar bot em execução")
        print("[0] Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = int(input("Escolha uma opção: "))
            
            if opcao == 0:  # Voltar
                break
            elif opcao == 1:  # Iniciar bot simulado
                executar_bot_simulado(config)
            elif opcao == 2:  # Iniciar bot real
                executar_bot_real(config)
            elif opcao == 3:  # Ver status
                verificar_status_bot()
            elif opcao == 4:  # Ver posições
                verificar_posicoes()
            elif opcao == 5:  # Parar bot
                parar_bot()
            else:
                print("Opção inválida!")
                time.sleep(1)
                
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

# Submenu de Backtest e Análise
def submenu_backtest(config):
    """
    Exibe o submenu de backtest e análise.
    
    Args:
        config (dict): Configurações do bot
    """
    while True:
        exibir_cabecalho("BACKTEST E ANÁLISE")
        
        print("[1] Executar backtest")
        print("[2] Ver resultados de backtests")
        print("[3] Comparar estratégias")
        print("[4] Visualizar gráficos de performance")
        print("[5] Executar minerador de estratégias")
        print("[0] Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = int(input("Escolha uma opção: "))
            
            if opcao == 0:  # Voltar
                break
            elif opcao == 1:  # Executar backtest
                executar_backtest(config)
            elif opcao == 2:  # Ver resultados
                ver_estatisticas()
            elif opcao == 3:  # Comparar estratégias
                comparar_estrategias(config)
            elif opcao == 4:  # Visualizar gráficos
                visualizar_graficos_performance()
            elif opcao == 5:  # Minerador de estratégias
                executar_minerador(config)
            else:
                print("Opção inválida!")
                time.sleep(1)
                
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

# Submenu de Configurações
def submenu_configuracoes(config):
    """
    Exibe o submenu de configurações.
    
    Args:
        config (dict): Configurações do bot
    """
    while True:
        exibir_cabecalho("CONFIGURAÇÕES")
        
        print("[1] Editar configurações gerais (.env)")
        print("[2] Configuração avançada de backtest")
        print("[3] Configuração do minerador")
        print("[4] Configuração de indicadores")
        print("[5] Salvar configuração atual")
        print("[6] Carregar configuração salva")
        print("[0] Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = int(input("Escolha uma opção: "))
            
            if opcao == 0:  # Voltar
                break
            elif opcao == 1:  # Editar .env
                configurar_env()
            elif opcao == 2:  # Config backtest
                config_backtest()
            elif opcao == 3:  # Config minerador
                config_minerador()
            elif opcao == 4:  # Config indicadores
                config_indicadores()
            elif opcao == 5:  # Salvar config
                salvar_configuracao(config)
            elif opcao == 6:  # Carregar config
                config = carregar_configuracao() or config
            else:
                print("Opção inválida!")
                time.sleep(1)
                
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)
            
    return config

# Submenu de Machine Learning
def submenu_ml(config):
    """
    Exibe o submenu de machine learning.
    
    Args:
        config (dict): Configurações do bot
    """
    while True:
        exibir_cabecalho("MACHINE LEARNING")
        
        print("[1] Treinar classificador de regime de mercado")
        print("[2] Treinar filtro de sinais")
        print("[3] Otimizar parâmetros com ML")
        print("[4] Ver desempenho dos modelos")
        print("[5] Exportar modelos treinados")
        print("[6] Importar modelos")
        print("[0] Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = int(input("Escolha uma opção: "))
            
            if opcao == 0:  # Voltar
                break
            elif opcao == 1:  # Treinar classificador
                treinar_classificador_regime(config)
            elif opcao == 2:  # Treinar filtro
                treinar_filtro_sinais(config)
            elif opcao == 3:  # Otimizar parâmetros
                otimizar_parametros(config)
            elif opcao == 4:  # Ver desempenho
                ver_desempenho_modelos()
            elif opcao == 5:  # Exportar modelos
                exportar_modelos()
            elif opcao == 6:  # Importar modelos
                importar_modelos()
            else:
                print("Opção inválida!")
                time.sleep(1)
                
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

# Submenu de Monitoramento
def submenu_monitoramento(config):
    """
    Exibe o submenu de monitoramento.
    
    Args:
        config (dict): Configurações do bot
    """
    while True:
        exibir_cabecalho("MONITORAMENTO")
        
        print("[1] Monitorar recursos do sistema")
        print("[2] Ver logs em tempo real")
        print("[3] Ver estatísticas de rede")
        print("[4] Ver logs do bot")
        print("[5] Exportar relatórios")
        print("[0] Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = int(input("Escolha uma opção: "))
            
            if opcao == 0:  # Voltar
                break
            elif opcao == 1:  # Monitorar recursos
                monitorar_recursos()
            elif opcao == 2:  # Ver logs em tempo real
                ver_logs_tempo_real()
            elif opcao == 3:  # Estatísticas de rede
                ver_estatisticas_rede()
            elif opcao == 4:  # Ver logs do bot
                ver_logs_bot()
            elif opcao == 5:  # Exportar relatórios
                exportar_relatorios()
            else:
                print("Opção inválida!")
                time.sleep(1)
                
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

# Submenu de Utilitários
def submenu_utilitarios(config):
    """
    Exibe o submenu de utilitários.
    
    Args:
        config (dict): Configurações do bot
    """
    while True:
        exibir_cabecalho("UTILITÁRIOS")
        
        print("[1] Verificar dependências")
        print("[2] Exportar configurações")
        print("[3] Importar dados históricos")
        print("[4] Fazer backup dos dados")
        print("[5] Restaurar dados de backup")
        print("[6] Ver manual de uso")
        print("[0] Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = int(input("Escolha uma opção: "))
            
            if opcao == 0:  # Voltar
                break
            elif opcao == 1:  # Verificar dependências
                verificar_dependencias_menu()
            elif opcao == 2:  # Exportar configurações
                exportar_configuracoes(config)
            elif opcao == 3:  # Importar dados históricos
                importar_dados_historicos()
            elif opcao == 4:  # Fazer backup
                fazer_backup()
            elif opcao == 5:  # Restaurar backup
                restaurar_backup()
            elif opcao == 6:  # Ver manual
                ver_manual()
            else:
                print("Opção inválida!")
                time.sleep(1)
                
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

# Placeholder para funções que serão implementadas separadamente
def executar_bot_simulado(config):
    """
    Executa o bot de trading em modo simulado.
    Não faz transações reais, apenas simula as operações.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('iniciar_bot_ml')
    exibir_cabecalho("INICIAR BOT EM MODO SIMULADO")
    
    print("AVISO: O bot será executado em modo simulado (sem transações reais).")
    print("Pressione Ctrl+C a qualquer momento para interromper a execução.")
    print("\nConfiguração atual:")
    print(f"Par de trading: {config.get('TRADING_PAIR', 'BTCUSDT')}")
    print(f"Intervalo de tempo: {config.get('CANDLE_INTERVAL', '1h')}")
    print(f"Tamanho da posição: {config.get('POSITION_SIZE', '10.0')}")
    print("="*60)
    
    # Confirmar início
    confirmar = input("\nIniciar o bot em modo simulado? (s/N): ")
    if confirmar.lower() != 's':
        print("Operação cancelada.")
        input("\nPressione Enter para continuar...")
        return
    
    # Criar instância do bot
    try:
        bot = TradingBotML(
            api_key=config.get('API_KEY'),
            api_secret=config.get('API_SECRET'),
            par=config.get('TRADING_PAIR', 'BTCUSDT'),
            position_size=float(config.get('POSITION_SIZE', 10.0)),
            candle_interval=config.get('CANDLE_INTERVAL', '1h'),
            dias_historico=int(config.get('HISTORICO_DIAS', 30)),
            modo_simulado=True
        )
        
        # Carregar modelos
        if os.path.exists(config.get('MODELO_CLASSIFICADOR', '')):
            bot.carregar_classificador_regimes(config.get('MODELO_CLASSIFICADOR'))
            print("\nClassificador de regimes de mercado carregado.")
        else:
            logger.warning("Modelo classificador não encontrado. Bot funcionará sem classificação de regimes.")
            print("\nAVISO: Modelo classificador não encontrado. Bot funcionará sem classificação de regimes.")
        
        if os.path.exists(config.get('MODELO_FILTRO', '')):
            bot.carregar_filtro_sinais(config.get('MODELO_FILTRO'))
            print("Filtro de sinais carregado.")
        else:
            logger.warning("Modelo de filtro de sinais não encontrado. Bot funcionará sem filtro de sinais.")
            print("AVISO: Modelo de filtro de sinais não encontrado. Bot funcionará sem filtro de sinais.")
        
        # Carregar parâmetros otimizados
        if os.path.exists(config.get('PARAMS_OTIMIZADOS', '')):
            try:
                with open(config.get('PARAMS_OTIMIZADOS'), 'r') as f:
                    params = json.load(f)
                if 'parametros' in params:
                    bot.configurar_parametros(params['parametros'])
                    print("Parâmetros otimizados carregados.")
            except Exception as e:
                logger.error(f"Erro ao carregar parâmetros otimizados: {e}")
                print(f"Erro ao carregar parâmetros otimizados: {e}")
        
        print("\nBot configurado. Iniciando execução...")
        print("="*60)
        
        # Iniciar bot
        logger.info("Iniciando bot em modo simulado.")
        bot.iniciar(bloquear=False)
        
        print("\nBot iniciado em modo simulado!")
        print("Os logs estão sendo salvos em './logs/bot_trading.log'")
        print("Mantenha esta janela aberta para continuar a execução.")
        print("Pressione Ctrl+C a qualquer momento para interromper.")
        
        # Exibir opções de monitoramento
        print("\nOpções disponíveis:")
        print("[1] Exibir logs em tempo real")
        print("[2] Voltar ao menu (bot continuará em execução)")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            # Exibir logs em tempo real (implementação simplificada)
            print("\nExibindo logs em tempo real (pressione Ctrl+C para voltar):")
            print("="*60)
            try:
                # Versão simplificada - em produção, usar um thread ou 'tail -f'
                ultima_linha = 0
                while True:
                    with open('logs/bot_trading.log', 'r') as f:
                        linhas = f.readlines()
                    
                    if len(linhas) > ultima_linha:
                        for i in range(ultima_linha, len(linhas)):
                            print(linhas[i].strip())
                        ultima_linha = len(linhas)
                    
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print("\nMonitoramento interrompido. Bot continua em execução.")
        
        input("\nPressione Enter para voltar ao menu...")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários: {e}")
        print(f"\nErro ao importar módulos necessários: {e}")
        print("Verifique se todos os módulos estão instalados corretamente.")
        input("\nPressione Enter para continuar...")
    
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}", exc_info=True)
        print(f"\nErro ao iniciar o bot: {e}")
        input("\nPressione Enter para continuar...")

def executar_bot_real(config):
    print("\nFunção de executar bot real será implementada em breve.")
    input("\nPressione Enter para continuar...")

def verificar_status_bot():
    print("\nFunção de verificar status será implementada em breve.")
    input("\nPressione Enter para continuar...")

def verificar_posicoes():
    print("\nFunção de verificar posições será implementada em breve.")
    input("\nPressione Enter para continuar...")

def parar_bot():
    print("\nFunção de parar bot será implementada em breve.")
    input("\nPressione Enter para continuar...")

def executar_backtest(config):
    """
    Executa um backtest com as configurações fornecidas.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('iniciar_bot_ml')
    
    # Verificar se backtest.py existe
    if not os.path.exists('backtest.py'):
        print("\nErro: arquivo backtest.py não encontrado no diretório atual.")
        print("Por favor, verifique se o arquivo existe na raiz do projeto.")
        logger.error("Arquivo backtest.py não encontrado.")
        input("\nPressione Enter para continuar...")
        return
    
    exibir_cabecalho("EXECUTAR BACKTEST")
    
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
    
    try:
        # Importar o módulo de backtest
        from backtest import Backtest
        
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
            input("\nPressione Enter para continuar...")
            return
        
        # Salvar resultados
        caminho_resultado = f"resultados/backtests/{nome_resultado}.json"
        
        with open(caminho_resultado, 'w') as f:
            json.dump(resultado, f, indent=2)
        
        # Resumo dos resultados
        fim = datetime.now()
        duracao = fim - inicio
        
        exibir_cabecalho("RESULTADOS DO BACKTEST")
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
        
        print("\nBacktest concluído com sucesso!")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulo de backtest: {e}")
        print(f"\nErro ao importar módulo de backtest: {e}")
    except Exception as e:
        logger.error(f"Erro ao executar backtest: {e}", exc_info=True)
        print(f"\nErro ao executar backtest: {e}")
    
    input("\nPressione Enter para continuar...")

def ver_estatisticas():
    """
    Exibe os resultados dos backtests realizados anteriormente.
    """
    logger = logging.getLogger('iniciar_bot_ml')
    exibir_cabecalho("RESULTADOS DE BACKTESTS")
    
    # Verificar diretório de resultados
    diretorio_resultados = 'resultados/backtests'
    if not os.path.exists(diretorio_resultados):
        os.makedirs(diretorio_resultados, exist_ok=True)
        print("\nNenhum resultado de backtest encontrado.")
        input("\nPressione Enter para continuar...")
        return
    
    # Listar arquivos de resultados
    arquivos_resultados = [f for f in os.listdir(diretorio_resultados) if f.endswith('.json')]
    
    if not arquivos_resultados:
        print("\nNenhum resultado de backtest encontrado.")
        input("\nPressione Enter para continuar...")
        return
    
    # Exibir lista de backtests disponíveis
    print("\nBacktests disponíveis:")
    for i, arquivo in enumerate(arquivos_resultados, 1):
        # Extrair informações básicas do nome do arquivo
        try:
            # Formato esperado: backtest_PAR_TIMEFRAME_DATA_HORA.json
            partes = arquivo.replace('backtest_', '').replace('.json', '').split('_')
            par = partes[0]
            timeframe = partes[1]
            data = '_'.join(partes[2:])
            
            # Tentar formatar a data
            try:
                data_formatada = datetime.strptime(data, '%Y%m%d_%H%M%S').strftime('%d/%m/%Y %H:%M')
            except:
                data_formatada = data
            
            print(f"[{i}] {par} ({timeframe}) - {data_formatada}")
        except:
            print(f"[{i}] {arquivo}")
    
    print("[0] Voltar")
    print("="*60)
    
    # Solicitar escolha do usuário
    try:
        escolha = int(input("\nEscolha um backtest para visualizar detalhes: "))
        
        if escolha == 0:
            return
        
        if escolha < 1 or escolha > len(arquivos_resultados):
            print("Opção inválida!")
            input("\nPressione Enter para continuar...")
            return
        
        # Carregar resultados do backtest selecionado
        arquivo_selecionado = arquivos_resultados[escolha - 1]
        caminho_completo = os.path.join(diretorio_resultados, arquivo_selecionado)
        
        try:
            with open(caminho_completo, 'r') as f:
                resultados = json.load(f)
            
            exibir_cabecalho(f"DETALHES DO BACKTEST: {arquivo_selecionado}")
            
            # Exibir informações básicas
            print(f"Par: {resultados.get('par', 'N/A')}")
            print(f"Timeframe: {resultados.get('timeframe', 'N/A')}")
            print(f"Dias de histórico: {resultados.get('dias_historico', 'N/A')}")
            print(f"Position Size: {resultados.get('position_size', 'N/A')}")
            print("-"*60)
            
            # Exibir métricas principais
            print("MÉTRICAS PRINCIPAIS:")
            print(f"Total de operações: {resultados.get('total_operacoes', 0)}")
            print(f"Operações vencedoras: {resultados.get('operacoes_vencedoras', 0)}")
            print(f"Operações perdedoras: {resultados.get('operacoes_perdedoras', 0)}")
            print(f"Taxa de acerto: {resultados.get('taxa_acerto', 0):.2f}%")
            print(f"Lucro total: {resultados.get('lucro_total', 0):.2f}")
            print(f"Expectativa matemática: {resultados.get('expectativa_matematica', 0):.4f}")
            print(f"Fator de lucro: {resultados.get('fator_lucro', 0):.2f}")
            print(f"Maior drawdown: {resultados.get('max_drawdown', 0):.2f} ({resultados.get('drawdown_percentual', 0):.2f}%)")
            print("-"*60)
            
            # Exibir estatísticas de sequências
            print("ESTATÍSTICAS DE SEQUÊNCIAS:")
            print(f"Maior sequência de ganhos: {resultados.get('maior_sequencia_ganhos', 0)}")
            print(f"Maior sequência de perdas: {resultados.get('maior_sequencia_perdas', 0)}")
            print("-"*60)
            
            # Exibir estatísticas de rede, se disponíveis
            if 'estatisticas_rede' in resultados:
                print("ESTATÍSTICAS DE REDE:")
                for chave, valor in resultados['estatisticas_rede'].items():
                    print(f"{chave}: {valor}")
                print("-"*60)
            
            # Opções adicionais
            print("\nOPÇÕES ADICIONAIS:")
            print("[1] Ver detalhes das operações")
            print("[2] Exportar relatório detalhado")
            print("[3] Visualizar gráficos (se disponível)")
            print("[0] Voltar")
            
            opcao = int(input("\nEscolha uma opção: "))
            
            if opcao == 1:  # Ver detalhes das operações
                exibir_cabecalho(f"OPERAÇÕES DO BACKTEST: {arquivo_selecionado}")
                
                operacoes = resultados.get('operacoes', [])
                if not operacoes:
                    print("Nenhuma operação disponível para este backtest.")
                else:
                    for i, op in enumerate(operacoes, 1):
                        tipo = op.get('tipo', 'N/A')
                        resultado = float(op.get('resultado', 0))
                        resultado_str = f"+{resultado:.4f}" if resultado >= 0 else f"{resultado:.4f}"
                        data_entrada = op.get('data_entrada', 'N/A')
                        data_saida = op.get('data_saida', 'N/A')
                        
                        # Colorir resultado (simulação simples com caracteres)
                        if resultado >= 0:
                            resultado_formatado = f"✓ {resultado_str}"
                        else:
                            resultado_formatado = f"✗ {resultado_str}"
                        
                        print(f"[{i}] {tipo} | {resultado_formatado} | Entrada: {data_entrada} | Saída: {data_saida}")
                        
                        # Mostrar apenas 20 operações por vez
                        if i % 20 == 0 and i < len(operacoes):
                            continuar = input("\nPressione Enter para continuar ou 'q' para sair: ")
                            if continuar.lower() == 'q':
                                break
                
            elif opcao == 2:  # Exportar relatório
                # Criar nome para o relatório
                nome_relatorio = arquivo_selecionado.replace('.json', '_relatorio.txt')
                caminho_relatorio = os.path.join(diretorio_resultados, nome_relatorio)
                
                try:
                    with open(caminho_relatorio, 'w') as f:
                        f.write("="*60 + "\n")
                        f.write("   RELATÓRIO DETALHADO DO BACKTEST\n")
                        f.write("="*60 + "\n")
                        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        
                        # Informações básicas
                        f.write("INFORMAÇÕES BÁSICAS:\n")
                        f.write(f"Par: {resultados.get('par', 'N/A')}\n")
                        f.write(f"Timeframe: {resultados.get('timeframe', 'N/A')}\n")
                        f.write(f"Dias de histórico: {resultados.get('dias_historico', 'N/A')}\n")
                        f.write(f"Position Size: {resultados.get('position_size', 'N/A')}\n\n")
                        
                        # Métricas principais
                        f.write("MÉTRICAS PRINCIPAIS:\n")
                        f.write(f"Total de operações: {resultados.get('total_operacoes', 0)}\n")
                        f.write(f"Operações vencedoras: {resultados.get('operacoes_vencedoras', 0)}\n")
                        f.write(f"Operações perdedoras: {resultados.get('operacoes_perdedoras', 0)}\n")
                        f.write(f"Taxa de acerto: {resultados.get('taxa_acerto', 0):.2f}%\n")
                        f.write(f"Lucro total: {resultados.get('lucro_total', 0):.2f}\n")
                        f.write(f"Expectativa matemática: {resultados.get('expectativa_matematica', 0):.4f}\n")
                        f.write(f"Fator de lucro: {resultados.get('fator_lucro', 0):.2f}\n")
                        f.write(f"Maior drawdown: {resultados.get('max_drawdown', 0):.2f} ({resultados.get('drawdown_percentual', 0):.2f}%)\n\n")
                        
                        # Estatísticas de sequências
                        f.write("ESTATÍSTICAS DE SEQUÊNCIAS:\n")
                        f.write(f"Maior sequência de ganhos: {resultados.get('maior_sequencia_ganhos', 0)}\n")
                        f.write(f"Maior sequência de perdas: {resultados.get('maior_sequencia_perdas', 0)}\n\n")
                        
                        # Estatísticas de rede
                        if 'estatisticas_rede' in resultados:
                            f.write("ESTATÍSTICAS DE REDE:\n")
                            for chave, valor in resultados['estatisticas_rede'].items():
                                f.write(f"{chave}: {valor}\n")
                            f.write("\n")
                        
                        # Detalhes das operações
                        f.write("DETALHES DAS OPERAÇÕES:\n")
                        operacoes = resultados.get('operacoes', [])
                        if not operacoes:
                            f.write("Nenhuma operação disponível para este backtest.\n")
                        else:
                            for i, op in enumerate(operacoes, 1):
                                f.write(f"Operação #{i}:\n")
                                f.write(f"  Tipo: {op.get('tipo', 'N/A')}\n")
                                f.write(f"  Entrada: {op.get('preco_entrada', 0):.4f}\n")
                                f.write(f"  Saída: {op.get('preco_saida', 0):.4f}\n")
                                f.write(f"  Resultado: {op.get('resultado', 0):.4f}\n")
                                f.write(f"  Data entrada: {op.get('data_entrada', 'N/A')}\n")
                                f.write(f"  Data saída: {op.get('data_saida', 'N/A')}\n")
                                f.write("\n")
                    
                    print(f"\nRelatório detalhado salvo em: {caminho_relatorio}")
                
                except Exception as e:
                    logger.error(f"Erro ao exportar relatório: {e}")
                    print(f"\nErro ao exportar relatório: {e}")
            
            elif opcao == 3:  # Visualizar gráficos
                try:
                    # Tenta importar o módulo de gráficos
                    import backtest_plots
                    
                    # Obter nome base para os gráficos
                    nome_base = arquivo_selecionado.replace('.json', '')
                    
                    print("\nGerando gráficos...")
                    backtest_plots.gerar_graficos(resultados, nome_base)
                    print("Gráficos gerados com sucesso!")
                    
                except ImportError:
                    print("\nMódulo backtest_plots não encontrado. Gráficos não puderam ser gerados.")
                except Exception as e:
                    logger.error(f"Erro ao gerar gráficos: {e}")
                    print(f"\nErro ao gerar gráficos: {e}")
            
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar arquivo JSON: {caminho_completo}")
            print("\nErro ao ler o arquivo de resultados. O formato pode estar corrompido.")
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de resultados: {e}")
            print(f"\nErro ao processar o arquivo de resultados: {e}")
    
    except ValueError:
        print("\nPor favor, digite um número válido.")
    
    input("\nPressione Enter para continuar...")

def comparar_estrategias(config):
    print("\nFunção de comparar estratégias será implementada em breve.")
    input("\nPressione Enter para continuar...")

def visualizar_graficos_performance():
    print("\nFunção de visualizar gráficos será implementada em breve.")
    input("\nPressione Enter para continuar...")

def executar_minerador(config):
    """
    Executa o minerador de estratégias para encontrar os melhores parâmetros.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('iniciar_bot_ml')
    exibir_cabecalho("MINERADOR DE ESTRATÉGIAS")
    
    # Verificar se o módulo do minerador está disponível
    try:
        from src.ml.strategy_miner_ml import MineradorEstrategiasML
    except ImportError as e:
        logger.error(f"Erro ao importar o módulo do minerador: {e}")
        print(f"\nErro ao importar o módulo do minerador: {e}")
        print("Verifique se todos os módulos necessários estão instalados.")
        input("\nPressione Enter para continuar...")
        return
    
    # Obter configurações básicas
    par = config.get('TRADING_PAIR', 'BTCUSDT')
    timeframe = config.get('CANDLE_INTERVAL', '1h')
    dias = int(config.get('HISTORICO_DIAS', 30))
    
    # Exibir configurações atuais
    print(f"Par de trading: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    print("="*60)
    
    # Permitir personalizar os parâmetros
    personalizar = input("\nDeseja personalizar os parâmetros básicos? (s/N): ")
    
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
    
    # Configurar parâmetros do minerador
    print("\nCONFIGURAÇÃO DO MINERADOR")
    
    # Configurar modo
    print("\nSelecione o modo de operação:")
    print("[1] Busca em grade (grid search)")
    print("[2] Busca aleatória (random search)")
    print("[3] Busca inteligente com ML")
    
    try:
        modo = int(input("\nModo de busca [1]: ") or "1")
        if modo not in [1, 2, 3]:
            print("Modo inválido. Usando busca em grade.")
            modo = 1
    except ValueError:
        print("Valor inválido. Usando busca em grade.")
        modo = 1
    
    # Configurar número de combinações
    try:
        if modo == 1:  # Grid search
            max_combinacoes = int(input("\nNúmero máximo de combinações a testar [100]: ") or "100")
        elif modo == 2:  # Random search
            max_combinacoes = int(input("\nNúmero de tentativas aleatórias [50]: ") or "50")
        else:  # Busca com ML
            max_combinacoes = int(input("\nNúmero de iterações [30]: ") or "30")
    except ValueError:
        if modo == 1:
            max_combinacoes = 100
        elif modo == 2:
            max_combinacoes = 50
        else:
            max_combinacoes = 30
        print("Valor inválido. Usando valor padrão.")
    
    # Configurar ranges para parâmetros
    print("\nDefina os intervalos para cada parâmetro:")
    
    # ADX period
    try:
        adx_period_min = int(input("Período ADX mínimo [5]: ") or "5")
        adx_period_max = int(input("Período ADX máximo [30]: ") or "30")
        adx_period_step = int(input("Passo do período ADX [5]: ") or "5")
    except ValueError:
        adx_period_min = 5
        adx_period_max = 30
        adx_period_step = 5
        print("Valores inválidos. Usando valores padrão.")
    
    # ADX threshold
    try:
        adx_threshold_min = int(input("Limiar ADX mínimo [15]: ") or "15")
        adx_threshold_max = int(input("Limiar ADX máximo [40]: ") or "40")
        adx_threshold_step = int(input("Passo do limiar ADX [5]: ") or "5")
    except ValueError:
        adx_threshold_min = 15
        adx_threshold_max = 40
        adx_threshold_step = 5
        print("Valores inválidos. Usando valores padrão.")
    
    # DI threshold
    try:
        di_threshold_min = int(input("Limiar DI mínimo [10]: ") or "10")
        di_threshold_max = int(input("Limiar DI máximo [30]: ") or "30")
        di_threshold_step = int(input("Passo do limiar DI [5]: ") or "5")
    except ValueError:
        di_threshold_min = 10
        di_threshold_max = 30
        di_threshold_step = 5
        print("Valores inválidos. Usando valores padrão.")
    
    # Configurar critério de classificação
    print("\nSelecione o critério de classificação:")
    print("[1] Lucro total")
    print("[2] Expectativa matemática")
    print("[3] Fator de lucro")
    print("[4] Taxa de acerto ajustada pelo drawdown")
    
    try:
        criterio = int(input("\nCritério [1]: ") or "1")
        if criterio not in [1, 2, 3, 4]:
            print("Critério inválido. Usando lucro total.")
            criterio = 1
    except ValueError:
        print("Valor inválido. Usando lucro total.")
        criterio = 1
    
    # Mapear critério para nome
    criterio_map = {
        1: "lucro_total",
        2: "expectativa_matematica",
        3: "fator_lucro",
        4: "taxa_acerto_ajustada"
    }
    criterio_nome = criterio_map[criterio]
    
    # Confirmar início do minerador
    print("\nCONFIGURAÇÃO DO MINERADOR")
    print(f"Par: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    
    modo_texto = {
        1: "Busca em grade (grid search)",
        2: "Busca aleatória (random search)",
        3: "Busca inteligente com ML"
    }
    print(f"Modo de busca: {modo_texto[modo]}")
    print(f"Combinações/iterações: {max_combinacoes}")
    
    print("\nRanges de parâmetros:")
    print(f"Período ADX: {adx_period_min} a {adx_period_max}, passo {adx_period_step}")
    print(f"Limiar ADX: {adx_threshold_min} a {adx_threshold_max}, passo {adx_threshold_step}")
    print(f"Limiar DI: {di_threshold_min} a {di_threshold_max}, passo {di_threshold_step}")
    
    criterio_texto = {
        1: "Lucro total",
        2: "Expectativa matemática",
        3: "Fator de lucro",
        4: "Taxa de acerto ajustada pelo drawdown"
    }
    print(f"Critério de classificação: {criterio_texto[criterio]}")
    print("="*60)
    
    confirmar = input("\nIniciar minerador com os parâmetros acima? (s/N): ")
    if confirmar.lower() != 's':
        print("Operação cancelada.")
        input("\nPressione Enter para continuar...")
        return
    
    # Criar diretório para resultados
    os.makedirs('resultados/minerador', exist_ok=True)
    
    # Timestamp para identificação
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_resultado = f"minerador_{par}_{timeframe}_{timestamp}"
    caminho_resultado = f"resultados/minerador/{nome_resultado}.json"
    
    # Iniciar minerador
    print("\nIniciando minerador de estratégias...")
    print("Este processo pode demorar bastante tempo, dependendo do número de combinações.")
    print("Por favor, aguarde...")
    
    inicio = datetime.now()
    
    try:
        # Criar parâmetros de busca
        params_busca = {
            'adx_period': {
                'min': adx_period_min,
                'max': adx_period_max,
                'step': adx_period_step
            },
            'adx_threshold': {
                'min': adx_threshold_min,
                'max': adx_threshold_max,
                'step': adx_threshold_step
            },
            'di_threshold': {
                'min': di_threshold_min,
                'max': di_threshold_max,
                'step': di_threshold_step
            }
        }
        
        # Criar instância do minerador
        minerador = MineradorEstrategiasML(
            par=par,
            timeframe=timeframe,
            dias_historico=dias
        )
        
        # Executar mineração de acordo com o modo selecionado
        if modo == 1:  # Grid search
            resultados = minerador.busca_em_grade(
                params=params_busca,
                max_combinacoes=max_combinacoes,
                criterio=criterio_nome
            )
        elif modo == 2:  # Random search
            resultados = minerador.busca_aleatoria(
                params=params_busca,
                num_tentativas=max_combinacoes,
                criterio=criterio_nome
            )
        else:  # Busca com ML
            resultados = minerador.busca_ml(
                params=params_busca,
                num_iteracoes=max_combinacoes,
                criterio=criterio_nome
            )
        
        # Verificar resultados
        if not resultados or not resultados.get('estrategias'):
            logger.error("Minerador falhou ao retornar resultados.")
            print("\nErro: O minerador não retornou resultados válidos.")
            input("\nPressione Enter para continuar...")
            return
        
        # Calcular tempo de execução
        fim = datetime.now()
        duracao = fim - inicio
        
        # Exibir resultados
        exibir_cabecalho("RESULTADOS DO MINERADOR")
        print(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}")
        print(f"Total de estratégias testadas: {resultados.get('total_testadas', 0)}")
        print(f"Critério de classificação: {criterio_texto[criterio]}")
        print("-"*60)
        
        # Exibir melhores estratégias (top 10)
        estrategias = resultados.get('estrategias', [])
        print("\nMelhores estratégias encontradas:")
        for i, estrategia in enumerate(estrategias[:10], 1):
            print(f"\n#{i} - Pontuação: {estrategia.get('pontuacao', 0):.4f}")
            print(f"  Parâmetros:")
            for param, valor in estrategia.get('parametros', {}).items():
                print(f"    {param}: {valor}")
            print(f"  Métricas:")
            print(f"    Lucro total: {estrategia.get('metricas', {}).get('lucro_total', 0):.2f}")
            print(f"    Taxa de acerto: {estrategia.get('metricas', {}).get('taxa_acerto', 0):.2f}%")
            print(f"    Operações: {estrategia.get('metricas', {}).get('total_operacoes', 0)}")
            print(f"    Fator de lucro: {estrategia.get('metricas', {}).get('fator_lucro', 0):.2f}")
        
        print("-"*60)
        print(f"Tempo de execução: {duracao.total_seconds():.2f} segundos")
        
        # Salvar resultados
        with open(caminho_resultado, 'w') as f:
            json.dump(resultados, f, indent=2)
        
        print(f"Resultados salvos em: {caminho_resultado}")
        
        # Perguntar se deseja utilizar a melhor estratégia
        if estrategias:
            melhor_estrategia = estrategias[0]
            utilizar = input("\nDeseja utilizar a melhor estratégia encontrada? (s/N): ")
            
            if utilizar.lower() == 's':
                # Salvar a melhor estratégia como parâmetros otimizados
                params_path = config.get('PARAMS_OTIMIZADOS', 'modelos/otimizador/params_otimizados.json')
                os.makedirs(os.path.dirname(params_path), exist_ok=True)
                
                try:
                    dados_salvos = {
                        'parametros': melhor_estrategia.get('parametros', {}),
                        'metricas': melhor_estrategia.get('metricas', {}),
                        'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'origem': 'minerador_estrategias',
                        'par': par,
                        'timeframe': timeframe,
                        'dias_historico': dias
                    }
                    
                    with open(params_path, 'w') as f:
                        json.dump(dados_salvos, f, indent=2)
                    
                    print(f"Melhor estratégia salva como parâmetros otimizados em: {params_path}")
                    
                except Exception as e:
                    logger.error(f"Erro ao salvar melhor estratégia: {e}")
                    print(f"Erro ao salvar melhor estratégia: {e}")
        
        print("\nMineração de estratégias concluída com sucesso!")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários: {e}")
        print(f"\nErro ao importar módulos necessários: {e}")
        print("Verifique se todos os módulos estão instalados corretamente.")
    
    except Exception as e:
        logger.error(f"Erro durante a mineração: {e}", exc_info=True)
        print(f"\nErro durante a mineração: {e}")
    
    input("\nPressione Enter para continuar...")

def configurar_env():
    """
    Permite editar o arquivo .env com as configurações do bot.
    """
    exibir_cabecalho("CONFIGURAÇÕES GERAIS (.env)")
    
    if not os.path.exists('.env'):
        print("Arquivo .env não encontrado. Criando um novo...")
        verificar_ambiente()  # Cria o arquivo .env padrão
    
    # Carregar configurações atuais
    config_atual = {}
    categorias = {}
    categoria_atual = "Geral"
    
    try:
        with open('.env', 'r') as f:
            linhas = f.readlines()
            
            for linha in linhas:
                linha = linha.strip()
                
                # Pular linhas vazias e comentários sem categoria
                if not linha or (linha.startswith('#') and '=' not in linha and ':' not in linha):
                    continue
                
                # Verificar se é um cabeçalho de categoria
                if linha.startswith('#') and (':' in linha or '=' in linha):
                    possivel_categoria = linha.lstrip('#').strip()
                    if ':' in possivel_categoria:
                        categoria_atual = possivel_categoria.split(':')[0].strip()
                    elif '=' in possivel_categoria:
                        categoria_atual = possivel_categoria.split('=')[0].strip()
                    categorias[categoria_atual] = []
                    continue
                
                # Verificar se é uma configuração
                if '=' in linha and not linha.startswith('#'):
                    chave, valor = linha.split('=', 1)
                    chave = chave.strip()
                    valor = valor.strip()
                    config_atual[chave] = valor
                    
                    if categoria_atual in categorias:
                        categorias[categoria_atual].append(chave)
                    else:
                        categorias[categoria_atual] = [chave]
        
        # Se não há categorias definidas, colocar tudo em Geral
        if not categorias:
            categorias["Geral"] = list(config_atual.keys())
        
    except Exception as e:
        print(f"Erro ao ler o arquivo .env: {e}")
        print("Criando configurações padrão...")
        verificar_ambiente()  # Cria o arquivo .env padrão
        input("\nPressione Enter para continuar...")
        return
    
    # Exibir e editar configurações por categoria
    while True:
        exibir_cabecalho("CONFIGURAÇÕES GERAIS (.env)")
        
        print("Categorias disponíveis:")
        for i, cat in enumerate(categorias.keys(), 1):
            num_configs = len(categorias[cat])
            print(f"[{i}] {cat} ({num_configs} configurações)")
        
        print("\n[0] Salvar e voltar")
        print("[S] Salvar configurações")
        print("[C] Criar nova configuração")
        print("="*60)
        
        escolha = input("Escolha uma categoria ou opção: ").strip()
        
        if escolha == '0':
            # Salvar antes de sair
            salvar_configuracoes_env(config_atual, categorias)
            break
        elif escolha.lower() == 's':
            # Apenas salvar
            salvar_configuracoes_env(config_atual, categorias)
            print("Configurações salvas com sucesso!")
            time.sleep(1)
            continue
        elif escolha.lower() == 'c':
            # Criar nova configuração
            nova_chave = input("Nome da nova configuração: ").strip()
            if nova_chave:
                if nova_chave in config_atual:
                    print(f"Configuração '{nova_chave}' já existe!")
                else:
                    valor = input(f"Valor para '{nova_chave}': ").strip()
                    config_atual[nova_chave] = valor
                    
                    # Escolher categoria
                    print("\nEscolha a categoria:")
                    for i, cat in enumerate(categorias.keys(), 1):
                        print(f"[{i}] {cat}")
                    print(f"[{len(categorias) + 1}] Nova categoria")
                    
                    try:
                        cat_escolha = int(input("Categoria: "))
                        if 1 <= cat_escolha <= len(categorias):
                            cat_nome = list(categorias.keys())[cat_escolha - 1]
                            categorias[cat_nome].append(nova_chave)
                        elif cat_escolha == len(categorias) + 1:
                            nova_cat = input("Nome da nova categoria: ").strip()
                            if nova_cat:
                                categorias[nova_cat] = [nova_chave]
                            else:
                                categorias["Geral"].append(nova_chave)
                        else:
                            categorias["Geral"].append(nova_chave)
                    except:
                        categorias["Geral"].append(nova_chave)
                    
                    print(f"Configuração '{nova_chave}' adicionada!")
            time.sleep(1)
            continue
        
        try:
            escolha = int(escolha)
            if 1 <= escolha <= len(categorias):
                editar_categoria(list(categorias.keys())[escolha - 1], categorias, config_atual)
            else:
                print("Opção inválida!")
                time.sleep(1)
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

def editar_categoria(categoria, categorias, config_atual):
    """
    Permite editar as configurações de uma categoria específica.
    
    Args:
        categoria (str): Nome da categoria
        categorias (dict): Dicionário com categorias e suas configurações
        config_atual (dict): Configurações atuais
    """
    while True:
        exibir_cabecalho(f"CONFIGURAÇÕES - {categoria}")
        
        configs = categorias[categoria]
        for i, chave in enumerate(configs, 1):
            valor = config_atual.get(chave, "")
            # Se for uma senha ou API_SECRET, ocultar o valor
            if 'password' in chave.lower() or 'secret' in chave.lower():
                if valor:
                    display_valor = "*" * len(valor)
                else:
                    display_valor = ""
            else:
                display_valor = valor
            print(f"[{i}] {chave} = {display_valor}")
        
        print("\n[0] Voltar")
        print("[R] Remover configuração")
        print("="*60)
        
        escolha = input("Escolha uma configuração para editar ou uma opção: ").strip()
        
        if escolha == '0':
            break
        elif escolha.lower() == 'r':
            # Remover configuração
            try:
                num_remover = int(input("Número da configuração para remover: "))
                if 1 <= num_remover <= len(configs):
                    chave_remover = configs[num_remover - 1]
                    confirmar = input(f"Confirma remover '{chave_remover}'? (s/N): ").lower()
                    if confirmar == 's':
                        configs.remove(chave_remover)
                        if chave_remover in config_atual:
                            del config_atual[chave_remover]
                        print(f"Configuração '{chave_remover}' removida!")
                else:
                    print("Número inválido!")
            except ValueError:
                print("Por favor, digite um número válido.")
            time.sleep(1)
            continue
        
        try:
            escolha = int(escolha)
            if 1 <= escolha <= len(configs):
                chave = configs[escolha - 1]
                valor_atual = config_atual.get(chave, "")
                
                # Se for uma senha, perguntar se quer alterar antes de mostrar
                if 'password' in chave.lower() or 'secret' in chave.lower():
                    if valor_atual:
                        alterar = input(f"Alterar '{chave}'? A senha atual está definida. (s/N): ").lower()
                        if alterar != 's':
                            continue
                
                # Mostrar valor atual e solicitar novo valor
                print(f"\nConfigurando: {chave}")
                print(f"Valor atual: {valor_atual}")
                novo_valor = input("Novo valor (vazio para manter o atual): ").strip()
                
                if novo_valor:
                    config_atual[chave] = novo_valor
                    print(f"Configuração '{chave}' atualizada!")
                    time.sleep(1)
            else:
                print("Opção inválida!")
                time.sleep(1)
        except ValueError:
            print("Por favor, digite um número válido.")
            time.sleep(1)

def salvar_configuracoes_env(config_atual, categorias):
    """
    Salva as configurações no arquivo .env.
    
    Args:
        config_atual (dict): Configurações atuais
        categorias (dict): Dicionário com categorias e suas configurações
    """
    try:
        # Fazer backup do arquivo atual
        if os.path.exists('.env'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs('backups', exist_ok=True)
            backup_file = f"backups/.env_backup_{timestamp}"
            with open('.env', 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
        
        # Escrever novo arquivo
        with open('.env', 'w') as f:
            f.write("# Configurações do Bot de Trading com ML\n")
            f.write("# Arquivo gerado automaticamente\n")
            f.write(f"# Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Escrever configurações por categoria
            for categoria, chaves in categorias.items():
                if chaves:  # Só escrever categorias com configurações
                    f.write(f"\n# {categoria} ===================\n")
                    for chave in chaves:
                        if chave in config_atual:
                            f.write(f"{chave}={config_atual[chave]}\n")
            
            # Adicionar configurações que não estão em nenhuma categoria
            todas_chaves_categorizadas = [chave for chaves in categorias.values() for chave in chaves]
            sem_categoria = [chave for chave in config_atual if chave not in todas_chaves_categorizadas]
            
            if sem_categoria:
                f.write("\n# Outras configurações ===================\n")
                for chave in sem_categoria:
                    f.write(f"{chave}={config_atual[chave]}\n")
        
        print("\nConfigurações salvas com sucesso!")
        print(f"Backup criado em: {backup_file}")
        
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        input("\nPressione Enter para continuar...")

def treinar_classificador_regime(config):
    print("\nFunção de treinar classificador será implementada em breve.")
    input("\nPressione Enter para continuar...")

def treinar_filtro_sinais(config):
    print("\nFunção de treinar filtro será implementada em breve.")
    input("\nPressione Enter para continuar...")

def otimizar_parametros(config):
    """
    Executa a otimização de parâmetros utilizando técnicas de ML.
    Usa otimização bayesiana para encontrar os melhores parâmetros para a estratégia.
    
    Args:
        config (dict): Configurações do bot
    """
    logger = logging.getLogger('iniciar_bot_ml')
    exibir_cabecalho("OTIMIZAÇÃO DE PARÂMETROS")
    
    # Verificar se o módulo de otimização está disponível
    try:
        from src.ml.otimizacao_bayesiana import OtimizadorBayesiano, criar_espaco_busca_adx
    except ImportError as e:
        logger.error(f"Erro ao importar o módulo de otimização: {e}")
        print(f"\nErro ao importar o módulo de otimização: {e}")
        print("Verifique se todos os módulos necessários estão instalados.")
        input("\nPressione Enter para continuar...")
        return
    
    # Obter configurações básicas
    par = config.get('TRADING_PAIR', 'BTCUSDT')
    timeframe = config.get('CANDLE_INTERVAL', '1h')
    dias = int(config.get('HISTORICO_DIAS', 30))
    position_size = float(config.get('POSITION_SIZE', 10.0))
    
    # Exibir configurações atuais
    print(f"Par de trading: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    print(f"Tamanho da posição: {position_size}")
    print("="*60)
    
    # Configurar a otimização
    print("\nCONFIGURAÇÃO DA OTIMIZAÇÃO")
    
    # Permitir personalizar os parâmetros básicos
    personalizar = input("\nDeseja personalizar os parâmetros básicos? (s/N): ")
    
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
    
    # Configurar parâmetros da otimização
    try:
        n_iteracoes = int(input("Número de iterações [50]: ") or "50")
        random_starts = int(input("Pontos aleatórios iniciais [10]: ") or "10")
    except ValueError:
        n_iteracoes = 50
        random_starts = 10
        print("\nValores inválidos. Usando valores padrão.")
    
    # Configurar espaço de busca
    print("\nCONFIGURAÇÃO DO ESPAÇO DE BUSCA")
    print("Defina os limites para cada parâmetro")
    
    # Configurar limites do período ADX
    try:
        adx_period_min = int(input("Período ADX mínimo [5]: ") or "5")
        adx_period_max = int(input("Período ADX máximo [30]: ") or "30")
    except ValueError:
        adx_period_min = 5
        adx_period_max = 30
        print("Valores inválidos. Usando valores padrão.")
    
    # Configurar limites do limiar ADX
    try:
        adx_threshold_min = int(input("Limiar ADX mínimo [15]: ") or "15")
        adx_threshold_max = int(input("Limiar ADX máximo [40]: ") or "40")
    except ValueError:
        adx_threshold_min = 15
        adx_threshold_max = 40
        print("Valores inválidos. Usando valores padrão.")
    
    # Configurar limites do limiar DI
    try:
        di_threshold_min = int(input("Limiar DI mínimo [10]: ") or "10")
        di_threshold_max = int(input("Limiar DI máximo [30]: ") or "30")
    except ValueError:
        di_threshold_min = 10
        di_threshold_max = 30
        print("Valores inválidos. Usando valores padrão.")
    
    # Confirmar início da otimização
    print("\nCONFIGURAÇÃO DA OTIMIZAÇÃO")
    print(f"Par: {par}")
    print(f"Timeframe: {timeframe}")
    print(f"Dias de histórico: {dias}")
    print(f"Número de iterações: {n_iteracoes}")
    print(f"Pontos aleatórios iniciais: {random_starts}")
    print("\nEspaço de busca:")
    print(f"Período ADX: {adx_period_min} a {adx_period_max}")
    print(f"Limiar ADX: {adx_threshold_min} a {adx_threshold_max}")
    print(f"Limiar DI: {di_threshold_min} a {di_threshold_max}")
    print("="*60)
    
    confirmar = input("\nIniciar otimização com os parâmetros acima? (s/N): ")
    if confirmar.lower() != 's':
        print("Otimização cancelada.")
        input("\nPressione Enter para continuar...")
        return
    
    # Criar diretório para resultados da otimização
    os.makedirs('resultados/otimizacao', exist_ok=True)
    
    # Timestamp para identificação
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_resultado = f"otimizacao_{par}_{timeframe}_{timestamp}"
    caminho_resultado = f"resultados/otimizacao/{nome_resultado}.json"
    
    # Criar espaço de busca
    espaco_busca = criar_espaco_busca_adx(
        adx_period_min=adx_period_min,
        adx_period_max=adx_period_max,
        adx_threshold_min=adx_threshold_min,
        adx_threshold_max=adx_threshold_max,
        di_threshold_min=di_threshold_min,
        di_threshold_max=di_threshold_max
    )
    
    # Iniciar otimização
    print("\nIniciando otimização de parâmetros...")
    print("Este processo pode demorar bastante tempo, dependendo do número de iterações.")
    print("Por favor, aguarde...")
    
    inicio = datetime.now()
    
    try:
        # Criar e executar otimizador
        otimizador = OtimizadorBayesiano(
            par=par,
            timeframe=timeframe,
            dias_historico=dias,
            position_size=position_size
        )
        
        # Executar otimização
        resultado = otimizador.otimizar(
            espaco_busca=espaco_busca,
            n_iteracoes=n_iteracoes,
            random_starts=random_starts
        )
        
        # Verificar resultado
        if not resultado:
            logger.error("Otimização falhou ao retornar resultado.")
            print("\nErro: A otimização não retornou resultado válido.")
            input("\nPressione Enter para continuar...")
            return
        
        # Calcular tempo de execução
        fim = datetime.now()
        duracao = fim - inicio
        
        # Exibir resultados
        exibir_cabecalho("RESULTADOS DA OTIMIZAÇÃO")
        print(f"Par: {par} | Timeframe: {timeframe} | Dias: {dias}")
        print(f"Total de iterações: {n_iteracoes}")
        print(f"Melhor valor obtido: {resultado['melhor_valor']:.4f}")
        print("\nMelhores parâmetros encontrados:")
        for param, valor in resultado['parametros'].items():
            print(f"  {param}: {valor}")
        
        print("\nHistórico de melhoria:")
        for i, (iter_num, valor) in enumerate(resultado.get('historico_melhorias', [])[:10]):
            print(f"  Iteração {iter_num}: {valor:.4f}")
        
        if len(resultado.get('historico_melhorias', [])) > 10:
            print(f"  ... e mais {len(resultado.get('historico_melhorias', [])) - 10} melhorias")
        
        print("-"*60)
        print(f"Tempo de execução: {duracao.total_seconds():.2f} segundos")
        
        # Salvar resultados
        with open(caminho_resultado, 'w') as f:
            json.dump(resultado, f, indent=2)
        
        print(f"Resultados salvos em: {caminho_resultado}")
        
        # Perguntar se deseja salvar como parâmetros padrão
        salvar_padrao = input("\nDeseja salvar estes parâmetros como padrão para o bot? (s/N): ")
        if salvar_padrao.lower() == 's':
            params_path = config.get('PARAMS_OTIMIZADOS', 'modelos/otimizador/params_otimizados.json')
            os.makedirs(os.path.dirname(params_path), exist_ok=True)
            
            try:
                with open(params_path, 'w') as f:
                    json.dump(resultado, f, indent=2)
                print(f"Parâmetros salvos como padrão em: {params_path}")
            except Exception as e:
                logger.error(f"Erro ao salvar parâmetros como padrão: {e}")
                print(f"Erro ao salvar parâmetros como padrão: {e}")
        
        print("\nOtimização concluída com sucesso!")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários: {e}")
        print(f"\nErro ao importar módulos necessários: {e}")
        print("Verifique se todos os módulos estão instalados corretamente.")
    
    except Exception as e:
        logger.error(f"Erro durante a otimização: {e}", exc_info=True)
        print(f"\nErro durante a otimização: {e}")
    
    input("\nPressione Enter para continuar...")

def ver_desempenho_modelos():
    print("\nFunção de ver desempenho será implementada em breve.")
    input("\nPressione Enter para continuar...")

def exportar_modelos():
    print("\nFunção de exportar modelos será implementada em breve.")
    input("\nPressione Enter para continuar...")

def importar_modelos():
    print("\nFunção de importar modelos será implementada em breve.")
    input("\nPressione Enter para continuar...")

def monitorar_recursos():
    print("\nFunção de monitorar recursos será implementada em breve.")
    input("\nPressione Enter para continuar...")

def ver_logs_tempo_real():
    print("\nFunção de ver logs em tempo real será implementada em breve.")
    input("\nPressione Enter para continuar...")

def ver_estatisticas_rede():
    print("\nFunção de ver estatísticas de rede será implementada em breve.")
    input("\nPressione Enter para continuar...")

def ver_logs_bot():
    print("\nFunção de ver logs do bot será implementada em breve.")
    input("\nPressione Enter para continuar...")

def exportar_relatorios():
    print("\nFunção de exportar relatórios será implementada em breve.")
    input("\nPressione Enter para continuar...")

def verificar_dependencias_menu():
    print("\nVerificando dependências do sistema...")
    verificar_dependencias()
    verificar_dependencias_ml()
    input("\nPressione Enter para continuar...")

def exportar_configuracoes(config):
    print("\nFunção de exportar configurações será implementada em breve.")
    input("\nPressione Enter para continuar...")

def importar_dados_historicos():
    print("\nFunção de importar dados históricos será implementada em breve.")
    input("\nPressione Enter para continuar...")

def fazer_backup():
    print("\nFunção de fazer backup será implementada em breve.")
    input("\nPressione Enter para continuar...")

def restaurar_backup():
    print("\nFunção de restaurar backup será implementada em breve.")
    input("\nPressione Enter para continuar...")

def ver_manual():
    print("\nFunção de ver manual será implementada em breve.")
    input("\nPressione Enter para continuar...")

# Função principal
def main():
    """
    Função principal que controla a execução do programa.
    """
    # Configurar logger
    logger = configurar_logger()
    logger.info("Iniciando aplicação")
    
    # Verificar ambiente
    verificar_ambiente()
    
    # Verificar configuração
    config = verificar_configuracao()
    if not config:
        logger.error("Falha na verificação de configuração. Encerrando.")
        print("\nFalha na verificação de configuração. Por favor, configure o arquivo .env corretamente.")
        input("\nPressione Enter para encerrar...")
        sys.exit(1)
    
    # Loop principal do menu
    continuar = True
    while continuar:
        continuar = menu_principal(config)
    
    # Encerrar programa
    logger.info("Encerrando aplicação")
    print("\nObrigado por usar o Bot de Trading com Machine Learning!")
    print("Encerrando aplicação...")
    time.sleep(1)

# Executar programa se for o script principal
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro não tratado: {e}")
        logging.error(f"Erro não tratado: {e}", exc_info=True)
        sys.exit(1) 