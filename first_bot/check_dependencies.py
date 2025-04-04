#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verificador de dependências para o bot de trading.

Este módulo verifica as dependências necessárias para executar o bot.
Inclui verificação de dependências básicas e de ML.
"""

def verificar_dependencias():
    """
    Verifica as dependências básicas necessárias para o bot.
    
    Returns:
        bool: True se todas as dependências estão instaladas, False caso contrário
    """
    import importlib
    
    # Lista de dependências essenciais
    dependencias = [
        'pandas',
        'numpy',
        'dotenv',
        'binance',
        'talib',
        'requests',
        'websocket',
        'json',
        'datetime',
        'time',
        'os',
        'sys',
        'logging'
    ]
    
    # Verificar cada dependência
    todas_ok = True
    print("\nVerificando dependências básicas:")
    
    for dependencia in dependencias:
        try:
            # Verifica se o módulo pode ser importado
            importlib.import_module(dependencia)
            print(f"✅ {dependencia}")
        except ImportError:
            print(f"❌ {dependencia} - NÃO ENCONTRADO")
            todas_ok = False
    
    return todas_ok

def verificar_dependencias_ml():
    """
    Verifica as dependências de ML necessárias para o bot avançado.
    
    Returns:
        bool: True se todas as dependências de ML estão instaladas, False caso contrário
    """
    import importlib
    
    # Lista de dependências de ML
    dependencias_ml = [
        'sklearn',       # scikit-learn
        'xgboost',       # XGBoost
        'skopt',         # scikit-optimize
        'matplotlib',    # Visualizações
        'joblib',        # Salvar/carregar modelos
        'talib',         # Indicadores técnicos
        'psutil'         # Monitoramento de recursos
    ]
    
    # Dependências opcionais (não impedem o uso do bot)
    dependencias_opcionais = [
        'plotly',        # Visualizações interativas
        'seaborn',       # Visualizações estatísticas
        'tqdm'           # Barras de progresso
    ]
    
    # Verificar dependências essenciais
    todas_ok = True
    print("\nVerificando dependências de ML essenciais:")
    
    for dependencia in dependencias_ml:
        try:
            # Verifica se o módulo pode ser importado
            importlib.import_module(dependencia)
            print(f"✅ {dependencia}")
        except ImportError:
            print(f"❌ {dependencia} - NÃO ENCONTRADO")
            todas_ok = False
    
    # Verificar dependências opcionais
    print("\nVerificando dependências opcionais:")
    
    for dependencia in dependencias_opcionais:
        try:
            importlib.import_module(dependencia)
            print(f"✅ {dependencia}")
        except ImportError:
            print(f"⚠️ {dependencia} - NÃO ENCONTRADO (opcional)")
    
    # Verificar versões específicas
    try:
        import sklearn
        print(f"scikit-learn version: {sklearn.__version__}")
        
        import xgboost
        print(f"xgboost version: {xgboost.__version__}")
        
        import pandas
        print(f"pandas version: {pandas.__version__}")
        
        import numpy
        print(f"numpy version: {numpy.__version__}")
    except:
        pass
    
    return todas_ok

if __name__ == "__main__":
    print("Verificando todas as dependências...")
    deps_basicas = verificar_dependencias()
    deps_ml = verificar_dependencias_ml()
    
    if deps_basicas and deps_ml:
        print("\n✅ Todas as dependências estão instaladas corretamente.")
    else:
        print("\n❌ Algumas dependências estão faltando. Por favor, instale-as.")
        print("Execute: pip install -r requirements_unified.txt")
        print("Nota: TA-Lib precisa ser instalado separadamente. Consulte as instruções no arquivo requirements_unified.txt.") 