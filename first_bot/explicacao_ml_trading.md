# Métodos de Machine Learning para Trading Implementados

Este documento explica os métodos de Machine Learning implementados no sistema de trading atual, sua funcionalidade e como eles se integram ao bot.

## 1. Otimização Bayesiana para Parâmetros de Trading

### Implementação: `src/ml/otimizacao_bayesiana.py`

A otimização bayesiana é particularmente eficiente para otimizar parâmetros da estratégia ADX, economizando tempo computacional em comparação com buscas por força bruta.

**Principais funcionalidades:**
- Busca automatizada dos melhores parâmetros para a estratégia ADX
- Balanceamento entre exploração de novos pontos e refinamento de áreas promissoras
- Visualização da convergência e importância dos parâmetros
- Persistência dos resultados para uso futuro

**Parâmetros otimizados:**
- `ADX_THRESHOLD`: Limiar para considerar a força da tendência
- `ADX_PERIOD`: Período do indicador ADX
- `DI_PLUS_PERIOD` e `DI_MINUS_PERIOD`: Períodos dos indicadores DI
- `ATR_PERIOD`: Período do ATR para cálculo de volatilidade
- Multiplicadores de stop loss e take profit

**Como funciona:**
1. Define um espaço de busca para os parâmetros
2. Constrói um modelo probabilístico da função objetivo (resultados do backtest)
3. Usa uma função de aquisição para decidir quais pontos explorar a seguir
4. Atualiza o modelo após cada avaliação
5. Converge para os parâmetros ótimos com menos avaliações que métodos tradicionais

**Integração com o sistema:**
- Os parâmetros otimizados são salvos em `modelos/otimizador/params_otimizados.json`
- O bot carrega estes parâmetros automaticamente durante a inicialização
- A otimização pode ser executada periodicamente para adaptar a estratégia a mudanças no mercado

## 2. Classificador de Regimes de Mercado

### Implementação: `src/ml/classificador_regimes.py`

O classificador de regimes identifica diferentes condições de mercado e permite que o bot adapte seus parâmetros a cada tipo de mercado.

**Tipos de regimes identificados:**
- Mercado Lateral (consolidação)
- Tendência de Alta
- Tendência de Baixa
- Alta Volatilidade

**Features utilizadas para classificação:**
- Tendência: ADX médio, diferença entre DI+ e DI-
- Volatilidade: ATR relativo, desvio padrão de retornos
- Momentum: Rate of Change (ROC) de diferentes períodos
- Volume: Volume relativo à média, tendência de volume
- Médias Móveis: Cruzamentos e diferenças percentuais

**Como funciona:**
1. Extrai features dos dados de mercado
2. Utiliza Random Forest para classificar o regime atual
3. Associa parâmetros ótimos a cada regime de mercado
4. Permite que o bot ajuste sua estratégia em tempo real

**Integração com o sistema:**
- O modelo treinado é salvo em `modelos/classificador_regime/classificador_regime.joblib`
- O bot consulta o classificador antes de cada operação
- Os parâmetros da estratégia são ajustados de acordo com o regime detectado

## 3. Filtro de Sinais com XGBoost

### Implementação: `src/ml/filtro_sinais.py`

O filtro de sinais avalia a qualidade dos sinais de trading gerados pela estratégia ADX, reduzindo operações com baixa probabilidade de sucesso.

**Features para avaliação de sinais:**
- Valores atuais de ADX, DI+ e DI-
- Volatilidade (ATR relativo)
- Tendência e Momentum (diferenças de médias móveis)
- Volume relativo
- Padrões de preço recentes
- Consistência da tendência

**Como funciona:**
1. Para cada sinal gerado pela estratégia ADX, extrai features relevantes
2. Utiliza XGBoost para prever a probabilidade de sucesso do sinal
3. Filtra sinais com baixa probabilidade de sucesso
4. Melhora a taxa de acerto do bot, reduzindo falsos positivos

**Integração com o sistema:**
- O modelo treinado é salvo em `modelos/filtro_sinais/filtro_sinais.joblib`
- O bot consulta o filtro antes de executar operações
- Sinais com probabilidade abaixo do limiar configurado são ignorados

## Como Utilizar os Recursos de ML no Sistema

### 1. Treinamento dos Modelos

O sistema permite treinar os modelos de ML utilizando dados históricos:

```python
# Exemplo de treinamento do filtro de sinais
from src.ml.filtro_sinais import FiltroSinaisXGBoost

# Carregar dados históricos e operações passadas
dados_historicos = carregar_dados_historicos()
operacoes_passadas = carregar_operacoes()

# Inicializar e treinar o filtro
filtro = FiltroSinaisXGBoost()
X, y = filtro.preparar_dataset(dados_historicos, operacoes_passadas)
filtro.treinar(X, y, otimizar_hiperparametros=True)
filtro.salvar_modelo()
```

### 2. Otimização de Parâmetros

A otimização bayesiana pode ser executada para encontrar os melhores parâmetros:

```python
from src.ml.otimizacao_bayesiana import OtimizadorBayesiano, criar_espaco_busca_adx

# Definir função objetivo (executa backtests)
def funcao_objetivo(**params):
    resultado_backtest = executar_backtest(**params)
    return -resultado_backtest['lucro_total']  # Negativo porque queremos maximizar

# Criar otimizador
espaco_busca = criar_espaco_busca_adx()
otimizador = OtimizadorBayesiano(funcao_objetivo, espaco_busca, n_calls=50)

# Executar otimização
melhores_params = otimizador.otimizar()
otimizador.salvar_resultados()
```

### 3. Uso no Bot de Trading

O sistema integra os modelos de ML diretamente no fluxo de trading:

```python
# No módulo de verificação de condições de trading
def verificar_condicoes_compra(self):
    # Verificação tradicional baseada em ADX
    if self.adx > self.ADX_THRESHOLD and self.di_plus > self.di_minus:
        # Identificar regime de mercado atual
        regime = self.classificador_regime.identificar_regime(self.dados_recentes)
        
        # Ajustar parâmetros para o regime atual
        parametros_otimos = self.classificador_regime.obter_parametros_otimos(regime)
        self.ajustar_parametros(parametros_otimos)
        
        # Extrair features para o filtro de sinais
        features = self.filtro_sinais.extrair_features(self.dados_recentes)
        
        # Verificar qualidade do sinal
        if self.filtro_sinais.sinal_eh_qualidade(features):
            return True
    
    return False
```

## Próximos Passos para ML no Bot de Trading

1. **Implementar aprendizado contínuo:** Atualizar os modelos automaticamente com novos dados
2. **Adicionar novos classificadores:** Expandir para detectar padrões específicos de mercado
3. **Desenvolver análise de sentimento:** Incorporar dados de notícias e redes sociais
4. **Implementar previsão de preços:** Utilizar modelos de série temporal para prever movimentos futuros
5. **Criar sistema de ensemble:** Combinar múltiplos modelos para decisões mais robustas
