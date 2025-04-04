"""
Estratégia de Trading baseada no indicador ADX (Average Directional Index)

Regras da estratégia:
1. Um sinal de trading é gerado quando:
   - Os 4 candles anteriores têm ADX < 20
   - O ADX atual cruza acima de 20
2. A direção da operação é determinada pelos indicadores direcionais:
   - Se DI+ > DI-, é gerado um sinal de COMPRA
   - Se DI- > DI+, é gerado um sinal de VENDA
3. O ATR (Average True Range) é utilizado como base para calcular os níveis de:
   - Stop Loss (usando STOP_MULTIPLIER_BUY e STOP_MULTIPLIER_SELL)
   - Take Profit (usando GAIN_MULTIPLIER_BUY e GAIN_MULTIPLIER_SELL)

O indicador ADX mede a força da tendência, independentemente da direção.
Os indicadores direcionais (DI+ e DI-) determinam a direção da tendência.
"""

import pandas as pd
import numpy as np
import talib
from datetime import datetime
from binance.enums import *
from src.config.config import (
    ADX_THRESHOLD, ADX_PERIOD, ATR_PERIOD,
    STOP_MULTIPLIER_BUY, GAIN_MULTIPLIER_BUY,
    STOP_MULTIPLIER_SELL, GAIN_MULTIPLIER_SELL,
    DI_PLUS_PERIOD, DI_MINUS_PERIOD,
    DI_PLUS_THRESHOLD, DI_MINUS_THRESHOLD,
    POSITION_SIZE, ADX_PREVIOUS_CANDLES
)
from src.utils.logger import Logger

class ADXStrategy:
    """
    Implementação da estratégia de trading baseada no ADX para o mercado de futuros.
    
    Esta classe é responsável por calcular indicadores técnicos (ADX, DI+, DI-),
    verificar condições de entrada e gerenciar sinais de trading.
    """
    
    def __init__(self, binance_service):
        """
        Inicializa a estratégia ADX.
        
        Args:
            binance_service: Instância do serviço de conexão com a Binance
        """
        self.binance_service = binance_service
        self.logger = Logger()
        self.previous_adx = None
        self.previous_di_plus = None
        self.previous_di_minus = None
        self.last_adx_values = []  # Lista para armazenar os últimos valores do ADX
    
    def check_adx_trigger(self, current_adx):
        """
        Verifica se o ADX atual satisfaz as condições de gatilho:
        - Os candles anteriores devem ter ADX < 20
        - O ADX atual deve ser > 20
        
        Args:
            current_adx (float): Valor atual do ADX
            
        Returns:
            bool: True se as condições do gatilho são satisfeitas
        """
        # Precisamos de pelo menos o número configurado de valores anteriores
        if len(self.last_adx_values) < ADX_PREVIOUS_CANDLES:
            return False
            
        # Verifica se os últimos valores estão abaixo do threshold
        last_values_below = all(adx < ADX_THRESHOLD for adx in self.last_adx_values[-ADX_PREVIOUS_CANDLES:])
        
        # Verifica se o valor atual está acima do threshold
        current_above = current_adx >= ADX_THRESHOLD
        
        # Log para debug
        self.logger.log_info(
            f"Verificando gatilho ADX: últimos {ADX_PREVIOUS_CANDLES} valores={self.last_adx_values[-ADX_PREVIOUS_CANDLES:]}, "
            f"atual={current_adx:.2f}, threshold={ADX_THRESHOLD}"
        )
        
        return last_values_below and current_above
    
    def calculate_indicators(self):
        """
        Calcula os indicadores ADX, DI+, DI- e ATR usando dados de kline do mercado de futuros.
        
        Returns:
            tuple: (ADX atual, DI+ atual, DI- atual, ATR usado no ADX, ATR para stops)
        """
        try:
            # Obter dados de klines do mercado de futuros
            df = self.binance_service.get_klines()
            
            if df is None or df.empty:
                self.logger.log_error("Não foi possível obter dados de klines para calcular indicadores")
                return None, None, None, None, None
            
            # Preparar nomes de colunas para uso no TA-Lib (maiúsculas para padronização)
            df.rename(columns={
                'open': 'Open', 
                'high': 'High', 
                'low': 'Low', 
                'close': 'Close', 
                'volume': 'Volume'
            }, inplace=True)
            
            # Calcular os indicadores usando TA-Lib
            # Plus Directional Indicator
            df['di_plus'] = talib.PLUS_DI(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=DI_PLUS_PERIOD)
            
            # Minus Directional Indicator
            df['di_minus'] = talib.MINUS_DI(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=DI_MINUS_PERIOD)
            
            # Average Directional Index
            df['adx'] = talib.ADX(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=ADX_PERIOD)
            
            # Average True Range para stops e targets
            df['atr'] = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=ATR_PERIOD)
            
            # ATR usado nos cálculos do ADX (para referência)
            df['atr_adx'] = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=ADX_PERIOD)
            
            # Obter os valores mais recentes
            if len(df) > 0:
                # Armazenar os últimos 5 valores do ADX (4 anteriores + atual)
                adx_values = df['adx'].tail(5).tolist()
                if len(adx_values) >= 5:
                    self.last_adx_values = adx_values[:-1]  # Armazena os 4 valores anteriores
                
                last_row = df.iloc[-1]
                current_adx = last_row['adx']
                current_di_plus = last_row['di_plus']
                current_di_minus = last_row['di_minus']
                current_atr_adx = last_row['atr_adx']
                current_atr = last_row['atr']
                
                # Log detalhado dos indicadores
                self.logger.log_info(
                    f"Indicadores calculados: ADX={current_adx:.2f}, "
                    f"DI+={current_di_plus:.2f}, DI-={current_di_minus:.2f}, "
                    f"ATR={current_atr:.2f}"
                )
                
                # Verificar se os valores são válidos
                if np.isnan(current_adx) or np.isnan(current_di_plus) or np.isnan(current_di_minus) or np.isnan(current_atr):
                    self.logger.log_error("Valores de indicadores inválidos (NaN)")
                    return None, None, None, None, None
                
                # Atualizar valores anteriores
                self.previous_adx = current_adx
                self.previous_di_plus = current_di_plus
                self.previous_di_minus = current_di_minus
                
                return current_adx, current_di_plus, current_di_minus, current_atr_adx, current_atr
            else:
                self.logger.log_error("Dataframe vazio após cálculo de indicadores")
                return None, None, None, None, None
                
        except Exception as e:
            self.logger.log_error(f"Erro ao calcular indicadores: {str(e)}")
            return None, None, None, None, None

    def calculate_indicators_df(self, df):
        """
        Calcula os indicadores ADX, DI+, DI- e ATR em um DataFrame fornecido.
        
        Args:
            df (pd.DataFrame): DataFrame com dados de klines (deve conter colunas: open, high, low, close, volume)
        
        Returns:
            pd.DataFrame: DataFrame com indicadores calculados adicionados
        """
        try:
            if df is None or df.empty:
                self.logger.log_error("DataFrame vazio fornecido para cálculo de indicadores")
                return df
            
            # Criar cópia do DataFrame para não modificar o original
            result_df = df.copy()
            
            # Padronizar nomes das colunas para o cálculo
            # Verifica se já estão em minúsculas ou maiúsculas
            has_lower = all(col in result_df.columns for col in ['open', 'high', 'low', 'close'])
            has_upper = all(col in result_df.columns for col in ['Open', 'High', 'Low', 'Close'])
            
            if has_lower:
                # Renomear para maiúsculas para uso no TA-Lib
                result_df.rename(columns={
                    'open': 'Open', 
                    'high': 'High', 
                    'low': 'Low', 
                    'close': 'Close', 
                    'volume': 'Volume' if 'volume' in result_df.columns else 'volume'
                }, inplace=True)
            elif not has_upper:
                self.logger.log_error("DataFrame não contém as colunas necessárias para cálculo de indicadores")
                return df
            
            # Calcular os indicadores usando TA-Lib
            # Plus Directional Indicator
            result_df['di_plus'] = talib.PLUS_DI(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=DI_PLUS_PERIOD)
            
            # Minus Directional Indicator
            result_df['di_minus'] = talib.MINUS_DI(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=DI_MINUS_PERIOD)
            
            # Average Directional Index
            result_df['adx'] = talib.ADX(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=ADX_PERIOD)
            
            # Average True Range para stops e targets
            result_df['atr'] = talib.ATR(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=ATR_PERIOD)
            
            # ATR usado nos cálculos do ADX (para referência)
            result_df['atr_adx'] = talib.ATR(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=ADX_PERIOD)
            
            # Renomear de volta para minúsculas para consistência
            if has_lower:
                result_df.rename(columns={
                    'Open': 'open', 
                    'High': 'high', 
                    'Low': 'low', 
                    'Close': 'close', 
                    'Volume': 'volume'
                }, inplace=True)
            
            return result_df
            
        except Exception as e:
            self.logger.log_error(f"Erro ao calcular indicadores no DataFrame: {str(e)}")
            return df

    def check_buy_conditions(self, adx, di_plus, di_minus, ask_price, atr):
        """
        Verifica se as condições para uma operação de compra estão satisfeitas.
        
        Args:
            adx (float): Valor atual do ADX
            di_plus (float): Valor atual do DI+
            di_minus (float): Valor atual do DI-
            ask_price (float): Preço de compra atual (ask)
            atr (float): Valor do ATR para cálculo de stop e alvo
            
        Returns:
            bool: True se as condições de compra estão satisfeitas, False caso contrário
        """
        # Log detalhado das condições para depuração
        self.logger.log_info(
            f"Verificando condições de COMPRA: ADX={adx:.2f} (threshold: {ADX_THRESHOLD}), "
            f"DI+={di_plus:.2f}, DI-={di_minus:.2f}"
        )

        # Verificações de segurança para valores inválidos
        if any(np.isnan(x) for x in [adx, di_plus, di_minus]) or atr <= 0:
            self.logger.log_error("Valores inválidos. Não é possível verificar condições de compra.")
            return False
            
        # Verificar se o ask_price é válido
        if ask_price is None or ask_price <= 0:
            self.logger.log_error(f"Preço de compra (ask) inválido: {ask_price}")
            return False

        # Verificar o novo gatilho do ADX
        adx_trigger = self.check_adx_trigger(adx)
                      
        # Verificar se DI+ é maior que DI- (confirmação de tendência de alta)
        trend_confirmation = di_plus > di_minus
        
        # Todas as condições devem ser atendidas
        buy_condition = adx_trigger and trend_confirmation
        
        # Log do resultado
        if buy_condition:
            self.logger.log_info("Condições de COMPRA satisfeitas!")
            
            # Calcular níveis de stop loss e take profit
            stop_loss = ask_price - (STOP_MULTIPLIER_BUY * atr)
            take_profit = ask_price + (GAIN_MULTIPLIER_BUY * atr)
            
            # Verificar se os valores de stop loss e take profit são válidos
            if stop_loss <= 0:
                self.logger.log_error(f"Stop loss calculado é inválido: {stop_loss}. Ajustando para 1% abaixo do preço de entrada.")
                stop_loss = ask_price * 0.99  # Fallback: 1% abaixo do preço de entrada
                
            if take_profit <= ask_price:
                self.logger.log_error(f"Take profit calculado é inválido: {take_profit}. Ajustando para 1% acima do preço de entrada.")
                take_profit = ask_price * 1.01  # Fallback: 1% acima do preço de entrada
            
            # Calcular relação risco/recompensa
            risk = ask_price - stop_loss
            reward = take_profit - ask_price
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Verificar se a relação risco/recompensa é aceitável (pelo menos 1:1)
            if risk_reward_ratio < 1.0:
                self.logger.log_warning(f"Relação risco/recompensa insuficiente: {risk_reward_ratio:.2f}. Operação cancelada.")
                return False
            
            # Registrar a operação no log
            self.logger.log_operation({
                "timestamp": datetime.now().isoformat(),
                "action": "BUY_SIGNAL",
                "adx": adx,
                "di_plus": di_plus,
                "di_minus": di_minus,
                "entry_price": ask_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "atr": atr,
                "risk_reward_ratio": risk_reward_ratio,
                "last_adx_values": self.last_adx_values
            })
            
            # Verificar posições existentes e executar a ordem
            try:
                # Criar ordem e ordens de proteção
                result = self.binance_service.create_order(
                    action="BUY",
                    entry_price=ask_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=POSITION_SIZE
                )
                return result
            except Exception as e:
                self.logger.log_error(f"Erro ao executar ordem de compra: {str(e)}")
                return False
        else:
            # Log das razões pelas quais as condições não foram satisfeitas
            if not adx_trigger:
                self.logger.log_info(f"Gatilho ADX não satisfeito: últimos {ADX_PREVIOUS_CANDLES} valores={self.last_adx_values[-ADX_PREVIOUS_CANDLES:]}, atual={adx:.2f}")
            if not trend_confirmation:
                self.logger.log_info(f"DI+ ({di_plus:.2f}) não é maior que DI- ({di_minus:.2f})")
            return False

    def check_sell_conditions(self, adx, di_plus, di_minus, bid_price, atr):
        """
        Verifica se as condições para uma operação de venda estão satisfeitas.
        
        Args:
            adx (float): Valor atual do ADX
            di_plus (float): Valor atual do DI+
            di_minus (float): Valor atual do DI-
            bid_price (float): Preço de venda atual (bid)
            atr (float): Valor do ATR para cálculo de stop e alvo
            
        Returns:
            bool: True se as condições de venda estão satisfeitas, False caso contrário
        """
        # Log detalhado das condições para depuração
        self.logger.log_info(
            f"Verificando condições de VENDA: ADX={adx:.2f} (threshold: {ADX_THRESHOLD}), "
            f"DI+={di_plus:.2f}, DI-={di_minus:.2f}"
        )

        # Verificações de segurança para valores inválidos
        if any(np.isnan(x) for x in [adx, di_plus, di_minus]) or atr <= 0:
            self.logger.log_error("Valores inválidos. Não é possível verificar condições de venda.")
            return False
            
        # Verificar se o bid_price é válido
        if bid_price is None or bid_price <= 0:
            self.logger.log_error(f"Preço de venda (bid) inválido: {bid_price}")
            return False

        # Verificar o novo gatilho do ADX
        adx_trigger = self.check_adx_trigger(adx)
                      
        # Verificar se DI- é maior que DI+ (confirmação de tendência de baixa)
        trend_confirmation = di_minus > di_plus
        
        # Todas as condições devem ser atendidas
        sell_condition = adx_trigger and trend_confirmation
        
        # Log do resultado
        if sell_condition:
            self.logger.log_info("Condições de VENDA satisfeitas!")
            
            # Calcular níveis de stop loss e take profit
            stop_loss = bid_price + (STOP_MULTIPLIER_SELL * atr)
            take_profit = bid_price - (GAIN_MULTIPLIER_SELL * atr)
            
            # Verificar se os valores de stop loss e take profit são válidos
            if take_profit <= 0:
                self.logger.log_error(f"Take profit calculado é inválido: {take_profit}. Ajustando para 1% abaixo do preço de entrada.")
                take_profit = bid_price * 0.99  # Fallback: 1% abaixo do preço de entrada
                
            if stop_loss <= bid_price:
                self.logger.log_error(f"Stop loss calculado é inválido: {stop_loss}. Ajustando para 1% acima do preço de entrada.")
                stop_loss = bid_price * 1.01  # Fallback: 1% acima do preço de entrada
            
            # Calcular relação risco/recompensa
            risk = stop_loss - bid_price
            reward = bid_price - take_profit
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Verificar se a relação risco/recompensa é aceitável (pelo menos 1:1)
            if risk_reward_ratio < 1.0:
                self.logger.log_warning(f"Relação risco/recompensa insuficiente: {risk_reward_ratio:.2f}. Operação cancelada.")
                return False
            
            # Registrar a operação no log
            self.logger.log_operation({
                "timestamp": datetime.now().isoformat(),
                "action": "SELL_SIGNAL",
                "adx": adx,
                "di_plus": di_plus,
                "di_minus": di_minus,
                "entry_price": bid_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "atr": atr,
                "risk_reward_ratio": risk_reward_ratio,
                "last_adx_values": self.last_adx_values
            })
            
            # Verificar posições existentes e executar a ordem
            try:
                # Criar ordem e ordens de proteção
                result = self.binance_service.create_order(
                    action="SELL",
                    entry_price=bid_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=POSITION_SIZE
                )
                return result
            except Exception as e:
                self.logger.log_error(f"Erro ao executar ordem de venda: {str(e)}")
                return False
        else:
            # Log das razões pelas quais as condições não foram satisfeitas
            if not adx_trigger:
                self.logger.log_info(f"Gatilho ADX não satisfeito: últimos {ADX_PREVIOUS_CANDLES} valores={self.last_adx_values[-ADX_PREVIOUS_CANDLES:]}, atual={adx:.2f}")
            if not trend_confirmation:
                self.logger.log_info(f"DI- ({di_minus:.2f}) não é maior que DI+ ({di_plus:.2f})")
            return False 