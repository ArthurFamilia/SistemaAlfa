"""
Módulo para Classificação de Regimes de Mercado

Este módulo implementa um classificador de regimes de mercado usando
Random Forest para identificar diferentes tipos de mercado e selecionar
os parâmetros mais adequados para cada regime.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
from datetime import datetime
import logging

class ClassificadorRegimeMercado:
    """
    Classificador de regimes de mercado usando Random Forest.
    """
    
    def __init__(self, n_estimators=100, max_depth=10, random_state=42,
                 diretorio_modelos='modelos/regimes'):
        """
        Inicializa o classificador de regimes de mercado.
        
        Args:
            n_estimators: Número de árvores na floresta
            max_depth: Profundidade máxima das árvores
            random_state: Seed para reprodutibilidade
            diretorio_modelos: Diretório para salvar modelos
        """
        self.modelo = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )
        self.scaler = StandardScaler()
        self.diretorio_modelos = diretorio_modelos
        self.feature_names = []
        
        # Criar diretório para modelos se não existir
        os.makedirs(self.diretorio_modelos, exist_ok=True)
        
        # Configurações adicionais
        self.regimes = {
            0: "Mercado Lateral",
            1: "Tendência de Alta",
            2: "Tendência de Baixa", 
            3: "Alta Volatilidade"
        }
        
        # Mapeamento de parâmetros ótimos por regime
        self.parametros_por_regime = {}
        
    def extrair_features(self, df):
        """
        Extrai features para classificação de regime de mercado.
        
        Args:
            df: DataFrame com dados de mercado (deve conter colunas de preço, volume e indicadores)
            
        Returns:
            np.array: Array com features extraídas
        """
        # Verificar colunas necessárias
        colunas_necessarias = ['open', 'high', 'low', 'close', 'volume', 'adx', 'di_plus', 'di_minus', 'atr']
        for col in colunas_necessarias:
            if col not in df.columns:
                raise ValueError(f"DataFrame deve conter a coluna {col}")
        
        # Calcular médias móveis se não existirem
        if 'ma_curta' not in df.columns:
            df['ma_curta'] = df['close'].rolling(8).mean()
        if 'ma_longa' not in df.columns:
            df['ma_longa'] = df['close'].rolling(21).mean()
        
        # Lista para armazenar todas as features
        features = []
        
        # 1. Tendência (baseada em ADX e DI)
        adx_medio = df['adx'].rolling(14).mean()
        di_diff = df['di_plus'] - df['di_minus']
        di_diff_norm = di_diff / df['adx'].clip(lower=1)  # Normalizado pela força da tendência
        
        # 2. Volatilidade (ATR relativo e outros indicadores)
        atr_relativo = df['atr'] / df['close'] * 100  # ATR como % do preço
        volatilidade_5d = df['close'].pct_change().rolling(5).std() * 100  # Desvio padrão de 5 dias
        range_relativo = (df['high'] - df['low']) / df['close'] * 100  # Range diário em %
        
        # 3. Momentum
        roc_5 = df['close'].pct_change(5) * 100  # Rate of Change de 5 períodos
        roc_14 = df['close'].pct_change(14) * 100
        
        # 4. Volume
        volume_rel = df['volume'] / df['volume'].rolling(20).mean()
        volume_trend = df['volume'].rolling(5).mean() / df['volume'].rolling(20).mean()
        
        # 5. Média móvel
        ma_cross = (df['ma_curta'] > df['ma_longa']).astype(int)
        ma_diff = (df['ma_curta'] - df['ma_longa']) / df['close'] * 100  # Diferença em %
        
        # Remover NaN
        len_df = len(df)
        start_idx = 21  # Índice onde todas as features estarão disponíveis (max lookback)
        
        # Criar matriz de features
        X = np.column_stack([
            adx_medio.values[start_idx:],
            di_diff.values[start_idx:],
            di_diff_norm.values[start_idx:],
            atr_relativo.values[start_idx:],
            volatilidade_5d.values[start_idx:],
            range_relativo.values[start_idx:],
            roc_5.values[start_idx:],
            roc_14.values[start_idx:],
            volume_rel.values[start_idx:],
            volume_trend.values[start_idx:],
            ma_cross.values[start_idx:],
            ma_diff.values[start_idx:]
        ])
        
        # Armazenar nomes das features
        self.feature_names = [
            'ADX_Médio',
            'DI_Diff',
            'DI_Diff_Norm',
            'ATR_Relativo',
            'Volatilidade_5d',
            'Range_Relativo',
            'ROC_5',
            'ROC_14',
            'Volume_Rel',
            'Volume_Trend',
            'MA_Cross',
            'MA_Diff'
        ]
        
        return X
        
    def gerar_labels(self, df, start_idx=21):
        """
        Gera labels para regimes de mercado baseado em heurísticas.
        
        Args:
            df: DataFrame com dados de mercado
            start_idx: Índice inicial para começar a atribuir labels
            
        Returns:
            np.array: Array com labels gerados
        """
        # Inicializar array de labels
        labels = np.zeros(len(df) - start_idx, dtype=int)
        
        # Obter dados relevantes
        adx = df['adx'].values[start_idx:]
        di_plus = df['di_plus'].values[start_idx:]
        di_minus = df['di_minus'].values[start_idx:]
        atr_rel = df['atr'].values[start_idx:] / df['close'].values[start_idx:] * 100
        
        # Definir limiares
        ADX_THRESHOLD_TREND = 25  # Limiar para considerar tendência
        ATR_REL_THRESHOLD = 2.0   # Limiar para volatilidade alta (2% do preço)
        
        # Atribuir labels
        for i in range(len(labels)):
            # Verificar tendência (ADX)
            if adx[i] >= ADX_THRESHOLD_TREND:
                # Verificar direção da tendência (DI+ vs DI-)
                if di_plus[i] > di_minus[i]:
                    labels[i] = 1  # Tendência de alta
                else:
                    labels[i] = 2  # Tendência de baixa
            else:
                # Sem tendência forte, verificar volatilidade
                if atr_rel[i] >= ATR_REL_THRESHOLD:
                    labels[i] = 3  # Alta volatilidade
                else:
                    labels[i] = 0  # Mercado lateral/consolidação
        
        return labels
        
    def treinar(self, df, labels=None, test_size=0.2, verboso=True):
        """
        Treina o classificador de regimes de mercado.
        
        Args:
            df: DataFrame com dados de mercado
            labels: Array de labels se disponível, ou None para gerar automaticamente
            test_size: Proporção para conjunto de teste
            verboso: Se True, exibe métricas de desempenho
            
        Returns:
            float: Acurácia do modelo no conjunto de teste
        """
        # Extrair features
        X = self.extrair_features(df)
        
        # Gerar ou usar labels fornecidos
        if labels is None:
            start_idx = len(df) - len(X)  # Índice onde as features começam
            y = self.gerar_labels(df, start_idx)
        else:
            # Verificar se o tamanho corresponde
            if len(labels) != len(X):
                raise ValueError(f"Tamanho de labels ({len(labels)}) não corresponde ao tamanho de features ({len(X)})")
            y = np.array(labels)
        
        # Dividir em conjunto de treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False, random_state=42
        )
        
        # Normalizar features
        X_train_norm = self.scaler.fit_transform(X_train)
        X_test_norm = self.scaler.transform(X_test)
        
        # Treinar modelo
        self.modelo.fit(X_train_norm, y_train)
        
        # Avaliar modelo
        y_pred = self.modelo.predict(X_test_norm)
        accuracy = self.modelo.score(X_test_norm, y_test)
        
        if verboso:
            print(f"\nAcurácia do classificador de regimes: {accuracy:.4f}")
            print("\nRelatório de classificação:")
            print(classification_report(y_test, y_pred, target_names=[self.regimes[i] for i in range(len(self.regimes))]))
            
            print("\nMatriz de confusão:")
            cm = confusion_matrix(y_test, y_pred)
            print(cm)
            
            # Analisar importância das features
            self._mostrar_importancia_features()
        
        return accuracy
        
    def _mostrar_importancia_features(self):
        """Exibe a importância das features usadas pelo modelo."""
        importances = self.modelo.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\nImportância das Features:")
        for i, idx in enumerate(indices):
            if i < len(self.feature_names):
                print(f"{self.feature_names[idx]}: {importances[idx]:.4f}")
            
        # Plotar importância
        plt.figure(figsize=(12, 6))
        plt.title('Importância das Features para Classificação de Regimes')
        plt.bar(range(len(indices)), importances[indices], align='center')
        plt.xticks(range(len(indices)), [self.feature_names[i] for i in indices], rotation=90)
        plt.tight_layout()
        plt.show()
        
    def identificar_regime(self, dados_recentes):
        """
        Identifica o regime atual do mercado.
        
        Args:
            dados_recentes: DataFrame com dados recentes do mercado
            
        Returns:
            tuple: (regime, probabilidades) - O regime identificado e as probabilidades para cada classe
        """
        # Extrair features
        try:
            X = self.extrair_features(dados_recentes)
            
            # Usar apenas o último ponto (estado atual do mercado)
            X_atual = X[-1:].reshape(1, -1)
            
            # Normalizar
            X_atual_norm = self.scaler.transform(X_atual)
            
            # Prever regime
            regime = self.modelo.predict(X_atual_norm)[0]
            probabilidades = self.modelo.predict_proba(X_atual_norm)[0]
            
            # Log do resultado
            regime_nome = self.regimes.get(regime, f"Desconhecido ({regime})")
            logging.info(f"Regime de mercado identificado: {regime_nome}")
            logging.info(f"Probabilidades: {[f'{self.regimes[i]}: {p:.2f}' for i, p in enumerate(probabilidades)]}")
            
            return regime, probabilidades
        
        except Exception as e:
            logging.error(f"Erro ao identificar regime de mercado: {str(e)}")
            # Fallback para regime neutro (lateral)
            return 0, np.array([1.0, 0.0, 0.0, 0.0])
            
    def configurar_parametros_por_regime(self, parametros_por_regime):
        """
        Configura os parâmetros ótimos para cada regime de mercado.
        
        Args:
            parametros_por_regime (dict): Dicionário com os parâmetros para cada regime
        """
        self.parametros_por_regime = parametros_por_regime
        return self
    
    def obter_parametros_otimos(self, regime):
        """
        Retorna os parâmetros ótimos para o regime especificado.
        
        Args:
            regime (int): ID do regime de mercado (0-3)
            
        Returns:
            dict: Parâmetros ótimos para o regime
        """
        if not hasattr(self, 'parametros_por_regime') or self.parametros_por_regime is None:
            return {}
            
        return self.parametros_por_regime.get(regime, {})
        
    def salvar_modelo(self, caminho_modelo=None):
        """
        Salva o modelo em um arquivo.
        
        Args:
            caminho_modelo: Caminho para o arquivo do modelo (sem extensão)
            
        Returns:
            str: Caminho para o arquivo salvo
        """
        if caminho_modelo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_modelo = f"classificador_regimes_{timestamp}"
            
        # Salvar modelo
        caminho_modelo = os.path.join(self.diretorio_modelos, f"{caminho_modelo}.joblib")
        modelo_data = {
            'modelo': self.modelo,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'parametros_por_regime': self.parametros_por_regime,
            'regimes': self.regimes
        }
        
        joblib.dump(modelo_data, caminho_modelo)
        print(f"Modelo salvo em {caminho_modelo}")
        return caminho_modelo
        
    def carregar_modelo(self, caminho_arquivo):
        """
        Carrega o modelo treinado e o scaler de um arquivo.
        
        Args:
            caminho_arquivo: Caminho para o arquivo do modelo
            
        Returns:
            bool: True se o carregamento foi bem-sucedido
        """
        try:
            modelo_data = joblib.load(caminho_arquivo)
            
            self.modelo = modelo_data['modelo']
            self.scaler = modelo_data['scaler']
            self.feature_names = modelo_data['feature_names']
            self.parametros_por_regime = modelo_data.get('parametros_por_regime', {})
            self.regimes = modelo_data.get('regimes', self.regimes)
            
            print(f"Modelo carregado de {caminho_arquivo}")
            return True
            
        except Exception as e:
            print(f"Erro ao carregar modelo: {str(e)}")
            return False 