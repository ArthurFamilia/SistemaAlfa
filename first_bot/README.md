# Bot de Trading ADX para Binance Futures

Bot de trading automatizado baseado no indicador ADX (Average Directional Index), desenvolvido para operar na Binance Futures.

## Visão Geral da Estratégia

Este bot utiliza uma estratégia baseada no ADX (Average Directional Index) para identificar oportunidades de trading no mercado de futuros da Binance:

1. **Identificação de Força de Tendência**: O ADX mede a força da tendência de mercado, independentemente da direção.
2. **Determinação de Direção**: Os indicadores direcionais (DI+ e DI-) determinam a direção da tendência.
3. **Gestão de Risco**: O ATR (Average True Range) é utilizado para calcular stops e alvos.

### Regras de Entrada

- **Compra (Long)**: Quando o ADX rompe acima do limiar configurado E o DI+ é maior que o DI-.
- **Venda (Short)**: Quando o ADX rompe acima do limiar configurado E o DI- é maior que o DI+.

### Gestão de Risco

- Stop Loss e Take Profit são calculados com base no ATR
- Os multiplicadores podem ser configurados separadamente para operações de compra e venda
- O bot utiliza alavancagem configurável e margem isolada por padrão no mercado de futuros

## Instalação

### Requisitos

- Python 3.7 ou superior
- Pacotes Python (listados em `requirements.txt`)
- Conta na Binance Futures com permissões de API habilitadas
- TA-Lib (instalação separada necessária)

### Passos de Instalação

1. Clone o repositório:
   ```
   git clone [URL_DO_REPOSITORIO]
   cd trading-bot-adx
   ```

2. Instale as dependências Python:
   ```
   pip install -r requirements.txt
   ```

3. Instale o TA-Lib:
   - Windows: Baixe o arquivo .whl apropriado em https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   - Linux: `sudo apt-get install ta-lib`
   - Mac: `brew install ta-lib`

4. Configure suas credenciais da API Binance:
   - Crie um arquivo `.env` na pasta raiz do projeto (você pode copiar de `.env.example`)
   - Adicione suas chaves da API:
     ```
     API_KEY=sua_api_key
     API_SECRET=sua_api_secret
     SIMULATION_MODE=TRUE
     ```

## Configuração

### Configurações Principais

No arquivo `.env`:

```
# Credenciais da API
API_KEY=sua_api_key
API_SECRET=sua_api_secret

# Modo de operação
SIMULATION_MODE=TRUE

# Configurações do mercado
TRADING_PAIR=ETHUSDT
CANDLE_INTERVAL=5m
KLINE_LIMIT=100
POSITION_SIZE=500.0

# Configurações de alavancagem
FUTURES_LEVERAGE=5
FUTURES_MARGIN_TYPE=ISOLATED
```

### Configurações dos Indicadores

No arquivo `src/config/config.py`:

- `ADX_PERIOD`: Período para cálculo do ADX (padrão: 10)
- `ADX_THRESHOLD`: Limiar do ADX para considerar uma tendência válida (padrão: 30.0)
- `ADX_PREVIOUS_CANDLES`: Número de candles anteriores que devem ter ADX < threshold
- `DI_PLUS_PERIOD` e `DI_MINUS_PERIOD`: Períodos para cálculo dos indicadores direcionais
- `ATR_PERIOD`: Período para cálculo do ATR para stops/gains

## Uso

### Iniciando o Bot

```
python iniciar_bot.py
```

O script oferece um menu interativo com as seguintes opções:

1. Iniciar Bot de Trading
2. Executar Backtest
3. Minerar Estratégias
4. Testar cálculo de ATR
5. Sair

### Modo de Simulação

Por padrão, o bot opera no ambiente de teste (testnet) da Binance Futures. Mantenha `SIMULATION_MODE=TRUE` no arquivo `.env` para usar o modo de simulação.

### Modo Real

Para operar com dinheiro real:
1. Altere `SIMULATION_MODE=FALSE` no arquivo `.env`
2. Verifique se suas credenciais da API têm permissões para trading
3. Configure os parâmetros de risco adequadamente

**ATENÇÃO**: O trading no mercado de futuros com alavancagem envolve alto risco!

## Funcionalidades

### Bot de Trading
- Monitoramento em tempo real do mercado
- Execução automática de ordens baseada na estratégia ADX
- Gestão de risco com stops e alvos dinâmicos
- Logs detalhados de operações e erros

### Backtest
- Análise de desempenho histórico da estratégia
- Geração de gráficos de análise
- Métricas de risco e retorno
- Exportação de resultados em JSON

### Minerador de Estratégias
- Otimização de parâmetros da estratégia
- Teste de diferentes configurações
- Identificação de melhores parâmetros
- Exportação de resultados

## Estrutura do Projeto

```
├── src/
│   ├── bot.py                 # Ponto de entrada principal
│   ├── config/
│   │   └── config.py          # Configurações e parâmetros
│   ├── services/
│   │   ├── adx_strategy.py    # Implementação da estratégia ADX
│   │   └── binance_service.py # Serviço para interagir com a Binance
│   └── utils/
│       └── logger.py          # Utilitário de logging
├── check_dependencies.py      # Verificador de dependências
├── iniciar_bot.py            # Script de inicialização
├── backtest.py               # Script de backtest
├── strategy_miner.py         # Minerador de estratégias
├── simple_atr_test.py        # Teste do cálculo de ATR
├── requirements.txt          # Dependências Python
└── README.md                 # Este arquivo
```

## Avisos Importantes

- **Risco Financeiro**: Trading com alavancagem envolve risco significativo de perda de capital
- **Teste Exaustivamente**: Use sempre o modo de simulação antes de operar com dinheiro real
- **Gerenciamento de Risco**: Nunca arrisque mais do que você pode perder confortavelmente
- **Responsabilidade Total do Usuário**: 
  - O usuário é 100% responsável por todas as decisões de trading
  - O usuário é responsável por configurar e verificar todos os parâmetros de risco
  - O usuário é responsável por testar e validar o funcionamento do sistema
  - O autor, Arthur de Souza Age, não possui NENHUMA responsabilidade sobre:
    - Resultados das operações
    - Perdas financeiras
    - Funcionamento do sistema
    - Decisões de trading
    - Configurações utilizadas
  - Ao utilizar este sistema, o usuário assume TODA a responsabilidade e risco

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 