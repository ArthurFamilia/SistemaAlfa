"""
Módulo de Otimização Bayesiana para o Bot de Trading ADX

Este módulo implementa a otimização bayesiana para encontrar os melhores
parâmetros para a estratégia de trading ADX.
"""

import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
from skopt.plots import plot_convergence, plot_objective
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

class OtimizadorBayesiano:
    """
    Implementa otimização bayesiana para encontrar os melhores parâmetros
    para a estratégia de trading ADX.
    """
    
    def __init__(self, funcao_objetivo, espaco_busca, n_calls=50, n_random_starts=10, 
                 diretorio_resultados='resultados/otimizacao'):
        """
        Inicializa o otimizador bayesiano.
        
        Args:
            funcao_objetivo: Função que recebe os parâmetros e retorna o valor a ser minimizado
            espaco_busca: Lista de parâmetros e seus limites (usando skopt.space)
            n_calls: Número total de avaliações da função objetivo
            n_random_starts: Número de avaliações aleatórias iniciais
            diretorio_resultados: Diretório para salvar resultados
        """
        self.funcao_objetivo = funcao_objetivo
        self.espaco_busca = espaco_busca
        self.n_calls = n_calls
        self.n_random_starts = n_random_starts
        self.diretorio_resultados = diretorio_resultados
        self.resultado = None
        self.melhores_parametros = None
        self.melhor_valor = None
        
        # Criar diretório para resultados se não existir
        os.makedirs(self.diretorio_resultados, exist_ok=True)
        
    def otimizar(self, verbose=True):
        """
        Executa a otimização bayesiana.
        
        Args:
            verbose: Se True, exibe informações durante a otimização
            
        Returns:
            dict: Dicionário com os melhores parâmetros
        """
        # Wrapper para a função objetivo que lida com os nomes dos parâmetros
        @use_named_args(self.espaco_busca)
        def objetivo_wrapper(**params):
            # Verifica se já terminamos o processo
            if hasattr(objetivo_wrapper, 'chamadas'):
                objetivo_wrapper.chamadas += 1
            else:
                objetivo_wrapper.chamadas = 1
                
            # Registra progresso
            if verbose and objetivo_wrapper.chamadas % 5 == 0:
                print(f"Progresso: {objetivo_wrapper.chamadas}/{self.n_calls} avaliações completas")
                
            return self.funcao_objetivo(**params)
        
        # Executa a otimização
        if verbose:
            print(f"Iniciando otimização bayesiana com {self.n_calls} avaliações...")
            print(f"Espaço de busca: {self.espaco_busca}")
        
        self.resultado = gp_minimize(
            objetivo_wrapper,
            self.espaco_busca,
            n_calls=self.n_calls,
            n_random_starts=self.n_random_starts,
            verbose=verbose,
            random_state=42
        )
        
        # Extrair melhores parâmetros
        self.melhores_parametros = {}
        
        # Obtém os nomes dos parâmetros a partir dos objetos de dimensão
        param_names = []
        for dim in self.espaco_busca:
            if hasattr(dim, 'name'):
                param_names.append(dim.name)
            else:
                # Se a dimensão não tiver nome, usar um nome genérico
                param_names.append(f"param_{len(param_names)}")
        
        # Preencher o dicionário de melhores parâmetros
        for i, param_name in enumerate(param_names):
            self.melhores_parametros[param_name] = self.resultado.x[i]
            
        self.melhor_valor = self.resultado.fun
        
        if verbose:
            print("\nOtimização concluída!")
            print(f"Melhor valor encontrado: {-self.melhor_valor}")
            print("Melhores parâmetros:")
            for param, valor in self.melhores_parametros.items():
                print(f"  {param}: {valor}")
                
        return self.melhores_parametros
    
    def salvar_resultados(self, nome_arquivo=None):
        """
        Salva os resultados da otimização em um arquivo JSON.
        
        Args:
            nome_arquivo: Nome do arquivo para salvar resultados
            
        Returns:
            str: Caminho para o arquivo salvo
        """
        if self.resultado is None:
            raise ValueError("Execute otimizar() antes de salvar resultados")
            
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"otimizacao_bayesiana_{timestamp}.json"
            
        # Preparar dados para salvar
        resultados = {
            "melhores_parametros": self.melhores_parametros,
            "melhor_valor": float(-self.melhor_valor),  # Converte para positivo (normalmente é lucro)
            "n_calls": self.n_calls,
            "n_random_starts": self.n_random_starts,
            "timestamp": datetime.now().isoformat(),
            "todas_avaliacoes": []
        }
        
        # Obter nomes dos parâmetros
        param_names = []
        for dim in self.espaco_busca:
            if hasattr(dim, 'name'):
                param_names.append(dim.name)
            else:
                param_names.append(f"param_{len(param_names)}")
        
        # Adicionar todas as avaliações
        for i, (valor, params) in enumerate(zip(self.resultado.func_vals, self.resultado.x_iters)):
            params_dict = {}
            for j, param_name in enumerate(param_names):
                params_dict[param_name] = params[j]
                
            resultados["todas_avaliacoes"].append({
                "iteracao": i,
                "parametros": params_dict,
                "valor": float(-valor)  # Converte para positivo
            })
            
        # Salvar resultados
        caminho_completo = os.path.join(self.diretorio_resultados, nome_arquivo)
        with open(caminho_completo, 'w') as f:
            json.dump(resultados, f, indent=4)
            
        print(f"Resultados salvos em {caminho_completo}")
        return caminho_completo
    
    def plotar_convergencia(self, salvar=True):
        """
        Plota o gráfico de convergência da otimização.
        
        Args:
            salvar: Se True, salva o gráfico como arquivo
            
        Returns:
            plt.Figure: Objeto de figura
        """
        if self.resultado is None:
            raise ValueError("Execute otimizar() antes de plotar")
            
        # Plotar convergência
        fig = plot_convergence(self.resultado)
        plt.title("Convergência da Otimização Bayesiana")
        plt.ylabel("Valor Objetivo (-Lucro)")
        
        if salvar:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = os.path.join(self.diretorio_resultados, f"convergencia_{timestamp}.png")
            plt.savefig(caminho, dpi=300, bbox_inches='tight')
            print(f"Gráfico de convergência salvo em {caminho}")
            
        return fig
    
    def plotar_importancia_parametros(self, salvar=True):
        """
        Plota a importância de cada parâmetro na otimização.
        
        Args:
            salvar: Se True, salva o gráfico como arquivo
            
        Returns:
            plt.Figure: Objeto de figura
        """
        if self.resultado is None:
            raise ValueError("Execute otimizar() antes de plotar")
            
        # Plotar importância dos parâmetros
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Obter nomes dos parâmetros
        param_names = []
        for dim in self.espaco_busca:
            if hasattr(dim, 'name'):
                param_names.append(dim.name)
            else:
                param_names.append(f"param_{len(param_names)}")
                
        try:
            plot_objective(self.resultado, dimensions=param_names)
            
            if salvar:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho = os.path.join(self.diretorio_resultados, f"importancia_parametros_{timestamp}.png")
                plt.savefig(caminho, dpi=300, bbox_inches='tight')
                print(f"Gráfico de importância de parâmetros salvo em {caminho}")
                
            return fig
        except Exception as e:
            print(f"Erro ao plotar importância dos parâmetros: {str(e)}")
            return None

# Função para criar o espaço de busca para a estratégia ADX
def criar_espaco_busca_adx():
    """
    Cria o espaço de busca para otimização da estratégia ADX.
    
    Returns:
        list: Lista com os parâmetros e seus limites
    """
    espaco = [
        # Parâmetros dos indicadores - nomes compatíveis com o Backtest
        Real(15.0, 35.0, name='adx_threshold'),
        Integer(6, 14, name='adx_period'),
        Real(5.0, 25.0, name='di_threshold'),
        
        # Parâmetros de stops e targets - nomes compatíveis com o Backtest
        Real(1.0, 3.0, name='stop_multiplier_buy'),
        Real(1.0, 3.0, name='stop_multiplier_sell'),
        Real(2.0, 5.0, name='gain_multiplier_buy'),
        Real(2.0, 5.0, name='gain_multiplier_sell'),
    ]
    
    return espaco 