"""
Módulo de Filtro de Sinais para o Bot de Trading ADX

Este módulo implementa um filtro de sinais baseado em XGBoost para
prever a probabilidade de sucesso de um sinal de trading gerado
pela estratégia ADX.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import matplotlib.pyplot as plt
import joblib
import os
import json
from datetime import datetime
import logging

class FiltroSinaisXGBoost:
    """
    Filtro de sinais usando XGBoost para prever a qualidade/sucesso
    de sinais de trading gerados pela estratégia ADX.
    """
    
    def __init__(self, diretorio_modelos='modelos/filtro_sinais', limiar_qualidade=0.6):
        """
        Inicializa o filtro de sinais.
        
        Args:
            diretorio_modelos: Diretório para salvar modelos
            limiar_qualidade: Limiar de probabilidade para considerar um sinal como de qualidade
        """
        self.modelo = None
        self.scaler = StandardScaler()
        self.diretorio_modelos = diretorio_modelos
        self.limiar_qualidade = limiar_qualidade
        self.feature_names = []
        
        # Criar diretório para modelos se não existir
        os.makedirs(self.diretorio_modelos, exist_ok=True)
    
    def extrair_features(self, df, timestamp_entrada=None, idx=None):
        """
        Extrai features para prever a qualidade de um sinal.
        
        Args:
            df: DataFrame com dados de mercado
            timestamp_entrada: Timestamp do sinal de entrada (opcional)
            idx: Índice no DataFrame para extrair as features (opcional)
            
        Returns:
            np.array: Array com features extraídas
        """
        if timestamp_entrada is not None:
            # Encontrar índice do timestamp
            idx = df[df['timestamp'] == timestamp_entrada].index
            if len(idx) == 0:
                raise ValueError(f"Timestamp {timestamp_entrada} não encontrado no DataFrame")
            idx = idx[0]
        
        if idx is None:
            raise ValueError("Deve fornecer timestamp_entrada ou idx")
            
        # Verificar disponibilidade de dados
        if idx < 20:  # Precisamos de pelo menos 20 períodos anteriores
            raise ValueError(f"Índice {idx} muito baixo. Necessário pelo menos 20 períodos anteriores.")
            
        # 1. Indicadores ADX e DI no momento da entrada
        adx = df['adx'].iloc[idx]
        di_plus = df['di_plus'].iloc[idx]
        di_minus = df['di_minus'].iloc[idx]
        di_diff = di_plus - di_minus
        
        # 2. Volatilidade (ATR e outros)
        atr = df['atr'].iloc[idx]
        atr_relativo = atr / df['close'].iloc[idx] * 100  # ATR como % do preço
        
        # 3. Tendência e Momentum
        # Média móvel de 8 e 21 períodos
        ma8 = df['close'].rolling(8).mean().iloc[idx]
        ma21 = df['close'].rolling(21).mean().iloc[idx]
        ma_diff = (ma8 - ma21) / df['close'].iloc[idx] * 100  # Diferença como % do preço
        
        # Força da tendência (inclinação da média móvel)
        ma8_slope = (ma8 - df['close'].rolling(8).mean().iloc[idx-5]) / 5
        ma8_slope_rel = ma8_slope / df['close'].iloc[idx] * 100  # Inclinação como % do preço
        
        # 4. Volume e liquidez
        volume = df['volume'].iloc[idx]
        volume_rel = volume / df['volume'].rolling(20).mean().iloc[idx]
        
        # 5. Padrões de preço (velas, HH/HL, etc.)
        # Range das últimas 5 velas
        last_5_high = df['high'].iloc[idx-5:idx+1].max()
        last_5_low = df['low'].iloc[idx-5:idx+1].min()
        price_range = (last_5_high - last_5_low) / df['close'].iloc[idx] * 100  # Range como % do preço
        
        # 6. Posição relativa do preço
        # % do range de 14 dias
        high_14d = df['high'].rolling(14).max().iloc[idx]
        low_14d = df['low'].rolling(14).min().iloc[idx]
        price_position = (df['close'].iloc[idx] - low_14d) / (high_14d - low_14d) if high_14d > low_14d else 0.5
        
        # 7. Features avançadas (derivadas dos indicadores)
        # Consistência da tendência (quantos dos últimos 5 períodos tiveram ADX crescente)
        adx_increasing = sum(1 for i in range(idx-4, idx+1) if df['adx'].iloc[i] > df['adx'].iloc[i-1]) / 5
        
        # Combinação do ADX com a direção do preço
        price_direction = 1 if df['close'].iloc[idx] > df['close'].iloc[idx-1] else -1
        adx_price_agreement = 1 if (price_direction > 0 and di_plus > di_minus) or (price_direction < 0 and di_minus > di_plus) else 0
        
        # Criar array de features
        features = np.array([
            adx, 
            di_plus, 
            di_minus, 
            di_diff,
            atr_relativo,
            ma_diff,
            ma8_slope_rel,
            volume_rel,
            price_range,
            price_position,
            adx_increasing,
            adx_price_agreement
        ])
        
        # Armazenar nomes das features
        self.feature_names = [
            'ADX',
            'DI+',
            'DI-',
            'DI_Diff',
            'ATR_Relativo',
            'MA_Diff',
            'MA8_Slope',
            'Volume_Rel',
            'Price_Range',
            'Price_Position',
            'ADX_Increasing',
            'ADX_Price_Agreement'
        ]
        
        return features
    
    def preparar_dataset(self, df, operacoes):
        """
        Prepara o dataset de treinamento a partir dos dados históricos e operações realizadas.
        
        Args:
            df: DataFrame com dados históricos de mercado
            operacoes: Lista de dicionários com operações realizadas (deve conter 'timestamp_entrada' e 'resultado')
            
        Returns:
            tuple: (X, y) - Features e labels para treinamento
        """
        X = []
        y = []
        
        # Criar um DataFrame indexado por timestamp para facilitar a busca
        df_indexed = df.set_index('timestamp') if 'timestamp' in df.columns else df
        
        for op in operacoes:
            try:
                # Extrair timestamp e resultado
                timestamp = op.get('timestamp_entrada')
                resultado = op.get('resultado', 0)
                
                # Se a operação não tem timestamp ou resultado, pular
                if timestamp is None or resultado is None:
                    continue
                
                # Encontrar índice no DataFrame original
                if timestamp in df_indexed.index:
                    idx = df.index[df['timestamp'] == timestamp][0]
                else:
                    # Tentar encontrar o timestamp mais próximo
                    closest_idx = df['timestamp'].sub(timestamp).abs().idxmin()
                    idx = closest_idx
                
                # Extrair features
                features = self.extrair_features(df, idx=idx)
                
                # Adicionar ao dataset
                X.append(features)
                
                # Label: 1 se operação foi lucrativa, 0 caso contrário
                y.append(1 if resultado > 0 else 0)
                
            except Exception as e:
                logging.warning(f"Erro ao processar operação: {str(e)}")
                continue
                
        return np.array(X), np.array(y)
    
    def treinar(self, X, y, otimizar_hiperparametros=False, test_size=0.2, verboso=True):
        """
        Treina o modelo XGBoost para classificação de qualidade de sinais.
        
        Args:
            X: Features para treinamento
            y: Labels (1 para sinais lucrativos, 0 para não lucrativos)
            otimizar_hiperparametros: Se True, realiza busca em grade para otimizar hiperparâmetros
            test_size: Proporção do conjunto de teste
            verboso: Se True, exibe métricas de desempenho
            
        Returns:
            float: AUC-ROC no conjunto de teste
        """
        # Dividir em conjunto de treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Normalizar features
        X_train_norm = self.scaler.fit_transform(X_train)
        X_test_norm = self.scaler.transform(X_test)
        
        if otimizar_hiperparametros:
            # Definir grade de hiperparâmetros
            param_grid = {
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2],
                'n_estimators': [50, 100, 200],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }
            
            # Criar modelo base
            xgb_model = xgb.XGBClassifier(
                objective='binary:logistic',
                random_state=42
            )
            
            # Realizar busca em grade
            grid_search = GridSearchCV(
                estimator=xgb_model,
                param_grid=param_grid,
                cv=5,
                scoring='roc_auc',
                verbose=1 if verboso else 0
            )
            
            # Treinar com busca em grade
            grid_search.fit(X_train_norm, y_train)
            
            # Obter melhores parâmetros
            best_params = grid_search.best_params_
            if verboso:
                print(f"Melhores parâmetros: {best_params}")
                
            # Criar modelo com melhores parâmetros
            self.modelo = xgb.XGBClassifier(
                objective='binary:logistic',
                random_state=42,
                **best_params
            )
        else:
            # Usar modelo com parâmetros padrão
            self.modelo = xgb.XGBClassifier(
                max_depth=5,
                learning_rate=0.1,
                n_estimators=100,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='binary:logistic',
                random_state=42
            )
            
        # Treinar modelo
        self.modelo.fit(X_train_norm, y_train)
        
        # Avaliar modelo
        y_pred_proba = self.modelo.predict_proba(X_test_norm)[:, 1]
        y_pred = (y_pred_proba >= self.limiar_qualidade).astype(int)
        
        # Calcular métricas
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        auc_roc = roc_auc_score(y_test, y_pred_proba)
        
        if verboso:
            print("\nMétricas de Desempenho:")
            print(f"Acurácia: {accuracy:.4f}")
            print(f"Precisão: {precision:.4f}")
            print(f"Recall: {recall:.4f}")
            print(f"AUC-ROC: {auc_roc:.4f}")
            
            # Plotar importância das features
            self._plotar_importancia_features()
            
        return auc_roc
    
    def prever_qualidade_sinal(self, features):
        """
        Prevê a probabilidade de um sinal ser lucrativo.
        
        Args:
            features: Array de features extraídas para o sinal
            
        Returns:
            float: Probabilidade de sucesso do sinal (0 a 1)
        """
        if self.modelo is None:
            logging.error("Modelo não treinado. Treine o modelo antes de fazer previsões.")
            return 0.5  # Valor neutro
            
        try:
            # Normalizar features
            features_norm = self.scaler.transform(features.reshape(1, -1))
            
            # Obter probabilidade
            prob = self.modelo.predict_proba(features_norm)[0, 1]
            
            return prob
            
        except Exception as e:
            logging.error(f"Erro ao prever qualidade do sinal: {str(e)}")
            return 0.5  # Valor neutro em caso de erro
    
    def sinal_eh_qualidade(self, features):
        """
        Verifica se um sinal é considerado de qualidade (probabilidade acima do limiar).
        
        Args:
            features: Array de features extraídas para o sinal
            
        Returns:
            bool: True se o sinal é considerado de qualidade
        """
        prob = self.prever_qualidade_sinal(features)
        return prob >= self.limiar_qualidade
    
    def _plotar_importancia_features(self):
        """Plota a importância das features do modelo."""
        if self.modelo is None:
            return
            
        # Obter importância
        importance = self.modelo.feature_importances_
        
        # Criar DataFrame
        if len(self.feature_names) != len(importance):
            self.feature_names = [f"Feature_{i}" for i in range(len(importance))]
            
        feature_importance = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': importance
        }).sort_values('Importance', ascending=False)
        
        # Plotar
        plt.figure(figsize=(10, 6))
        plt.bar(feature_importance['Feature'], feature_importance['Importance'])
        plt.xticks(rotation=90)
        plt.title('Importância das Features para Qualidade dos Sinais')
        plt.tight_layout()
        plt.show()
        
        # Imprimir também no console
        print("\nImportância das Features:")
        for _, row in feature_importance.iterrows():
            print(f"{row['Feature']}: {row['Importance']:.4f}")
    
    def _exibir_importancia_features(self):
        """Exibe a importância das features usadas pelo modelo."""
        if hasattr(self, 'modelo') and self.modelo is not None:
            importances = self.modelo.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            print("\nImportância das Features para Filtro de Sinais:")
            for i, idx in enumerate(indices):
                if i < len(self.feature_names):
                    print(f"{self.feature_names[idx]}: {importances[idx]:.4f}")
    
    def carregar_modelo(self, caminho_modelo):
        """
        Carrega o modelo a partir de um arquivo.
        
        Args:
            caminho_modelo (str): Caminho para o arquivo do modelo
            
        Returns:
            self: Instância do filtro com o modelo carregado
        """
        try:
            import joblib
            
            if not os.path.exists(caminho_modelo):
                raise FileNotFoundError(f"Arquivo de modelo não encontrado: {caminho_modelo}")
                
            # Carregar modelo
            modelo_data = joblib.load(caminho_modelo)
            
            # Verificar se é um dicionário com modelo e scaler
            if isinstance(modelo_data, dict):
                self.modelo = modelo_data.get('modelo')
                self.scaler = modelo_data.get('scaler')
                self.feature_names = modelo_data.get('feature_names', self.feature_names)
                self.limiar_qualidade = modelo_data.get('limiar_qualidade', self.limiar_qualidade)
            else:
                # Caso seja apenas o modelo
                self.modelo = modelo_data
                
            logging.info(f"Modelo de filtro de sinais carregado com sucesso de {caminho_modelo}")
            return self
            
        except Exception as e:
            logging.error(f"Erro ao carregar modelo de filtro: {str(e)}")
            raise
    
    def salvar_modelo(self, caminho_modelo=None):
        """
        Salva o modelo em um arquivo.
        
        Args:
            caminho_modelo (str): Caminho para o arquivo do modelo
            
        Returns:
            str: Caminho para o arquivo salvo
        """
        if self.modelo is None:
            raise ValueError("Modelo não treinado. Execute treinar() antes de salvar.")
            
        try:
            import joblib
            
            if caminho_modelo is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho_modelo = os.path.join(self.diretorio_modelos, f"filtro_sinais_{timestamp}.joblib")
            
            # Salvar modelo e scaler
            modelo_data = {
                'modelo': self.modelo,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'limiar_qualidade': self.limiar_qualidade
            }
            
            joblib.dump(modelo_data, caminho_modelo)
            logging.info(f"Modelo de filtro de sinais salvo em {caminho_modelo}")
            
            return caminho_modelo
            
        except Exception as e:
            logging.error(f"Erro ao salvar modelo de filtro: {str(e)}")
            raise 