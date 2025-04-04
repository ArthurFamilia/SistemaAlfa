#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integração da configuração avançada com o minerador de estratégias.

Este script permite executar o minerador de estratégias com configurações
avançadas definidas pelo usuário.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Importar módulos do projeto
try:
    from config_avancada import ConfiguracaoAvancada
    from src.ml.strategy_miner_ml import MineradorEstrategiasML
    
    # Se backtest.py estiver na raiz
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from backtest import Backtest
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Verifique se todos os módulos estão instalados e se a estrutura do projeto está correta.")
    sys.exit(1)

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/minerador_avancado.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("minerador_avancado")

def criar_funcao_backtest(config: ConfiguracaoAvancada):
    """
    Cria uma função de backtest configurada com base nas configurações avançadas.
    
    Args:
        config: Configuração avançada
        
    Returns:
        Função que executa backtest com os parâmetros configurados
    """
    # Obter parâmetros de backtest
    backtest_config = config.backtest_config
    indicadores_config = config.indicadores_config
    
    def funcao_backtest(**kwargs):
        """
        Função de backtest configurada.
        
        Args:
            **kwargs: Parâmetros adicionais/override
            
        Returns:
            Resultado do backtest
        """
        # Mesclar parâmetros padrão com os fornecidos
        parametros = {
            'par': backtest_config['par'],
            'timeframe': backtest_config['timeframe'],
            'position_size': backtest_config['position_size'],
            'dias': backtest_config['dias_historico'],
            'plotar_grafico': backtest_config['plotar_grafico']
        }
        
        # Adicionar parâmetros de indicadores
        parametros.update({
            'adx_period': indicadores_config['adx']['period'],
            'adx_threshold': indicadores_config['adx']['threshold'],
            'di_plus_period': indicadores_config['di_plus']['period'],
            'di_plus_threshold': indicadores_config['di_plus']['threshold'],
            'di_minus_period': indicadores_config['di_minus']['period'],
            'di_minus_threshold': indicadores_config['di_minus']['threshold'],
            'atr_period': indicadores_config['atr']['period']
        })
        
        # Sobrescrever com os parâmetros passados
        parametros.update(kwargs)
        
        # Criar e executar backtest
        backtest = Backtest(dias_historico=parametros['dias'])
        resultado = backtest.executar(
            par=parametros['par'],
            timeframe=parametros['timeframe'],
            position_size=parametros['position_size'],
            adx_period=parametros['adx_period'],
            adx_threshold=parametros['adx_threshold'],
            di_plus_period=parametros['di_plus_period'],
            di_plus_threshold=parametros['di_plus_threshold'],
            di_minus_period=parametros['di_minus_period'],
            di_minus_threshold=parametros['di_minus_threshold'],
            atr_period=parametros['atr_period']
        )
        
        return resultado
    
    return funcao_backtest

def executar_minerador_estrategias(config: ConfiguracaoAvancada):
    """
    Executa o minerador de estratégias com as configurações avançadas.
    
    Args:
        config: Configuração avançada
        
    Returns:
        Lista com as melhores estratégias encontradas
    """
    # Obter configurações do minerador
    minerador_config = config.minerador_config
    
    # Criar função de backtest
    funcao_backtest = criar_funcao_backtest(config)
    
    # Parâmetros para o minerador
    dias_historico = minerador_config['dias_historico']
    pares = minerador_config['pares']
    timeframes = minerador_config['timeframes']
    
    # Espaços de busca
    espacos_busca = {
        'adx_period': minerador_config['periodos_adx'],
        'di_plus_period': minerador_config['periodos_di'],
        'di_minus_period': minerador_config['periodos_di'],
        'adx_threshold': minerador_config['limiares_adx'],
        'di_plus_threshold': minerador_config['limiares_di_plus'],
        'di_minus_threshold': minerador_config['limiares_di_minus'],
        'stop_multiplier': minerador_config['multiplicadores_stop'],
        'gain_multiplier': minerador_config['multiplicadores_gain']
    }
    
    # Critérios de seleção
    criterio_selecao = minerador_config['criterio_selecao']
    num_resultados = minerador_config['num_resultados']
    
    # Criar minerador
    minerador = MineradorEstrategiasML(
        backtest_fn=funcao_backtest,
        dias_historico=dias_historico,
        usar_ml=minerador_config['usar_ml'],
        usar_classificador_regimes=minerador_config['usar_classificador_regimes']
    )
    
    logger.info("Iniciando mineração de estratégias...")
    logger.info(f"Pares: {pares}")
    logger.info(f"Timeframes: {timeframes}")
    logger.info(f"Dias históricos: {dias_historico}")
    logger.info(f"Critério de seleção: {criterio_selecao}")
    
    # Para cada par e timeframe
    resultados_combinados = []
    
    for par in pares:
        for timeframe in timeframes:
            logger.info(f"Minerando estratégias para {par} ({timeframe})...")
            
            try:
                # Executar mineração
                resultados = minerador.minerar_estrategias(
                    espacos_busca=espacos_busca,
                    par=par,
                    timeframe=timeframe,
                    criterio_selecao=criterio_selecao,
                    max_estrategias=minerador_config['max_estrategias']
                )
                
                # Adicionar par e timeframe aos resultados
                for resultado in resultados:
                    resultado['par'] = par
                    resultado['timeframe'] = timeframe
                
                resultados_combinados.extend(resultados)
                
                # Salvar resultados para este par/timeframe
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                arquivo = f"resultados/estrategias/estrategias_{par}_{timeframe}_{timestamp}.json"
                
                os.makedirs(os.path.dirname(arquivo), exist_ok=True)
                
                with open(arquivo, 'w') as f:
                    json.dump(resultados, f, indent=2)
                
                logger.info(f"Resultados salvos em: {arquivo}")
                logger.info(f"Encontradas {len(resultados)} estratégias para {par} ({timeframe})")
                
            except Exception as e:
                logger.error(f"Erro ao minerar estratégias para {par} ({timeframe}): {e}")
    
    # Ordenar resultados combinados
    if criterio_selecao == 'expectativa':
        resultados_combinados.sort(key=lambda x: x.get('expectativa_matematica', 0), reverse=True)
    elif criterio_selecao == 'lucro_total':
        resultados_combinados.sort(key=lambda x: x.get('lucro_total', 0), reverse=True)
    elif criterio_selecao == 'taxa_acerto':
        resultados_combinados.sort(key=lambda x: x.get('taxa_acerto', 0), reverse=True)
    elif criterio_selecao == 'sharpe':
        resultados_combinados.sort(key=lambda x: x.get('sharpe_ratio', 0), reverse=True)
    
    # Limitar ao número de resultados
    resultados_combinados = resultados_combinados[:num_resultados]
    
    # Salvar resultados combinados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_combinado = f"resultados/estrategias/estrategias_combinadas_{timestamp}.json"
    
    with open(arquivo_combinado, 'w') as f:
        json.dump(resultados_combinados, f, indent=2)
    
    logger.info(f"Resultados combinados salvos em: {arquivo_combinado}")
    logger.info(f"Total de estratégias: {len(resultados_combinados)}")
    
    # Exibir melhores estratégias
    if resultados_combinados:
        logger.info("\nMelhores estratégias encontradas:")
        for i, estrategia in enumerate(resultados_combinados[:5], 1):
            logger.info(f"\n{i}. Estratégia para {estrategia['par']} ({estrategia['timeframe']}):")
            for param, valor in estrategia.items():
                if param not in ['par', 'timeframe']:
                    logger.info(f"   {param}: {valor}")
    
    return resultados_combinados

def testar_robustez_estrategias(config: ConfiguracaoAvancada, estrategias: List[Dict[str, Any]]):
    """
    Testa a robustez das estratégias encontradas em diferentes períodos.
    
    Args:
        config: Configuração avançada
        estrategias: Lista de estratégias a testar
        
    Returns:
        Estratégias com métricas de robustez
    """
    # Verificar se deve testar robustez
    if not config.minerador_config['testar_robustez'] or not estrategias:
        return estrategias
    
    logger.info("\nTestando robustez das estratégias...")
    
    # Períodos para teste
    periodos = config.minerador_config['periodos_teste_robustez']
    logger.info(f"Períodos de teste: {periodos}")
    
    # Criar função de backtest
    funcao_backtest = criar_funcao_backtest(config)
    
    # Testar cada estratégia em cada período
    for estrategia in estrategias:
        logger.info(f"\nTestando robustez para estratégia em {estrategia['par']} ({estrategia['timeframe']})...")
        
        # Extrair parâmetros da estratégia
        parametros = {k: v for k, v in estrategia.items() if k not in [
            'par', 'timeframe', 'lucro_total', 'taxa_acerto', 'expectativa_matematica', 
            'sharpe_ratio', 'operacoes', 'max_drawdown'
        ]}
        
        # Adicionar par e timeframe
        parametros['par'] = estrategia['par']
        parametros['timeframe'] = estrategia['timeframe']
        
        # Resultados por período
        resultados_periodos = []
        
        # Para cada período
        for periodo in periodos:
            logger.info(f"Testando em período: {periodo}...")
            
            try:
                # Definir dias históricos com base no período
                if periodo.endswith('d'):
                    dias = int(periodo[:-1])
                elif periodo.endswith('w'):
                    dias = int(periodo[:-1]) * 7
                elif periodo.endswith('m'):
                    dias = int(periodo[:-1]) * 30
                else:
                    dias = int(periodo)
                
                # Executar backtest para este período
                parametros['dias'] = dias
                resultado = funcao_backtest(**parametros)
                
                # Extrair métricas principais
                metricas = {
                    'periodo': periodo,
                    'lucro_total': resultado.get('lucro_total', 0),
                    'taxa_acerto': resultado.get('taxa_acerto', 0),
                    'expectativa_matematica': resultado.get('expectativa_matematica', 0),
                    'sharpe_ratio': resultado.get('sharpe_ratio', 0),
                    'max_drawdown': resultado.get('max_drawdown', 0),
                    'num_operacoes': len(resultado.get('operacoes', []))
                }
                
                resultados_periodos.append(metricas)
                
                logger.info(f"  Lucro total: {metricas['lucro_total']:.2f}")
                logger.info(f"  Taxa de acerto: {metricas['taxa_acerto']:.2f}")
                logger.info(f"  Expectativa matemática: {metricas['expectativa_matematica']:.2f}")
                
            except Exception as e:
                logger.error(f"Erro ao testar período {periodo}: {e}")
        
        # Adicionar resultados dos períodos à estratégia
        estrategia['resultados_periodos'] = resultados_periodos
        
        # Calcular métricas de robustez
        if resultados_periodos:
            # Consistência de lucratividade: % de períodos lucrativos
            periodos_lucrativos = sum(1 for r in resultados_periodos if r['lucro_total'] > 0)
            consistencia = periodos_lucrativos / len(resultados_periodos)
            estrategia['consistencia_lucratividade'] = consistencia
            
            # Variabilidade das métricas
            lucros = [r['lucro_total'] for r in resultados_periodos]
            expectativas = [r['expectativa_matematica'] for r in resultados_periodos]
            
            import numpy as np
            estrategia['variabilidade_lucro'] = np.std(lucros) / (np.mean(lucros) if np.mean(lucros) != 0 else 1)
            estrategia['variabilidade_expectativa'] = np.std(expectativas) / (np.mean(expectativas) if np.mean(expectativas) != 0 else 1)
            
            logger.info(f"Consistência de lucratividade: {consistencia:.2f}")
            logger.info(f"Variabilidade do lucro: {estrategia['variabilidade_lucro']:.2f}")
    
    return estrategias

def main():
    """Função principal para executar o minerador de estratégias avançado."""
    # Carregar configuração avançada
    config_file = input("Caminho para arquivo de configuração (deixe em branco para usar .env): ")
    
    config = ConfiguracaoAvancada()
    
    if config_file and os.path.exists(config_file):
        config.carregar_configuracoes(config_file)
        logger.info(f"Configuração carregada de: {config_file}")
    else:
        logger.info("Usando configuração padrão do arquivo .env")
    
    # Confirmar execução
    logger.info("\nConfiguração do minerador de estratégias:")
    for key, value in config.minerador_config.items():
        logger.info(f"{key}: {value}")
    
    confirmar = input("\nDeseja executar o minerador com essas configurações? (s/n): ")
    if confirmar.lower() != 's':
        logger.info("Execução cancelada pelo usuário.")
        return
    
    # Executar minerador
    try:
        estrategias = executar_minerador_estrategias(config)
        
        # Testar robustez
        if config.minerador_config['testar_robustez'] and estrategias:
            estrategias = testar_robustez_estrategias(config, estrategias)
            
            # Salvar estratégias com métricas de robustez
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            arquivo = f"resultados/estrategias/estrategias_robustez_{timestamp}.json"
            
            with open(arquivo, 'w') as f:
                json.dump(estrategias, f, indent=2)
            
            logger.info(f"Estratégias com métricas de robustez salvas em: {arquivo}")
        
        logger.info("\nMineração de estratégias concluída!")
        
    except Exception as e:
        logger.error(f"Erro ao executar minerador: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcesso interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Erro não tratado: {e}", exc_info=True) 