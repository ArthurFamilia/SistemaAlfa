"""
Arquivo de configuração central do bot de trading.

Este arquivo contém todas as configurações importantes do bot:
- Parâmetros de mercado (símbolo, tamanho da posição)
- Configurações dos indicadores (períodos e limiares)
- Multiplicadores para cálculo de stops e alvos
- Configurações do mercado de futuros (alavancagem, tipo de margem)
"""

import os
import ast
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env, se existir
load_dotenv()

#==========================================================
# CONFIGURAÇÕES DO PAR DE TRADING
#==========================================================
# Compatibilidade com nomes antigos e novos
SYMBOL = os.getenv('TRADING_PAIR', os.getenv('PAIR', 'BTCUSDT'))
KLINE_INTERVAL = os.getenv('CANDLE_INTERVAL', os.getenv('TIMEFRAME', '1h'))
KLINE_LIMIT = int(os.getenv('KLINE_LIMIT', '100'))
POSITION_SIZE = float(os.getenv('POSITION_SIZE', '10.0'))

#==========================================================
# CONFIGURAÇÕES DOS INDICADORES
#==========================================================
ADX_PERIOD = int(os.getenv('ADX_PERIOD', '8'))
ADX_THRESHOLD = float(os.getenv('ADX_THRESHOLD', '25.0'))
ADX_PREVIOUS_CANDLES = int(os.getenv('ADX_PREVIOUS_CANDLES', '2'))

DI_PLUS_PERIOD = int(os.getenv('DI_PLUS_PERIOD', '8'))
DI_MINUS_PERIOD = int(os.getenv('DI_MINUS_PERIOD', '8'))
DI_THRESHOLD = float(os.getenv('DI_THRESHOLD', '20.0'))
# Limiares específicos para DI+ e DI-
DI_PLUS_THRESHOLD = float(os.getenv('DI_PLUS_THRESHOLD', DI_THRESHOLD))
DI_MINUS_THRESHOLD = float(os.getenv('DI_MINUS_THRESHOLD', DI_THRESHOLD))

ATR_PERIOD = int(os.getenv('ATR_PERIOD', '14'))

#==========================================================
# MULTIPLICADORES PARA STOPS E TARGETS
#==========================================================
STOP_MULTIPLIER_BUY = float(os.getenv('STOP_MULTIPLIER_BUY', '2.0'))
GAIN_MULTIPLIER_BUY = float(os.getenv('GAIN_MULTIPLIER_BUY', '3.0'))
STOP_MULTIPLIER_SELL = float(os.getenv('STOP_MULTIPLIER_SELL', '2.0'))
GAIN_MULTIPLIER_SELL = float(os.getenv('GAIN_MULTIPLIER_SELL', '3.0'))

#==========================================================
# CONFIGURAÇÕES DO MERCADO DE FUTUROS
#==========================================================
FUTURES_LEVERAGE = int(os.getenv('FUTURES_LEVERAGE', '125'))
FUTURES_MARGIN_TYPE = os.getenv('FUTURES_MARGIN_TYPE', 'CROSSED')

#==========================================================
# CONFIGURAÇÕES DE LOGGING
#==========================================================
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = f"{LOG_DIR}/bot.log"

#==========================================================
# PARÂMETROS DO MINERADOR DE ESTRATÉGIAS
#==========================================================
# Converte strings de lista do .env em listas Python
def parse_list_env(var_name, default):
    value = os.getenv(var_name, default)
    if value:
        # Remove espaços extras e verifica se está entre colchetes
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            # Usa ast.literal_eval para converter string em lista de forma segura
            try:
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # Fallback para o método anterior se falhar
                return [float(x.strip()) for x in value[1:-1].split(',')]
        else:
            # Método anterior para compatibilidade
            return [float(x.strip()) for x in value.split(',')]
    return []

ADX_THRESHOLDS = parse_list_env('ADX_THRESHOLDS', '[25, 32]')
DI_THRESHOLDS = parse_list_env('DI_THRESHOLDS', '[15, 20, 25]')
ATR_PERIODS = parse_list_env('ATR_PERIODS', '[10, 12, 14, 16, 18, 20]')
STOP_MULTIPLIERS_BUY = parse_list_env('STOP_MULTIPLIERS_BUY', '[1.5, 2.0]')
STOP_MULTIPLIERS_SELL = parse_list_env('STOP_MULTIPLIERS_SELL', '[1.5, 2.0]')
GAIN_MULTIPLIERS_BUY = parse_list_env('GAIN_MULTIPLIERS_BUY', '[3.0, 4.0, 5.0]')
GAIN_MULTIPLIERS_SELL = parse_list_env('GAIN_MULTIPLIERS_SELL', '[3.0, 4.0, 5.0]')

# Períodos para os indicadores (usados pelo minerador de estratégias)
ADX_PERIODS = parse_list_env('ADX_PERIODS', '[8, 10, 12, 14]')
DI_PLUS_PERIODS = parse_list_env('DI_PLUS_PERIODS', '[8, 10, 12, 14]')
DI_MINUS_PERIODS = parse_list_env('DI_MINUS_PERIODS', '[8, 10, 12, 14]')

#==========================================================
# CONFIGURAÇÕES DE MACHINE LEARNING
#==========================================================
# Caminhos para modelos de ML (compatibilidade com nomes antigos e novos)
MODELO_CLASSIFICADOR = os.getenv('MODELO_CLASSIFICADOR', os.getenv('CAMINHO_MODELO_REGIME', 'modelos/regimes/classificador_regimes.joblib'))
MODELO_FILTRO = os.getenv('MODELO_FILTRO', os.getenv('CAMINHO_MODELO_FILTRO', 'modelos/filtro_sinais/filtro_sinais.joblib'))
PARAMS_OTIMIZADOS = os.getenv('PARAMS_OTIMIZADOS', 'modelos/otimizador/params_otimizados.json')

# Configurações de uso de ML
USAR_CLASSIFICADOR_REGIMES = os.getenv('USAR_CLASSIFICADOR_REGIMES', 'TRUE').upper() == 'TRUE'
USAR_FILTRO_SINAIS = os.getenv('USAR_FILTRO_SINAIS', 'TRUE').upper() == 'TRUE'
USAR_OTIMIZACAO_BAYESIANA = os.getenv('USAR_OTIMIZACAO_BAYESIANA', 'TRUE').upper() == 'TRUE'
LIMIAR_PROBABILIDADE_SINAL = float(os.getenv('LIMIAR_PROBABILIDADE_SINAL', '0.65'))

#==========================================================
# CONFIGURAÇÕES DE TIMEOUT E RETENTATIVAS
#==========================================================
# Configurações de conexão
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))  # segundos
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))  # segundos
RETRY_BACKOFF = float(os.getenv('RETRY_BACKOFF', '2.0'))  # multiplicador para backoff exponencial

# Configurações de simulação de rede
SIMULAR_REDE = os.getenv('SIMULAR_REDE', os.getenv('SIMULAR_LATENCIA', 'FALSE')).upper() == 'TRUE'
LATENCIA_BASE = float(os.getenv('LATENCIA_BASE', os.getenv('LATENCIA_SIMULADA', '50')))
VARIACAO_LATENCIA = float(os.getenv('VARIACAO_LATENCIA', '30'))
PROB_LATENCIA_ALTA = float(os.getenv('PROB_LATENCIA_ALTA', '0.05'))
MULTIPLICADOR_PICO = float(os.getenv('MULTIPLICADOR_PICO', '10'))
USAR_PING_REAL = os.getenv('USAR_PING_REAL', 'TRUE').upper() == 'TRUE'
USAR_LATENCIA_REAL = os.getenv('USAR_LATENCIA_REAL', 'TRUE').upper() == 'TRUE'

# Configurações de logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"