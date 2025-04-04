"""
Módulo de Backtest para estratégia ADX

Este módulo implementa um backtest completo para a estratégia ADX,
calculando métricas de desempenho e gerando resultados detalhados.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import talib
import matplotlib.pyplot as plt

# Adicionar diretório raiz ao path para importações relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.binance_service import BinanceService
from src.utils.logger import Logger

class Backtest:
    """
    Classe para execução de backtests da estratégia ADX.
    """
    
    def __init__(self, dias_historico=30):
        """
        Inicializa o backtest com os parâmetros informados.
        
        Args:
            dias_historico (int): Quantidade de dias para dados históricos
        """
        self.dias_historico = dias_historico
        self.logger = Logger()
        self.binance_service = BinanceService(simulation_mode=True)
        self.resultados = {}
        self.operacoes = []
    
    def obter_dados_historicos(self, par, timeframe, limit=1000):
        """
        Obtém dados históricos da Binance.
        
        Args:
            par (str): Par de trading (ex: BTCUSDT)
            timeframe (str): Intervalo de tempo (ex: 1h, 4h, 1d)
            limit (int): Limite de candles
        
        Returns:
            DataFrame: DataFrame com dados históricos
        """
        try:
            self.logger.log_info(f"Obtendo dados históricos para {par} ({timeframe}) - {self.dias_historico} dias")
            
            # Obter klines da Binance passando os parâmetros corretos
            klines = self.binance_service.obter_dados_historicos(
                symbol=par,
                interval=timeframe,
                limit=limit
            )
            
            if not klines:
                self.logger.log_error("Falha ao obter dados históricos")
                return None
            
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
        
            self.logger.log_info(f"Obtidos {len(df)} candles")
        return df
            
        except Exception as e:
            self.logger.log_error(f"Erro ao obter dados históricos: {str(e)}")
            return None
    
    def calcular_indicadores(self, df, adx_period=14):
        """
        Calcula indicadores técnicos para a estratégia ADX.
        
        Args:
            df (DataFrame): DataFrame com dados históricos
            adx_period (int): Período para o cálculo do ADX
            
        Returns:
            DataFrame: DataFrame com indicadores calculados
        """
        try:
            # Calcular ADX, +DI e -DI
            df['di_plus'] = talib.PLUS_DI(df['high'].values, df['low'].values, df['close'].values, timeperiod=adx_period)
            df['di_minus'] = talib.MINUS_DI(df['high'].values, df['low'].values, df['close'].values, timeperiod=adx_period)
            df['adx'] = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=adx_period)
        
        # Calcular ATR
            df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            
            # Remover linhas com NaN
            df = df.dropna()
        
        return df
    
        except Exception as e:
            self.logger.log_error(f"Erro ao calcular indicadores: {str(e)}")
            return None
    
    def verificar_condicoes_compra(self, row, adx_threshold=25.0, di_threshold=20.0):
        """
        Verifica se as condições de compra foram atendidas.
        
        Args:
            row (Series): Linha do DataFrame com dados
            adx_threshold (float): Valor mínimo do ADX
            di_threshold (float): Valor mínimo para diferença entre +DI e -DI
            
        Returns:
            bool: True se condições atendidas, False caso contrário
        """
        # Verificar se ADX está acima do threshold
        if row['adx'] >= adx_threshold:
            # Verificar se +DI está acima de -DI com margem de threshold
            if row['di_plus'] > row['di_minus'] and (row['di_plus'] - row['di_minus']) >= di_threshold:
                return True
            return False
    
    def verificar_condicoes_venda(self, row, adx_threshold=25.0, di_threshold=20.0):
        """
        Verifica se as condições de venda foram atendidas.
        
        Args:
            row (Series): Linha do DataFrame com dados
            adx_threshold (float): Valor mínimo do ADX
            di_threshold (float): Valor mínimo para diferença entre -DI e +DI
            
        Returns:
            bool: True se condições atendidas, False caso contrário
        """
        # Verificar se ADX está acima do threshold
        if row['adx'] >= adx_threshold:
            # Verificar se -DI está acima de +DI com margem de threshold
            if row['di_minus'] > row['di_plus'] and (row['di_minus'] - row['di_plus']) >= di_threshold:
                return True
            return False
    
    def executar(self, par='BTCUSDT', timeframe='1h', position_size=10.0, 
                 adx_period=14, adx_threshold=25.0, di_threshold=20.0,
                 stop_multiplier_buy=2.0, gain_multiplier_buy=3.0,
                 stop_multiplier_sell=2.0, gain_multiplier_sell=3.0):
        """
        Executa o backtest com os parâmetros informados.
        
        Args:
            par (str): Par de trading
            timeframe (str): Intervalo de tempo
            position_size (float): Tamanho da posição em USDT
            adx_period (int): Período para cálculo do ADX
            adx_threshold (float): Valor mínimo do ADX
            di_threshold (float): Valor mínimo para diferença entre DIs
            stop_multiplier_buy (float): Multiplicador de ATR para stop loss na compra
            gain_multiplier_buy (float): Multiplicador de ATR para take profit na compra
            stop_multiplier_sell (float): Multiplicador de ATR para stop loss na venda
            gain_multiplier_sell (float): Multiplicador de ATR para take profit na venda
            
        Returns:
            dict: Dicionário com resultados do backtest
        """
        try:
            # Obter dados históricos
            df = self.obter_dados_historicos(par, timeframe)
            if df is None or len(df) == 0:
                return {"erro": "Falha ao obter dados históricos"}
            
            # Calcular indicadores
            df = self.calcular_indicadores(df, adx_period)
            if df is None:
                return {"erro": "Falha ao calcular indicadores"}
            
            # Resetar resultados e operações
            self.resultados = {
                "par": par,
                "timeframe": timeframe,
                "periodo_dias": self.dias_historico,
                "posicao_tamanho": position_size,
                "adx_period": adx_period,
                "adx_threshold": adx_threshold,
                "di_threshold": di_threshold,
                "data_inicio": df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S'),
                "data_fim": df['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'),
                "total_operacoes": 0,
                "operacoes_ganho": 0,
                "operacoes_perda": 0,
                "lucro_total": 0.0,
                "maior_ganho": 0.0,
                "maior_perda": 0.0,
                "taxa_acerto": 0.0,
                "relacao_lucro_prejuizo": 0.0,
                "expectativa_matematica": 0.0,
                "fator_lucro": 0.0,
                "max_drawdown": 0.0,
                "drawdown_percentual": 0.0,
                "sequencia_max_ganhos": 0,
                "sequencia_max_perdas": 0
            }
            self.operacoes = []
            
            # Variáveis para controle do backtest
        posicao_aberta = False
            posicao_tipo = None
        preco_entrada = 0.0
        stop_loss = 0.0
        take_profit = 0.0
            
            # Sequências
            ganhos_consecutivos = 0
            perdas_consecutivas = 0
            sequencia_max_ganhos = 0
            sequencia_max_perdas = 0
            
            # Drawdown
            capital = position_size
            capital_maximo = capital
            drawdown_atual = 0.0
            drawdown_maximo = 0.0
            
            # Loop pelos dados
            for i in range(1, len(df)):
                row_anterior = df.iloc[i-1]
                row = df.iloc[i]
                
                # Se não há posição aberta, verificar sinais de entrada
            if not posicao_aberta:
                    # Verificar sinal de compra
                    if self.verificar_condicoes_compra(row_anterior, adx_threshold, di_threshold):
                        posicao_aberta = True
                        posicao_tipo = "BUY"
                        preco_entrada = row['open']
                        stop_loss = preco_entrada - (row_anterior['atr'] * stop_multiplier_buy)
                        take_profit = preco_entrada + (row_anterior['atr'] * gain_multiplier_buy)
                        
                        # Registrar operação
                        self.operacoes.append({
                            "entrada_data": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            "tipo": "COMPRA",
                            "preco_entrada": preco_entrada,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "tamanho": position_size,
                            "adx": row_anterior['adx'],
                            "di_plus": row_anterior['di_plus'],
                            "di_minus": row_anterior['di_minus']
                        })
                        
                    # Verificar sinal de venda
                    elif self.verificar_condicoes_venda(row_anterior, adx_threshold, di_threshold):
                        posicao_aberta = True
                        posicao_tipo = "SELL"
                        preco_entrada = row['open']
                        stop_loss = preco_entrada + (row_anterior['atr'] * stop_multiplier_sell)
                        take_profit = preco_entrada - (row_anterior['atr'] * gain_multiplier_sell)
                        
                        # Registrar operação
                        self.operacoes.append({
                            "entrada_data": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            "tipo": "VENDA",
                            "preco_entrada": preco_entrada,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "tamanho": position_size,
                            "adx": row_anterior['adx'],
                            "di_plus": row_anterior['di_plus'],
                            "di_minus": row_anterior['di_minus']
                        })
                
                # Se há posição aberta, verificar condições de saída
                else:
                    saida = False
                    resultado = ""
                    preco_saida = 0.0
                    
                    # Verificar stop loss e take profit para compra
                    if posicao_tipo == "BUY":
                        # Stop loss atingido
                        if row['low'] <= stop_loss:
                            saida = True
                            resultado = "PERDA"
                            preco_saida = stop_loss
                        
                        # Take profit atingido
                        elif row['high'] >= take_profit:
                            saida = True
                            resultado = "GANHO"
                            preco_saida = take_profit
                    
                    # Verificar stop loss e take profit para venda
                    elif posicao_tipo == "SELL":
                        # Stop loss atingido
                        if row['high'] >= stop_loss:
                            saida = True
                            resultado = "PERDA"
                            preco_saida = stop_loss
                        
                        # Take profit atingido
                        elif row['low'] <= take_profit:
                            saida = True
                            resultado = "GANHO"
                            preco_saida = take_profit
                    
                    # Se houve saída, registrar resultado
                    if saida:
                        # Calcular lucro/prejuízo
                        if posicao_tipo == "BUY":
                            lucro_prejuizo = (preco_saida - preco_entrada) * (position_size / preco_entrada)
                        else:  # SELL
                            lucro_prejuizo = (preco_entrada - preco_saida) * (position_size / preco_entrada)
                        
                        # Atualizar capital
                        capital += lucro_prejuizo
                        
                        # Atualizar drawdown
                        if capital > capital_maximo:
                            capital_maximo = capital
                    else:
                            drawdown_atual = (capital_maximo - capital) / capital_maximo
                            if drawdown_atual > drawdown_maximo:
                                drawdown_maximo = drawdown_atual
                        
                        # Atualizar estatísticas
                        self.resultados["total_operacoes"] += 1
                        
                        if resultado == "GANHO":
                            self.resultados["operacoes_ganho"] += 1
                            self.resultados["lucro_total"] += lucro_prejuizo
                            
                            if lucro_prejuizo > self.resultados["maior_ganho"]:
                                self.resultados["maior_ganho"] = lucro_prejuizo
                            
                            ganhos_consecutivos += 1
                            perdas_consecutivas = 0
                            
                            if ganhos_consecutivos > sequencia_max_ganhos:
                                sequencia_max_ganhos = ganhos_consecutivos
                        
                        else:  # PERDA
                            self.resultados["operacoes_perda"] += 1
                            self.resultados["lucro_total"] += lucro_prejuizo
                            
                            if lucro_prejuizo < self.resultados["maior_perda"]:
                                self.resultados["maior_perda"] = lucro_prejuizo
                            
                            perdas_consecutivas += 1
                            ganhos_consecutivos = 0
                            
                            if perdas_consecutivas > sequencia_max_perdas:
                                sequencia_max_perdas = perdas_consecutivas
                        
                        # Atualizar última operação
                        ultima_op = self.operacoes[-1]
                        ultima_op.update({
                            "saida_data": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            "preco_saida": preco_saida,
                            "resultado": resultado,
                            "lucro_prejuizo": lucro_prejuizo
                        })
                        
                        # Resetar estado
                        posicao_aberta = False
                        posicao_tipo = None
            
            # Calcular métricas finais
            total_ops = self.resultados["total_operacoes"]
            if total_ops > 0:
                self.resultados["taxa_acerto"] = self.resultados["operacoes_ganho"] / total_ops
                
                # Relação lucro/prejuízo - corrigido para usar médias em vez de máximos
                if self.resultados["operacoes_perda"] > 0 and self.resultados["operacoes_ganho"] > 0:
                    ganhos = [op["lucro_prejuizo"] for op in self.operacoes if op.get("resultado") == "GANHO" and "lucro_prejuizo" in op]
                    perdas = [op["lucro_prejuizo"] for op in self.operacoes if op.get("resultado") == "PERDA" and "lucro_prejuizo" in op]
                    
                    ganho_medio = sum(ganhos) / len(ganhos) if ganhos else 0
                    perda_media = abs(sum(perdas) / len(perdas)) if perdas else 1  # Uso de abs para garantir valor positivo
                    
                    self.resultados["relacao_lucro_prejuizo"] = abs(ganho_medio / perda_media) if perda_media != 0 else 0
                
                # Expectativa matemática
                self.resultados["expectativa_matematica"] = self.resultados["taxa_acerto"] * self.resultados["relacao_lucro_prejuizo"] - (1 - self.resultados["taxa_acerto"])
                
                # Fator de lucro
                ganhos = sum(op["lucro_prejuizo"] for op in self.operacoes if op.get("resultado") == "GANHO" and "lucro_prejuizo" in op)
                perdas = abs(sum(op["lucro_prejuizo"] for op in self.operacoes if op.get("resultado") == "PERDA" and "lucro_prejuizo" in op))
                self.resultados["fator_lucro"] = ganhos / perdas if perdas > 0 else 0
            
            # Drawdown
            self.resultados["max_drawdown"] = drawdown_maximo
            self.resultados["drawdown_percentual"] = drawdown_maximo * 100
            
            # Sequências
            self.resultados["sequencia_max_ganhos"] = sequencia_max_ganhos
            self.resultados["sequencia_max_perdas"] = sequencia_max_perdas
            
            # Adicionar operações ao resultado
            self.resultados["operacoes"] = self.operacoes
            
            self.logger.log_info(f"Backtest concluído: {total_ops} operações, "
                               f"Lucro: {self.resultados['lucro_total']:.2f}, "
                               f"Taxa acerto: {self.resultados['taxa_acerto']*100:.2f}%")
            
            return self.resultados
            
        except Exception as e:
            self.logger.log_error(f"Erro ao executar backtest: {str(e)}")
            return {"erro": str(e)}
    
    def exibir_resultados(self):
        """
        Exibe os resultados do backtest no console.
        """
        if not self.resultados:
            print("Nenhum resultado de backtest disponível.")
            return
        
        print("\n" + "="*50)
        print("RESULTADOS DO BACKTEST")
        print("="*50)
        
        # Informações gerais
        print(f"Par: {self.resultados.get('par')}")
        print(f"Período: {self.resultados.get('data_inicio')} a {self.resultados.get('data_fim')}")
        print(f"Timeframe: {self.resultados.get('timeframe')}")
        print(f"Tamanho da posição: {self.resultados.get('posicao_tamanho')} USDT")
        
        print("\nRESUMO DE OPERAÇÕES:")
        print(f"Total de operações: {self.resultados.get('total_operacoes', 0)}")
        print(f"Operações com ganho: {self.resultados.get('operacoes_ganho', 0)}")
        print(f"Operações com perda: {self.resultados.get('operacoes_perda', 0)}")
        
        # Usar valores padrão para evitar erros com None
        lucro_total = self.resultados.get('lucro_total', 0) or 0
        maior_ganho = self.resultados.get('maior_ganho', 0) or 0
        maior_perda = self.resultados.get('maior_perda', 0) or 0
        
        print(f"Lucro total: {lucro_total:.2f} USDT")
        print(f"Maior ganho: {maior_ganho:.2f} USDT")
        print(f"Maior perda: {maior_perda:.2f} USDT")
        
        print("\nMÉTRICAS DE RISCO:")
        
        # Usar valores padrão para evitar erros com None
        taxa_acerto = self.resultados.get('taxa_acerto', 0) or 0
        relacao_lucro_prejuizo = self.resultados.get('relacao_lucro_prejuizo', 0) or 0
        expectativa_matematica = self.resultados.get('expectativa_matematica', 0) or 0
        fator_lucro = self.resultados.get('fator_lucro', 0) or 0
        max_drawdown = self.resultados.get('max_drawdown', 0) or 0
        drawdown_percentual = self.resultados.get('drawdown_percentual', 0) or 0
        
        print(f"Taxa de acerto: {taxa_acerto*100:.2f}%")
        print(f"Relação lucro/prejuízo: {relacao_lucro_prejuizo:.2f}")
        print(f"Expectativa matemática: {expectativa_matematica:.4f}")
        print(f"Fator de lucro: {fator_lucro:.2f}")
        print(f"Máximo drawdown: {max_drawdown:.4f}")
        print(f"Drawdown percentual: {drawdown_percentual:.2f}%")
        
        print("\nSEQUÊNCIAS:")
        print(f"Maior sequência de ganhos: {self.resultados.get('sequencia_max_ganhos', 0)}")
        print(f"Maior sequência de perdas: {self.resultados.get('sequencia_max_perdas', 0)}")
        
        print("="*50)
    
    def salvar_operacoes_json(self, nome_arquivo='operacoes_backtest.json'):
        """
        Salva as operações do backtest em um arquivo JSON.
        
        Args:
            nome_arquivo (str): Nome do arquivo para salvar as operações
            
        Returns:
            str: Caminho para o arquivo salvo
        """
        try:
            with open(nome_arquivo, 'w') as f:
                json.dump(self.operacoes, f, indent=2)
            
            self.logger.log_info(f"Operações salvas em {nome_arquivo}")
            return nome_arquivo
        except Exception as e:
            self.logger.log_error(f"Erro ao salvar operações: {str(e)}")
            return None

# Executar backtest se o script for executado diretamente
if __name__ == "__main__":
    backtest = Backtest(dias_historico=30)
    resultados = backtest.executar(
        par='BTCUSDT',
        timeframe='1h',
        position_size=10.0,
        adx_threshold=25.0,
        di_threshold=20.0
    )
    
    backtest.exibir_resultados()
    backtest.salvar_operacoes_json() 