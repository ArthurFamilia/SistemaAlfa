"""
Bot de Trading ADX com integração de Machine Learning

Esta versão avançada do bot de trading integra:
1. Classificação de regimes de mercado (Random Forest)
2. Filtro de sinais com XGBoost
3. Parâmetros otimizados por otimização bayesiana
"""

import time
import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv

from src.services.binance_service import BinanceService
from src.services.adx_strategy import ADXStrategy
from src.config.config import (
    SYMBOL, KLINE_INTERVAL, 
    POSITION_SIZE
)
from src.utils.logger import Logger
from src.utils.network_simulator import NetworkSimulator

# Importações de ML
from src.ml.classificador_regimes import ClassificadorRegimeMercado
from src.ml.filtro_sinais import FiltroSinaisXGBoost

# Carrega variáveis de ambiente
load_dotenv()

class TradingBotML:
    """
    Bot de trading avançado com integração de machine learning.
    
    Esta versão do bot inclui:
    - Classificação automática de regimes de mercado
    - Parâmetros otimizados para cada regime de mercado
    - Filtro de sinais para melhorar a qualidade das entradas
    """
    
    def __init__(self):
        """Inicializa o bot de trading com componentes de ML."""
        # Configuração de intervalo de atualização (em segundos)
        self.interval = 2
        
        # Inicializa o logger
        self.logger = Logger()
        self.logger.log_info(f"Inicializando bot de trading ML para {SYMBOL}")
        
        # Carrega o modo de simulação do arquivo .env, se existir
        self.simulation_mode = os.getenv('SIMULATION_MODE', 'TRUE').upper() == 'TRUE'
        
        # Inicializa o simulador de rede
        self.network_simulator = NetworkSimulator()
        self.usar_ping_real = os.getenv('USAR_PING_REAL', 'TRUE').upper() == 'TRUE'
        self.usar_latencia_real = os.getenv('USAR_LATENCIA_REAL', 'TRUE').upper() == 'TRUE'
        
        # Inicializa os serviços
        self.binance_service = BinanceService(simulation_mode=self.simulation_mode)
        self.strategy = ADXStrategy(self.binance_service)
        
        # Estado do bot
        self.running = False
        self.last_check_time = None
        self.market_data_df = None  # DataFrame para armazenar dados de mercado
        
        # Componentes de ML
        self.classificador_regime = None
        self.filtro_sinais = None
        self.regime_atual = None
        self.parametros_atuais = {}
        
        # Inicializar componentes ML
        self._inicializar_componentes_ml()
        
        # Log de inicialização
        if not self.simulation_mode:
            # Aviso visual destacado para modo real
            self.logger.log_info("="*80)
            self.logger.log_info("                      ⚠️⚠️⚠️ AVISO IMPORTANTE ⚠️⚠️⚠️")
            self.logger.log_info("               BOT INICIALIZADO EM MODO DE PRODUÇÃO (REAL)")
            self.logger.log_info("          TODAS AS OPERAÇÕES SERÃO EXECUTADAS NA SUA CONTA REAL")
            self.logger.log_info("="*80)
        else:
            self.logger.log_info("Bot inicializado em modo de SIMULAÇÃO (sem operações reais)")
        
        self.logger.log_info(f"Intervalo de verificação: {self.interval} segundos")
        self.logger.log_info(f"Par de trading: {SYMBOL}")
        
        # Log de componentes ML
        self.logger.log_info("Componentes de ML inicializados:")
        self.logger.log_info(f"- Classificador de regimes: {'Ativo' if self.classificador_regime else 'Inativo'}")
        self.logger.log_info(f"- Filtro de sinais: {'Ativo' if self.filtro_sinais else 'Inativo'}")
    
    def _inicializar_componentes_ml(self):
        """Inicializa os componentes de machine learning."""
        try:
            # Criar diretórios para modelos, se não existirem
            diretorios = [
                'modelos',
                'modelos/regimes',
                'modelos/filtro_sinais',
                'modelos/otimizador',
                'modelos/classificador_regime'
            ]
            
            for diretorio in diretorios:
                if not os.path.exists(diretorio):
                    self.logger.log_info(f"Criando diretório: {diretorio}")
                    os.makedirs(diretorio, exist_ok=True)
            
            # Tentar carregar classificador de regimes
            self.classificador_regime = ClassificadorRegimeMercado()
            caminho_modelo_regime = os.getenv('CAMINHO_MODELO_REGIME', 'modelos/regimes/classificador_regimes.joblib')
            
            # Carregar parâmetros por regime
            self.parametros_por_regime = {
                0: {  # Mercado Lateral
                    'ADX_THRESHOLD': 25.0,
                    'STOP_MULTIPLIER_BUY': 1.5,
                    'STOP_MULTIPLIER_SELL': 1.5,
                    'GAIN_MULTIPLIER_BUY': 3.0,
                    'GAIN_MULTIPLIER_SELL': 3.0
                },
                1: {  # Tendência de Alta
                    'ADX_THRESHOLD': 20.0,
                    'STOP_MULTIPLIER_BUY': 2.0,
                    'STOP_MULTIPLIER_SELL': 1.5,
                    'GAIN_MULTIPLIER_BUY': 4.0,
                    'GAIN_MULTIPLIER_SELL': 2.5
                },
                2: {  # Tendência de Baixa
                    'ADX_THRESHOLD': 20.0,
                    'STOP_MULTIPLIER_BUY': 1.5,
                    'STOP_MULTIPLIER_SELL': 2.0,
                    'GAIN_MULTIPLIER_BUY': 2.5,
                    'GAIN_MULTIPLIER_SELL': 4.0
                },
                3: {  # Alta Volatilidade
                    'ADX_THRESHOLD': 30.0,
                    'STOP_MULTIPLIER_BUY': 2.5,
                    'STOP_MULTIPLIER_SELL': 2.5,
                    'GAIN_MULTIPLIER_BUY': 5.0,
                    'GAIN_MULTIPLIER_SELL': 5.0
                }
            }
            
            # Configurar parâmetros por regime
            self.classificador_regime.configurar_parametros_por_regime(self.parametros_por_regime)
            
            # Tentar carregar modelo pré-treinado
            try:
                if os.path.exists(caminho_modelo_regime):
                    self.classificador_regime.carregar_modelo(caminho_modelo_regime)
                    self.logger.log_info(f"Classificador de regimes carregado de {caminho_modelo_regime}")
                else:
                    self.logger.log_warning(f"Modelo de classificador não encontrado em {caminho_modelo_regime}")
                    self.classificador_regime = None
            except Exception as e:
                self.logger.log_error(f"Erro ao carregar classificador de regimes: {str(e)}")
                self.classificador_regime = None
            
            # Tentar carregar filtro de sinais
            self.filtro_sinais = FiltroSinaisXGBoost()
            caminho_modelo_filtro = os.getenv('CAMINHO_MODELO_FILTRO', 'modelos/filtro_sinais/filtro_sinais.joblib')
            
            try:
                if os.path.exists(caminho_modelo_filtro):
                    self.filtro_sinais.carregar_modelo(caminho_modelo_filtro)
                    self.logger.log_info(f"Filtro de sinais carregado de {caminho_modelo_filtro}")
                else:
                    self.logger.log_warning(f"Modelo de filtro não encontrado em {caminho_modelo_filtro}")
                    self.filtro_sinais = None
            except Exception as e:
                self.logger.log_error(f"Erro ao carregar filtro de sinais: {str(e)}")
                self.filtro_sinais = None
                
        except Exception as e:
            self.logger.log_error(f"Erro ao inicializar componentes ML: {str(e)}")
            self.classificador_regime = None
            self.filtro_sinais = None
    
    def run(self):
        """Executa o loop principal do bot de trading."""
        self.running = True
        
        if not self.simulation_mode:
            # Aviso visual de início de operação em modo real
            self.logger.log_info("\n" + "="*80)
            self.logger.log_info("               ⚠️⚠️⚠️ INICIANDO OPERAÇÕES REAIS ⚠️⚠️⚠️")
            self.logger.log_info("               Pressione CTRL+C para interromper")
            self.logger.log_info("="*80 + "\n")
        else:
            self.logger.log_info("Bot iniciado em modo de SIMULAÇÃO. Monitorando mercado...")
        
        # Contador para estatísticas de rede
        network_stats_counter = 0
        
        # Contador para identificação de regime (a cada 10 ciclos)
        regime_check_counter = 0
        
        try:
            while self.running:
                # Registra o tempo de início para cálculo de tempo de execução
                cycle_start = time.time()
                
                # Aplicar latência simulada ou mede latência real
                if self.usar_latencia_real:
                    latencia = self.network_simulator.medir_latencia_real()
                else:
                    latencia = self.network_simulator.aplicar_latencia()
                
                ping = self.network_simulator.medir_ou_simular_ping(self.usar_ping_real)
                
                # Atualizar dados históricos
                self._atualizar_dados_historicos()
                
                # Verificar regime de mercado a cada 10 ciclos
                regime_check_counter += 1
                if regime_check_counter >= 10 and self.classificador_regime is not None:
                    regime_check_counter = 0
                    self._identificar_regime_atual()
                
                # Executa o ciclo de verificação
                self._execute_check_cycle()
                
                # Registrar estatísticas de rede periodicamente (a cada 30 ciclos)
                network_stats_counter += 1
                if network_stats_counter >= 30:
                    self.logger.log_network_stats(self.network_simulator.obter_estatisticas_para_logger())
                    network_stats_counter = 0
                
                # Calcula o tempo para próxima verificação (considerando o tempo de execução)
                execution_time = time.time() - cycle_start
                sleep_time = max(0.1, self.interval - execution_time)
                
                # Aguarda até o próximo ciclo
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.log_info("Bot interrompido pelo usuário")
        except Exception as e:
            self.logger.log_error(f"Erro fatal: {str(e)}")
        finally:
            self.running = False
            self.logger.log_info("Bot finalizado")
            
            # Registrar estatísticas finais de rede
            self.logger.log_network_stats(self.network_simulator.obter_estatisticas_para_logger())
    
    def _atualizar_dados_historicos(self):
        """Atualiza o dataframe de dados históricos."""
        try:
            # Obter klines
            klines = self.binance_service.get_klines_raw()
            
            if klines is None or len(klines) == 0:
                self.logger.log_error("Não foi possível obter dados históricos")
                return
                
            # Converter para DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Converter tipos
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            # Calcular indicadores se necessário
            if 'adx' not in df.columns:
                df = self.strategy.calculate_indicators_df(df)
                
            # Atualizar dataframe
            self.market_data_df = df
            
        except Exception as e:
            self.logger.log_error(f"Erro ao atualizar dados históricos: {str(e)}")
    
    def _identificar_regime_atual(self):
        """Identifica o regime atual de mercado usando o classificador."""
        if self.classificador_regime is None or self.market_data_df is None:
            return
            
        try:
            # Identificar regime atual
            regime, probabilidades = self.classificador_regime.identificar_regime(self.market_data_df)
            
            # Se o regime mudou, atualizar parâmetros
            if self.regime_atual != regime:
                self.regime_atual = regime
                self._atualizar_parametros_por_regime(regime)
                
                # Log da mudança de regime
                regime_nome = self.classificador_regime.regimes.get(regime, f"Desconhecido ({regime})")
                self.logger.log_info(f"Regime de mercado identificado: {regime_nome}")
                self.logger.log_info(f"Probabilidades: {[f'{self.classificador_regime.regimes[i]}: {p:.2f}' for i, p in enumerate(probabilidades)]}")
                self.logger.log_info(f"Parâmetros atualizados para o regime: {regime_nome}")
                
        except Exception as e:
            self.logger.log_error(f"Erro ao identificar regime: {str(e)}")
    
    def _atualizar_parametros_por_regime(self, regime):
        """Atualiza os parâmetros da estratégia com base no regime identificado."""
        if self.classificador_regime is None:
            return
            
        try:
            # Obter parâmetros para o regime atual
            self.parametros_atuais = self.classificador_regime.obter_parametros_otimos(regime)
            
            # Log dos novos parâmetros
            self.logger.log_info("Parâmetros atualizados:")
            for param, valor in self.parametros_atuais.items():
                self.logger.log_info(f"- {param}: {valor}")
                
        except Exception as e:
            self.logger.log_error(f"Erro ao atualizar parâmetros: {str(e)}")
    
    def _execute_check_cycle(self):
        """Executa um ciclo de verificação de condições de trading."""
        try:
            # Obter dados de mercado
            market_data = self._process_market_data()
            if market_data is None:
                return
            
            adx, di_plus, di_minus, atr, bid_price, ask_price, volume_24h = market_data
            
            # Registrar dados de mercado
            self._log_market_data(adx, di_plus, di_minus, atr, bid_price, ask_price, volume_24h)
            
            # Exibir dados no console
            self._exibir_dados_mercado(adx, di_plus, di_minus, atr, bid_price, ask_price, volume_24h)
            
            # Verificar condições de trading com ML
            self._check_trading_conditions_ml(adx, di_plus, di_minus, atr, bid_price, ask_price)
            
        except Exception as e:
            error_msg = f"Erro no ciclo de verificação: {str(e)}"
            self.logger.log_error(error_msg)
            
            if not self.simulation_mode:
                # Aviso especial para erros em modo real
                self.logger.log_error("="*80)
                self.logger.log_error("⚠️⚠️⚠️ ALERTA: ERRO DURANTE OPERAÇÃO EM MODO REAL ⚠️⚠️⚠️")
                self.logger.log_error("Verifique imediatamente o estado da sua conta na Binance!")
                self.logger.log_error("="*80)
    
    def _log_market_data(self, adx, di_plus, di_minus, atr, bid_price, ask_price, volume_24h):
        """
        Registra os dados atuais do mercado para análise.
        
        Args:
            adx (float): Valor atual do ADX
            di_plus (float): Valor atual do DI+
            di_minus (float): Valor atual do DI-
            atr (float): Valor atual do ATR
            bid_price (float): Preço de venda atual
            ask_price (float): Preço de compra atual
            volume_24h (str): Volume de 24 horas formatado
        """
        # Calcula o spread entre bid e ask
        spread = ask_price - bid_price if (bid_price and ask_price) else 0
        spread_pct = (spread / bid_price * 100) if bid_price else 0
        
        # Prepara os dados do mercado para log
        market_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": SYMBOL,
            "adx": adx,
            "di_plus": di_plus,
            "di_minus": di_minus,
            "atr": atr,
            "bid_price": bid_price,
            "ask_price": ask_price,
            "spread": spread,
            "spread_pct": spread_pct,
            "volume_24h": volume_24h,
            "regime": self.regime_atual
        }
        
        # Usa o logger para exibir e registrar os dados
        self.logger.log_market_data(market_data)
    
    def _check_trading_conditions_ml(self, adx, di_plus, di_minus, atr, bid_price, ask_price):
        """
        Verifica condições de trading usando componentes de ML.
        
        Args:
            adx (float): Valor atual do ADX
            di_plus (float): Valor atual do DI+
            di_minus (float): Valor atual do DI-
            atr (float): Valor atual do ATR
            bid_price (float): Preço de venda atual
            ask_price (float): Preço de compra atual
        """
        try:
            # Verificar se já existe uma posição aberta
            posicao_atual = self.binance_service.get_position_info()
            if posicao_atual is not None:
                self.logger.log_info(f"Já existe uma posição {posicao_atual['side']} aberta. Ignorando sinais.")
                return
                
            # Obter o ADX_THRESHOLD para o regime atual
            adx_threshold = self.parametros_atuais.get('ADX_THRESHOLD', 25.0)
            
            # 1. Verificação tradicional da estratégia ADX
            if adx > adx_threshold:
                # 2. Direção da tendência
                if di_plus > di_minus:  # Tendência de alta
                    # Obter os multiplicadores específicos para o regime
                    stop_multiplier = self.parametros_atuais.get('STOP_MULTIPLIER_BUY', 2.0)
                    gain_multiplier = self.parametros_atuais.get('GAIN_MULTIPLIER_BUY', 3.0)
                    
                    # 3. Aplicar filtro de sinal ML se disponível
                    if self.filtro_sinais is not None and self.market_data_df is not None:
                        # Extrair features para o filtro
                        try:
                            # Usando o último índice do DataFrame
                            idx = len(self.market_data_df) - 1
                            features = self.filtro_sinais.extrair_features(self.market_data_df, idx=idx)
                            
                            # Verificar qualidade do sinal
                            probabilidade = self.filtro_sinais.prever_qualidade_sinal(features)
                            eh_qualidade = self.filtro_sinais.sinal_eh_qualidade(features)
                            
                            self.logger.log_info(f"Qualidade do sinal: {probabilidade:.2f} (limiar: {self.filtro_sinais.limiar_qualidade})")
                            
                            # Se o sinal não for de qualidade, pular
                            if not eh_qualidade:
                                self.logger.log_info("Sinal filtrado pelo modelo de ML")
                                return
                                
                            self.logger.log_info("Sinal aprovado pelo filtro de ML")
                            
                        except Exception as e:
                            self.logger.log_error(f"Erro ao aplicar filtro de sinal: {str(e)}")
                            # Continuar mesmo com erro no filtro
                    
                    # 4. Calcular preços de entrada, stop e alvo
                    entry_price = ask_price
                    stop_loss = entry_price - (atr * stop_multiplier)
                    take_profit = entry_price + (atr * gain_multiplier)
                    
                    # 5. Validação final
                    risk = entry_price - stop_loss
                    reward = take_profit - entry_price
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    if risk_reward_ratio < 1.5:
                        self.logger.log_info(f"Relação risco/recompensa insuficiente: {risk_reward_ratio:.2f}")
                        return
                    
                    # 6. Executar ordem de compra
                    self.logger.log_info("=== SINAL DE COMPRA GERADO ===")
                    self.logger.log_info(f"ADX: {adx:.2f}, DI+: {di_plus:.2f}, DI-: {di_minus:.2f}")
                    self.logger.log_info(f"Preço de entrada: {entry_price}")
                    self.logger.log_info(f"Stop Loss: {stop_loss}")
                    self.logger.log_info(f"Take Profit: {take_profit}")
                    self.logger.log_info(f"Relação risco/recompensa: {risk_reward_ratio:.2f}")
                    
                    if not self.simulation_mode:
                        # Código para executar ordem real
                        self._executar_ordem_compra(entry_price, stop_loss, take_profit)
                
                elif di_minus > di_plus:  # Tendência de baixa
                    # Obter os multiplicadores específicos para o regime
                    stop_multiplier = self.parametros_atuais.get('STOP_MULTIPLIER_SELL', 2.0)
                    gain_multiplier = self.parametros_atuais.get('GAIN_MULTIPLIER_SELL', 3.0)
                    
                    # Aplicar filtro de sinal ML se disponível
                    if self.filtro_sinais is not None and self.market_data_df is not None:
                        # Extrair features para o filtro
                        try:
                            # Usando o último índice do DataFrame
                            idx = len(self.market_data_df) - 1
                            features = self.filtro_sinais.extrair_features(self.market_data_df, idx=idx)
                            
                            # Verificar qualidade do sinal
                            probabilidade = self.filtro_sinais.prever_qualidade_sinal(features)
                            eh_qualidade = self.filtro_sinais.sinal_eh_qualidade(features)
                            
                            self.logger.log_info(f"Qualidade do sinal: {probabilidade:.2f} (limiar: {self.filtro_sinais.limiar_qualidade})")
                            
                            # Se o sinal não for de qualidade, pular
                            if not eh_qualidade:
                                self.logger.log_info("Sinal filtrado pelo modelo de ML")
                                return
                                
                            self.logger.log_info("Sinal aprovado pelo filtro de ML")
                            
                        except Exception as e:
                            self.logger.log_error(f"Erro ao aplicar filtro de sinal: {str(e)}")
                            # Continuar mesmo com erro no filtro
                    
                    # Calcular preços de entrada, stop e alvo
                    entry_price = bid_price
                    stop_loss = entry_price + (atr * stop_multiplier)
                    take_profit = entry_price - (atr * gain_multiplier)
                    
                    # Validação final
                    risk = stop_loss - entry_price
                    reward = entry_price - take_profit
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    if risk_reward_ratio < 1.5:
                        self.logger.log_info(f"Relação risco/recompensa insuficiente: {risk_reward_ratio:.2f}")
                        return
                    
                    # Executar ordem de venda
                    self.logger.log_info("=== SINAL DE VENDA GERADO ===")
                    self.logger.log_info(f"ADX: {adx:.2f}, DI+: {di_plus:.2f}, DI-: {di_minus:.2f}")
                    self.logger.log_info(f"Preço de entrada: {entry_price}")
                    self.logger.log_info(f"Stop Loss: {stop_loss}")
                    self.logger.log_info(f"Take Profit: {take_profit}")
                    self.logger.log_info(f"Relação risco/recompensa: {risk_reward_ratio:.2f}")
                    
                    if not self.simulation_mode:
                        # Código para executar ordem real
                        self._executar_ordem_venda(entry_price, stop_loss, take_profit)
            
        except Exception as e:
            self.logger.log_error(f"Erro durante verificação de condições de trading: {str(e)}")
    
    def _executar_ordem_compra(self, entry_price, stop_loss, take_profit):
        """
        Executa uma ordem de compra com seus respectivos stop loss e take profit.
        
        Args:
            entry_price (float): Preço de entrada
            stop_loss (float): Preço de stop loss
            take_profit (float): Preço de take profit
        """
        try:
            # Aviso específico para operações reais
            if not self.simulation_mode:
                self.logger.log_info("="*60)
                self.logger.log_info("⚠️ EXECUTANDO ORDEM REAL DE COMPRA ⚠️")
            
            # Registrar operação
            self.logger.log_operation({
                "timestamp": datetime.now().isoformat(),
                "action": "BUY",
                "symbol": SYMBOL,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "position_size": POSITION_SIZE,
                "mode": "REAL" if not self.simulation_mode else "SIMULATION"
            })
            
            # Criar ordem através do serviço Binance
            success = self.binance_service.create_order(
                action="BUY",
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=POSITION_SIZE
            )
            
            if success:
                self.logger.log_info(f"Ordem de compra criada: {SYMBOL} @ {entry_price}")
                self.logger.log_info(f"Stop Loss: {stop_loss}, Take Profit: {take_profit}")
                
                if not self.simulation_mode:
                    self.logger.log_info("⚠️ ORDEM REAL EXECUTADA COM SUCESSO ⚠️")
                    self.logger.log_info("="*60)
            else:
                self.logger.log_error(f"Falha ao criar ordem de compra para {SYMBOL}")
                
                if not self.simulation_mode:
                    self.logger.log_error("⚠️ FALHA NA EXECUÇÃO DE ORDEM REAL ⚠️")
                    self.logger.log_error("="*60)
                
        except Exception as e:
            self.logger.log_error(f"Erro ao executar ordem de compra: {str(e)}")
            
            if not self.simulation_mode:
                self.logger.log_error("="*80)
                self.logger.log_error("⚠️⚠️⚠️ ERRO CRÍTICO NA EXECUÇÃO DE ORDEM REAL ⚠️⚠️⚠️")
                self.logger.log_error("Verifique imediatamente o estado da sua conta na Binance!")
                self.logger.log_error("="*80)
    
    def _executar_ordem_venda(self, entry_price, stop_loss, take_profit):
        """
        Executa uma ordem de venda com seus respectivos stop loss e take profit.
        
        Args:
            entry_price (float): Preço de entrada
            stop_loss (float): Preço de stop loss
            take_profit (float): Preço de take profit
        """
        try:
            # Aviso específico para operações reais
            if not self.simulation_mode:
                self.logger.log_info("="*60)
                self.logger.log_info("⚠️ EXECUTANDO ORDEM REAL DE VENDA ⚠️")
            
            # Registrar operação
            self.logger.log_operation({
                "timestamp": datetime.now().isoformat(),
                "action": "SELL",
                "symbol": SYMBOL,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "position_size": POSITION_SIZE,
                "mode": "REAL" if not self.simulation_mode else "SIMULATION"
            })
            
            # Criar ordem através do serviço Binance
            success = self.binance_service.create_order(
                action="SELL",
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=POSITION_SIZE
            )
            
            if success:
                self.logger.log_info(f"Ordem de venda criada: {SYMBOL} @ {entry_price}")
                self.logger.log_info(f"Stop Loss: {stop_loss}, Take Profit: {take_profit}")
                
                if not self.simulation_mode:
                    self.logger.log_info("⚠️ ORDEM REAL EXECUTADA COM SUCESSO ⚠️")
                    self.logger.log_info("="*60)
            else:
                self.logger.log_error(f"Falha ao criar ordem de venda para {SYMBOL}")
                
                if not self.simulation_mode:
                    self.logger.log_error("⚠️ FALHA NA EXECUÇÃO DE ORDEM REAL ⚠️")
                    self.logger.log_error("="*60)
                
        except Exception as e:
            self.logger.log_error(f"Erro ao executar ordem de venda: {str(e)}")
            
            if not self.simulation_mode:
                self.logger.log_error("="*80)
                self.logger.log_error("⚠️⚠️⚠️ ERRO CRÍTICO NA EXECUÇÃO DE ORDEM REAL ⚠️⚠️⚠️")
                self.logger.log_error("Verifique imediatamente o estado da sua conta na Binance!")
                self.logger.log_error("="*80)

    def _process_market_data(self):
        """
        Processa os dados de mercado e verifica condições de trading.
        """
        try:
            # Obter preços atuais do mercado
            bid_price, ask_price = self.binance_service.get_bid_ask_price()
            if bid_price is None or ask_price is None:
                self.logger.log_error("Não foi possível obter preços bid/ask")
                return
            
            # Obter dados de volume 24h
            volume_24h = self.binance_service.get_24h_volume()
            
            # Verificar se existe posição aberta em simulação antes de gerar novos sinais
            if self.simulation_mode:
                # Verificar se stop loss ou take profit foram atingidos no modo simulação
                if self.binance_service.verificar_stop_loss_take_profit_simulacao(bid_price, ask_price):
                    # Se algum stop ou take foi atingido, não processar sinais neste ciclo
                    return
            
            # Se os dados do mercado ainda não foram inicializados
            if self.market_data_df is None:
                # Obter dados de kline do mercado
                self.market_data_df = self.binance_service.get_klines()
                if self.market_data_df is None:
                    self.logger.log_error("Falha ao obter dados de kline")
                    return
            
            # Calcular indicadores técnicos
            adx, di_plus, di_minus = self._calcular_adx(self.market_data_df)
            atr = self._calcular_atr(self.market_data_df)
            
            if adx is None or di_plus is None or di_minus is None or atr is None:
                self.logger.log_error("Não foi possível calcular indicadores")
                return
            
            # Atualizar o regime atual com base nos indicadores
            self._atualizar_regime(adx, di_plus, di_minus)
            
            # Exibir dados de mercado e indicadores
            self._exibir_dados_mercado(adx, di_plus, di_minus, atr, bid_price, ask_price, volume_24h)
            
            # Verificar condições de trading
            self._check_trading_conditions_ml(adx, di_plus, di_minus, atr, bid_price, ask_price)
        
        except Exception as e:
            self.logger.log_error(f"Erro no processamento de dados de mercado: {str(e)}")

    def _calcular_adx(self, df):
        """
        Calcula o ADX e os indicadores relacionados a partir do DataFrame de dados de mercado.
        
        Args:
            df (DataFrame): DataFrame com dados de mercado
            
        Returns:
            tuple: (adx, di_plus, di_minus) ou (None, None, None) em caso de erro
        """
        try:
            if 'adx' in df.columns and 'di_plus' in df.columns and 'di_minus' in df.columns:
                # Usar valores já calculados
                adx = df['adx'].iloc[-1]
                di_plus = df['di_plus'].iloc[-1]
                di_minus = df['di_minus'].iloc[-1]
                return adx, di_plus, di_minus
            else:
                # Calcular através da estratégia
                return self.strategy.calculate_indicators()
        except Exception as e:
            self.logger.log_error(f"Erro ao calcular ADX: {str(e)}")
            return None, None, None
    
    def _calcular_atr(self, df):
        """
        Calcula o ATR a partir do DataFrame de dados de mercado.
        
        Args:
            df (DataFrame): DataFrame com dados de mercado
            
        Returns:
            float: Valor do ATR ou None em caso de erro
        """
        try:
            if 'atr' in df.columns:
                # Usar valor já calculado
                return df['atr'].iloc[-1]
            else:
                # Obter o ATR calculado pela estratégia
                _, _, _, _, atr = self.strategy.calculate_indicators()
                return atr
        except Exception as e:
            self.logger.log_error(f"Erro ao calcular ATR: {str(e)}")
            return None
    
    def _atualizar_regime(self, adx, di_plus, di_minus):
        """
        Atualiza o regime de mercado com base nos indicadores atuais.
        
        Args:
            adx (float): Valor atual do ADX
            di_plus (float): Valor atual do DI+
            di_minus (float): Valor atual do DI-
        """
        if self.classificador_regime is None:
            # Se não tiver classificador, usar lógica simples
            if adx < 20:
                self.regime_atual = 0  # Mercado lateral
            elif di_plus > di_minus:
                self.regime_atual = 1  # Tendência de alta
            else:
                self.regime_atual = 2  # Tendência de baixa
                
            # Se o regime mudou, atualizar parâmetros
            if self.regime_atual in self.parametros_por_regime:
                self.parametros_atuais = self.parametros_por_regime[self.regime_atual]
    
    def _exibir_dados_mercado(self, adx, di_plus, di_minus, atr, bid_price, ask_price, volume_24h):
        """
        Exibe os dados de mercado no console e registra no log.
        
        Args:
            adx (float): Valor atual do ADX
            di_plus (float): Valor atual do DI+
            di_minus (float): Valor atual do DI-
            atr (float): Valor atual do ATR
            bid_price (float): Preço de venda atual
            ask_price (float): Preço de compra atual
            volume_24h (str): Volume de 24 horas formatado
        """
        try:
            # Calcular o spread
            spread = ask_price - bid_price if (bid_price and ask_price) else 0
            spread_pct = (spread / bid_price * 100) if bid_price else 0
            
            # Informações sobre o regime
            regime_nome = "Desconhecido"
            if self.classificador_regime and self.regime_atual is not None:
                regime_nome = self.classificador_regime.regimes.get(self.regime_atual, f"Regime {self.regime_atual}")
            elif self.regime_atual is not None:
                regimes_nomes = {0: "Lateral", 1: "Alta", 2: "Baixa", 3: "Alta Volatilidade"}
                regime_nome = regimes_nomes.get(self.regime_atual, f"Regime {self.regime_atual}")
            
            # Preparar dados de mercado
            market_data = {
                "timestamp": datetime.now().isoformat(),
                "symbol": SYMBOL,
                "adx": adx,
                "di_plus": di_plus,
                "di_minus": di_minus,
                "atr": atr,
                "bid_price": bid_price,
                "ask_price": ask_price,
                "spread": spread,
                "spread_pct": spread_pct,
                "volume_24h": volume_24h,
                "regime": f"{self.regime_atual} ({regime_nome})" if self.regime_atual is not None else "N/A"
            }
            
            # Registrar no log
            self.logger.log_market_data(market_data)
        except Exception as e:
            self.logger.log_error(f"Erro ao exibir dados de mercado: {str(e)}")


if __name__ == "__main__":
    # Criar e iniciar o bot
    bot = TradingBotML()
    bot.run() 