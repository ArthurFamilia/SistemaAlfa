"""
Utilitários gerais usados em todo o projeto.

Este arquivo contém funções auxiliares utilizadas em diversos módulos.
"""

import pandas as pd
import numpy as np
import talib
import os
import logging
from datetime import datetime

def calcular_indicadores_df(df):
    """
    Calcula os indicadores técnicos em um DataFrame.
    
    Args:
        df (pandas.DataFrame): DataFrame com dados de mercado
        
    Returns:
        pandas.DataFrame: DataFrame com indicadores calculados
    """
    try:
        # Verificar se o df é válido
        if df is None or df.empty:
            logging.error("DataFrame vazio fornecido para cálculo de indicadores")
            return df
        
        # Cria uma cópia do DataFrame para não modificar o original
        result_df = df.copy()
        
        # Converte para minúsculas por padrão se não estiverem
        colunas_originais = list(result_df.columns)
        colunas_lower = [col.lower() for col in colunas_originais]
        mapeamento_colunas = {colunas_originais[i]: colunas_lower[i] for i in range(len(colunas_originais))}
        result_df.rename(columns=mapeamento_colunas, inplace=True)
        
        # Padroniza nomes para usar no TA-Lib
        if 'open' in result_df.columns:
            result_df.rename(columns={
                'open': 'Open', 
                'high': 'High', 
                'low': 'Low', 
                'close': 'Close', 
                'volume': 'Volume' if 'volume' in result_df.columns else 'volume'
            }, inplace=True)
        
        # Verifica se as colunas necessárias estão presentes
        required_columns = ['Open', 'High', 'Low', 'Close']
        if not all(col in result_df.columns for col in required_columns):
            logging.error(f"DataFrame não contém as colunas necessárias: {required_columns}")
            return df
        
        # Calcula indicadores usando TA-Lib
        # ADX (Average Directional Index)
        result_df['adx'] = talib.ADX(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=14)
        
        # DI+ e DI- (Directional Indicators)
        result_df['di_plus'] = talib.PLUS_DI(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=14)
        result_df['di_minus'] = talib.MINUS_DI(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=14)
        
        # ATR (Average True Range)
        result_df['atr'] = talib.ATR(result_df['High'].values, result_df['Low'].values, result_df['Close'].values, timeperiod=14)
        
        # Médias Móveis
        result_df['ma_curta'] = talib.SMA(result_df['Close'].values, timeperiod=8)
        result_df['ma_longa'] = talib.SMA(result_df['Close'].values, timeperiod=21)
        
        # Remove linhas com NaN
        result_df.dropna(inplace=True)
        
        return result_df
        
    except Exception as e:
        logging.error(f"Erro ao calcular indicadores: {str(e)}")
        return df

def formatar_valor_monetario(valor, precisao=2, simbolo_moeda='$'):
    """
    Formata um valor como moeda.
    
    Args:
        valor (float): Valor a ser formatado
        precisao (int): Número de casas decimais
        simbolo_moeda (str): Símbolo da moeda
    
    Returns:
        str: Valor formatado
    """
    if valor is None:
        return f"{simbolo_moeda}0.00"
    
    return f"{simbolo_moeda}{abs(valor):.{precisao}f}"

def calcular_retorno_percentual(valor_inicial, valor_final):
    """
    Calcula o retorno percentual entre dois valores.
    
    Args:
        valor_inicial (float): Valor inicial
        valor_final (float): Valor final
    
    Returns:
        float: Retorno percentual
    """
    if valor_inicial is None or valor_final is None or valor_inicial == 0:
        return 0.0
    
    return ((valor_final / valor_inicial) - 1) * 100 