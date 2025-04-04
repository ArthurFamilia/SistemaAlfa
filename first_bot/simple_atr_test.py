"""
Script para testar o cálculo do ATR (Average True Range).

Este script obtém dados históricos da Binance e calcula o ATR para verificar
os níveis de stop loss e take profit que seriam utilizados.
"""

import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv
import os
from src.config.config import (
    SYMBOL, KLINE_INTERVAL, ATR_PERIOD,
    STOP_MULTIPLIER_BUY, STOP_MULTIPLIER_SELL,
    GAIN_MULTIPLIER_BUY, GAIN_MULTIPLIER_SELL
)

def obter_dados_historicos(dias=7):
    """
    Obtém dados históricos da Binance.
    
    Args:
        dias (int): Número de dias de dados históricos
        
    Returns:
        DataFrame: DataFrame com os dados históricos
    """
    print(f"\nObtendo dados históricos para {SYMBOL} dos últimos {dias} dias...")
    
    # Calcular timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(days=dias)
    
    # Inicializar cliente Binance
    client = Client()
    
    # Obter klines
    klines = client.get_historical_klines(
        SYMBOL,
        KLINE_INTERVAL,
        start_time.strftime("%d %b %Y %H:%M:%S"),
        end_time.strftime("%d %b %Y %H:%M:%S")
    )
    
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
    
    print(f"Obtidos {len(df)} candles com sucesso")
    return df

def calcular_atr(df):
    """
    Calcula o ATR e os níveis de stop loss e take profit.
    
    Args:
        df (DataFrame): DataFrame com dados históricos
        
    Returns:
        DataFrame: DataFrame com ATR e níveis calculados
    """
    # Calcular ATR
    df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=ATR_PERIOD)
    
    # Calcular níveis para compra
    df['stop_loss_buy'] = df['close'] - (STOP_MULTIPLIER_BUY * df['atr'])
    df['take_profit_buy'] = df['close'] + (GAIN_MULTIPLIER_BUY * df['atr'])
    
    # Calcular níveis para venda
    df['stop_loss_sell'] = df['close'] + (STOP_MULTIPLIER_SELL * df['atr'])
    df['take_profit_sell'] = df['close'] - (GAIN_MULTIPLIER_SELL * df['atr'])
    
    return df

def exibir_resultados(df):
    """
    Exibe os resultados do cálculo do ATR.
    
    Args:
        df (DataFrame): DataFrame com ATR e níveis calculados
    """
    print("\n" + "="*50)
    print("RESULTADOS DO CÁLCULO ATR")
    print("="*50)
    
    # Obter última linha (mais recente)
    ultima_linha = df.iloc[-1]
    
    print(f"\nÚltimo preço: {ultima_linha['close']:.2f}")
    print(f"ATR: {ultima_linha['atr']:.2f}")
    
    print("\nNíveis para COMPRA:")
    print(f"Stop Loss: {ultima_linha['stop_loss_buy']:.2f} ({STOP_MULTIPLIER_BUY} * ATR)")
    print(f"Take Profit: {ultima_linha['take_profit_buy']:.2f} ({GAIN_MULTIPLIER_BUY} * ATR)")
    
    print("\nNíveis para VENDA:")
    print(f"Stop Loss: {ultima_linha['stop_loss_sell']:.2f} ({STOP_MULTIPLIER_SELL} * ATR)")
    print(f"Take Profit: {ultima_linha['take_profit_sell']:.2f} ({GAIN_MULTIPLIER_SELL} * ATR)")
    
    # Calcular e exibir estatísticas do ATR
    print("\nEstatísticas do ATR:")
    print(f"Mínimo: {df['atr'].min():.2f}")
    print(f"Máximo: {df['atr'].max():.2f}")
    print(f"Média: {df['atr'].mean():.2f}")
    print(f"Desvio Padrão: {df['atr'].std():.2f}")
    
    # Exibir últimos 5 valores
    print("\nÚltimos 5 valores de ATR:")
    for i in range(-5, 0):
        print(f"{df['timestamp'].iloc[i]}: {df['atr'].iloc[i]:.2f}")

def test_atr_for_stops():
    """Função principal para testar o cálculo do ATR."""
    try:
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Obter dados históricos
        df = obter_dados_historicos(dias=7)
        
        # Calcular ATR e níveis
        df = calcular_atr(df)
        
        # Exibir resultados
        exibir_resultados(df)
        
    except Exception as e:
        print(f"\nErro ao executar teste do ATR: {str(e)}")

if __name__ == "__main__":
    test_atr_for_stops() 