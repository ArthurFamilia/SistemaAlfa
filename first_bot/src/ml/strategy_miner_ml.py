"""
Minerador de estratégias avançado usando otimização bayesiana.

Este módulo implementa uma versão avançada do minerador de estratégias
que utiliza otimização bayesiana para encontrar os melhores parâmetros
para a estratégia de trading ADX.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime
from src.ml.otimizacao_bayesiana import OtimizadorBayesiano, criar_espaco_busca_adx
import json
import matplotlib.pyplot as plt
from src.utils.logger import Logger

class MineradorEstrategiasML:
    """
    Minerador de estratégias usando otimização bayesiana.
    """
    
    def __init__(self, backtest_fn, dados_historicos=None, dias_historico=30, 
                 n_calls=50, diretorio_resultados='resultados/estrategias'):
        """
        Inicializa o minerador de estratégias.
        
        Args:
            backtest_fn: Função que executa o backtest com os parâmetros fornecidos
            dados_historicos: DataFrame com dados históricos (opcional)
            dias_historico: Número de dias para dados históricos (se dados_historicos=None)
            n_calls: Número de avaliações na otimização bayesiana
            diretorio_resultados: Diretório para salvar resultados
        """
        self.backtest_fn = backtest_fn
        self.dados_historicos = dados_historicos
        self.dias_historico = dias_historico
        self.n_calls = n_calls
        self.diretorio_resultados = diretorio_resultados
        self.resultados = None
        self.melhores_parametros = None
        self.logger = Logger()
        
        # Criar diretório para resultados se não existir
        os.makedirs(self.diretorio_resultados, exist_ok=True)
    
    def funcao_objetivo(self, **params):
        """
        Função objetivo para otimização bayesiana.
        
        Args:
            **params: Parâmetros para executar o backtest
            
        Returns:
            float: Valor negativo da métrica a ser maximizada
        """
        try:
            # Executar backtest com os parâmetros fornecidos
            resultado = self.backtest_fn(**params)
            
            # Extrair métrica de desempenho
            # Aqui usamos expectativa matemática, mas poderia ser lucro total,
            # sharpe ratio, etc, dependendo do que o backtest retorna
            
            # Verificar se resultado é dicionário
            if not isinstance(resultado, dict):
                self.logger.log_error(f"Backtest retornou tipo inválido: {type(resultado)}")
                return 0.0
            
            # Verificar se tem 'expectativa_matematica'
            if 'expectativa_matematica' in resultado:
                expectativa = resultado['expectativa_matematica']
            elif 'lucro_total' in resultado and 'total_operacoes' in resultado and resultado['total_operacoes'] > 0:
                # Calcular uma estimativa de expectativa
                expectativa = resultado['lucro_total'] / resultado['total_operacoes']
            else:
                # Fallback para lucro total
                expectativa = resultado.get('lucro_total', 0.0)
            
            # Se tiver drawdown, penalizar expectativa
            if 'max_drawdown' in resultado and resultado['max_drawdown'] > 0:
                # Penalizar mais fortemente drawdowns maiores
                penalidade_drawdown = resultado['max_drawdown'] / 1000  # Ajustar escala conforme necessário
                expectativa = expectativa * (1 - penalidade_drawdown)
            
            # Retornar negativo para minimização (otimizador minimiza)
            return -expectativa
            
        except Exception as e:
            self.logger.log_error(f"Erro na função objetivo: {str(e)}")
            return 0.0  # Valor neutro em caso de erro
    
    def minerar(self, espaco_busca=None, verbose=True):
        """
        Executa a mineração de estratégias.
        
        Args:
            espaco_busca: Lista de parâmetros e seus limites (usando skopt.space)
            verbose: Se True, exibe informações durante a otimização
            
        Returns:
            dict: Dicionário com os melhores parâmetros
        """
        # Se espaço de busca não fornecido, usar o padrão
        if espaco_busca is None:
            espaco_busca = criar_espaco_busca_adx()
            
        # Criar otimizador bayesiano
        otimizador = OtimizadorBayesiano(
            self.funcao_objetivo,
            espaco_busca,
            n_calls=self.n_calls,
            diretorio_resultados=self.diretorio_resultados
        )
        
        # Iniciar mineração
        self.logger.log_info(f"Iniciando mineração de estratégias com otimização bayesiana...")
        self.logger.log_info(f"Número de avaliações: {self.n_calls}")
        
        # Executar otimização
        self.melhores_parametros = otimizador.otimizar(verbose=verbose)
        
        # Salvar resultado
        caminho_resultado = otimizador.salvar_resultados()
        
        # Plotar convergência
        if verbose:
            try:
                otimizador.plotar_convergencia()
                otimizador.plotar_importancia_parametros()
            except Exception as e:
                self.logger.log_error(f"Erro ao plotar resultados: {str(e)}")
        
        # Armazenar resultado completo
        self.resultados = otimizador.resultado
        
        # Exibir melhores parâmetros
        self._exibir_melhores_resultados()
        
        return self.melhores_parametros
    
    def _exibir_melhores_resultados(self):
        """Exibe os melhores resultados encontrados."""
        if self.melhores_parametros is None:
            self.logger.log_error("Nenhum resultado disponível. Execute minerar() primeiro.")
            return
            
        print("\n" + "="*50)
        print("MELHORES PARÂMETROS ENCONTRADOS")
        print("="*50)
        
        # Formatar e exibir cada parâmetro
        for param, valor in self.melhores_parametros.items():
            if isinstance(valor, float):
                print(f"{param}: {valor:.4f}")
            else:
                print(f"{param}: {valor}")
        
        # Exibir valor da função objetivo
        melhor_valor = -self.resultados.fun if self.resultados else None
        if melhor_valor is not None:
            print(f"\nMelhor expectativa matemática: {melhor_valor:.4f}")
        
        print("="*50)
    
    def executar_backtest_melhor(self):
        """
        Executa um backtest com os melhores parâmetros encontrados.
        
        Returns:
            dict: Resultado do backtest
        """
        if self.melhores_parametros is None:
            self.logger.log_error("Nenhum resultado disponível. Execute minerar() primeiro.")
            return None
            
        try:
            # Executar backtest com os melhores parâmetros
            self.logger.log_info("Executando backtest com os melhores parâmetros...")
            resultado = self.backtest_fn(**self.melhores_parametros)
            
            # Exibir resultado detalhado
            print("\n" + "="*50)
            print("RESULTADO DO BACKTEST COM MELHORES PARÂMETROS")
            print("="*50)
            
            # Exibir métricas principais
            for metrica, valor in resultado.items():
                if isinstance(valor, float):
                    print(f"{metrica}: {valor:.4f}")
                else:
                    print(f"{metrica}: {valor}")
            
            print("="*50)
            
            return resultado
            
        except Exception as e:
            self.logger.log_error(f"Erro ao executar backtest: {str(e)}")
            return None
    
    def salvar_parametros(self, nome_arquivo=None):
        """
        Salva os melhores parâmetros em um arquivo JSON.
        
        Args:
            nome_arquivo: Nome do arquivo para salvar (opcional)
            
        Returns:
            str: Caminho para o arquivo salvo
        """
        if self.melhores_parametros is None:
            self.logger.log_error("Nenhum resultado disponível. Execute minerar() primeiro.")
            return None
            
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"melhores_parametros_{timestamp}.json"
            
        # Preparar dados para salvar
        data = {
            'melhores_parametros': self.melhores_parametros,
            'timestamp': datetime.now().isoformat(),
            'n_calls': self.n_calls
        }
        
        # Salvar arquivo
        caminho_completo = os.path.join(self.diretorio_resultados, nome_arquivo)
        with open(caminho_completo, 'w') as f:
            json.dump(data, f, indent=4)
            
        self.logger.log_info(f"Parâmetros salvos em {caminho_completo}")
        return caminho_completo 