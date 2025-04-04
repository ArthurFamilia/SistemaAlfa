"""
Módulo de Machine Learning para o Bot de Trading ADX.

Este módulo contém implementações de algoritmos de machine learning 
para otimização de parâmetros, classificação de regimes de mercado e 
filtragem de sinais de trading.
"""

from src.ml.otimizacao_bayesiana import OtimizadorBayesiano, criar_espaco_busca_adx
from src.ml.classificador_regimes import ClassificadorRegimeMercado
from src.ml.filtro_sinais import FiltroSinaisXGBoost 