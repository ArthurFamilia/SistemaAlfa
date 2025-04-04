#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Menu para Configuração Avançada do Bot de Trading

Este script cria uma interface de menu para configurar as opções avançadas
do backtest, minerador de estratégias e otimização bayesiana.
"""

import os
import sys
import json
from datetime import datetime
from config_avancada import ConfiguracaoAvancada, configuracao_interativa

def exibir_menu_principal():
    """Exibe o menu principal de configuração avançada."""
    print("\n" + "="*60)
    print("        CONFIGURAÇÃO AVANÇADA DO BOT DE TRADING")
    print("="*60)
    print("[1] Configurar parâmetros de backtest")
    print("[2] Configurar minerador de estratégias")
    print("[3] Configurar otimização bayesiana")
    print("[4] Configurar indicadores técnicos")
    print("[5] Utilizar assistente de configuração interativa")
    print("[6] Carregar configuração de arquivo")
    print("[7] Salvar configuração atual")
    print("[8] Exportar configuração para .env")
    print("[9] Imprimir configuração atual")
    print("[0] Sair e aplicar configurações")
    print("="*60)
    
    try:
        opcao = int(input("Escolha uma opção: "))
        return opcao
    except ValueError:
        return -1

def configurar_backtest(config):
    """
    Menu para configurar parâmetros de backtest.
    
    Args:
        config: Instância de ConfiguracaoAvancada
    """
    print("\n--- CONFIGURAÇÃO DE BACKTEST ---")
    
    while True:
        print("\nParâmetros atuais:")
        for i, (key, value) in enumerate(config.backtest_config.items(), 1):
            print(f"[{i}] {key}: {value}")
        
        print("\n[0] Voltar ao menu principal")
        
        try:
            opcao = int(input("\nEscolha o parâmetro a modificar (0 para voltar): "))
            
            if opcao == 0:
                break
                
            if 1 <= opcao <= len(config.backtest_config):
                param = list(config.backtest_config.keys())[opcao-1]
                valor_atual = config.backtest_config[param]
                
                print(f"\nModificando: {param}")
                print(f"Valor atual: {valor_atual}")
                
                novo_valor = input("Novo valor: ")
                
                # Converter para o tipo correto
                if isinstance(valor_atual, bool):
                    novo_valor = novo_valor.lower() in ('s', 'sim', 'true', 't', 'yes', 'y', '1')
                elif isinstance(valor_atual, int):
                    novo_valor = int(novo_valor)
                elif isinstance(valor_atual, float):
                    novo_valor = float(novo_valor)
                elif isinstance(valor_atual, list):
                    # Formato de lista: valor1,valor2,valor3
                    if novo_valor:
                        novo_valor = [x.strip() for x in novo_valor.split(',')]
                        
                        # Converter elementos se for lista de números
                        if valor_atual and all(isinstance(x, (int, float)) for x in valor_atual):
                            if all(isinstance(x, int) for x in valor_atual):
                                novo_valor = [int(x) for x in novo_valor]
                            else:
                                novo_valor = [float(x) for x in novo_valor]
                
                # Atualizar configuração
                config.modificar_config_backtest(**{param: novo_valor})
                print(f"\nParâmetro {param} atualizado para: {novo_valor}")
            else:
                print("\nOpção inválida!")
                
        except ValueError as e:
            print(f"\nErro ao modificar parâmetro: {e}")
            print("Por favor, tente novamente com um valor válido.")

def configurar_minerador(config):
    """
    Menu para configurar minerador de estratégias.
    
    Args:
        config: Instância de ConfiguracaoAvancada
    """
    print("\n--- CONFIGURAÇÃO DO MINERADOR DE ESTRATÉGIAS ---")
    
    while True:
        print("\nParâmetros atuais:")
        for i, (key, value) in enumerate(config.minerador_config.items(), 1):
            # Limitar tamanho de listas longas para exibição
            if isinstance(value, list) and len(str(value)) > 50:
                print(f"[{i}] {key}: {str(value)[:50]}...")
            else:
                print(f"[{i}] {key}: {value}")
        
        print("\n[0] Voltar ao menu principal")
        
        try:
            opcao = int(input("\nEscolha o parâmetro a modificar (0 para voltar): "))
            
            if opcao == 0:
                break
                
            if 1 <= opcao <= len(config.minerador_config):
                param = list(config.minerador_config.keys())[opcao-1]
                valor_atual = config.minerador_config[param]
                
                print(f"\nModificando: {param}")
                print(f"Valor atual: {valor_atual}")
                
                # Casos especiais para alguns parâmetros
                if param == 'criterio_selecao':
                    print("\nOpções disponíveis: expectativa, lucro_total, taxa_acerto, sharpe")
                
                novo_valor = input("Novo valor: ")
                
                # Converter para o tipo correto
                if isinstance(valor_atual, bool):
                    novo_valor = novo_valor.lower() in ('s', 'sim', 'true', 't', 'yes', 'y', '1')
                elif isinstance(valor_atual, int):
                    novo_valor = int(novo_valor)
                elif isinstance(valor_atual, float):
                    novo_valor = float(novo_valor)
                elif isinstance(valor_atual, list):
                    # Formato de lista: valor1,valor2,valor3
                    if novo_valor:
                        novo_valor = [x.strip() for x in novo_valor.split(',')]
                        
                        # Converter elementos se for lista de números
                        if valor_atual and all(isinstance(x, (int, float)) for x in valor_atual):
                            if all(isinstance(x, int) for x in valor_atual):
                                novo_valor = [int(x) for x in novo_valor]
                            else:
                                novo_valor = [float(x) for x in novo_valor]
                
                # Atualizar configuração
                config.modificar_config_minerador(**{param: novo_valor})
                print(f"\nParâmetro {param} atualizado para: {novo_valor}")
            else:
                print("\nOpção inválida!")
                
        except ValueError as e:
            print(f"\nErro ao modificar parâmetro: {e}")
            print("Por favor, tente novamente com um valor válido.")

def configurar_otimizacao(config):
    """
    Menu para configurar otimização bayesiana.
    
    Args:
        config: Instância de ConfiguracaoAvancada
    """
    print("\n--- CONFIGURAÇÃO DE OTIMIZAÇÃO BAYESIANA ---")
    
    while True:
        print("\nParâmetros atuais:")
        for i, (key, value) in enumerate(config.otimizacao_config.items(), 1):
            # Tratamento especial para dicionários
            if isinstance(value, dict):
                print(f"[{i}] {key}: {{{len(value)} itens}}")
            else:
                print(f"[{i}] {key}: {value}")
        
        print("\n[0] Voltar ao menu principal")
        print("[E] Editar espaços de busca")
        
        opcao = input("\nEscolha o parâmetro a modificar (0 para voltar): ")
        
        if opcao == '0':
            break
            
        if opcao.upper() == 'E':
            configurar_espacos_busca(config)
            continue
            
        try:
            opcao = int(opcao)
            
            if 1 <= opcao <= len(config.otimizacao_config):
                param = list(config.otimizacao_config.keys())[opcao-1]
                valor_atual = config.otimizacao_config[param]
                
                # Pular edição direta de dicionários
                if isinstance(valor_atual, dict):
                    print("\nPara editar espaços de busca, use a opção [E]")
                    continue
                
                print(f"\nModificando: {param}")
                print(f"Valor atual: {valor_atual}")
                
                # Casos especiais para alguns parâmetros
                if param == 'metrica_otimizacao':
                    print("\nOpções disponíveis: expectativa, lucro_total, sharpe, sortino")
                
                novo_valor = input("Novo valor: ")
                
                # Converter para o tipo correto
                if isinstance(valor_atual, bool):
                    novo_valor = novo_valor.lower() in ('s', 'sim', 'true', 't', 'yes', 'y', '1')
                elif isinstance(valor_atual, int):
                    novo_valor = int(novo_valor)
                elif isinstance(valor_atual, float):
                    novo_valor = float(novo_valor)
                elif isinstance(valor_atual, list):
                    # Formato de lista: valor1,valor2,valor3
                    if novo_valor:
                        novo_valor = [x.strip() for x in novo_valor.split(',')]
                        
                        # Converter elementos se for lista de números
                        if valor_atual and all(isinstance(x, (int, float)) for x in valor_atual):
                            if all(isinstance(x, int) for x in valor_atual):
                                novo_valor = [int(x) for x in novo_valor]
                            else:
                                novo_valor = [float(x) for x in novo_valor]
                
                # Atualizar configuração
                config.modificar_config_otimizacao(**{param: novo_valor})
                print(f"\nParâmetro {param} atualizado para: {novo_valor}")
            else:
                print("\nOpção inválida!")
                
        except ValueError as e:
            print(f"\nErro ao modificar parâmetro: {e}")
            print("Por favor, tente novamente com um valor válido.")

def configurar_espacos_busca(config):
    """
    Menu para configurar espaços de busca da otimização bayesiana.
    
    Args:
        config: Instância de ConfiguracaoAvancada
    """
    print("\n--- CONFIGURAÇÃO DE ESPAÇOS DE BUSCA ---")
    
    while True:
        print("\nEspaços contínuos/inteiros:")
        espacos = config.otimizacao_config['espacos_busca']
        for i, (param, intervalo) in enumerate(espacos.items(), 1):
            print(f"[{i}] {param}: {intervalo}")
        
        print("\nEspaços categóricos:")
        espacos_cat = config.otimizacao_config['espacos_categoricos']
        offset = len(espacos)
        for i, (param, valores) in enumerate(espacos_cat.items(), offset+1):
            print(f"[{i}] {param}: {valores}")
        
        print("\n[A] Adicionar novo espaço de busca")
        print("[0] Voltar")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '0':
            break
        
        if opcao.upper() == 'A':
            print("\nAdicionando novo espaço de busca")
            param = input("Nome do parâmetro: ")
            
            tipo = input("Tipo (continuo/inteiro/categorico): ").lower()
            
            if tipo in ['continuo', 'inteiro']:
                try:
                    min_val = input("Valor mínimo: ")
                    max_val = input("Valor máximo: ")
                    
                    if tipo == 'inteiro':
                        min_val = int(min_val)
                        max_val = int(max_val)
                    else:
                        min_val = float(min_val)
                        max_val = float(max_val)
                    
                    intervalo = (min_val, max_val)
                    config.definir_espaco_busca_personalizado(param, intervalo, tipo)
                    
                except ValueError as e:
                    print(f"Erro: {e}")
                    print("Por favor, insira valores numéricos válidos.")
            
            elif tipo == 'categorico':
                valores_str = input("Valores (separados por vírgula): ")
                valores = [val.strip() for val in valores_str.split(',')]
                
                # Converter para booleanos ou números se apropriado
                converted_valores = []
                for val in valores:
                    if val.lower() in ['true', 'false']:
                        converted_valores.append(val.lower() == 'true')
                    else:
                        try:
                            # Tentar converter para número
                            if '.' in val:
                                converted_valores.append(float(val))
                            else:
                                converted_valores.append(int(val))
                        except ValueError:
                            # Manter como string
                            converted_valores.append(val)
                
                config.definir_espaco_busca_personalizado(param, converted_valores, 'categorico')
            
            else:
                print("Tipo inválido! Use continuo, inteiro ou categorico.")
            
            continue
        
        try:
            opcao = int(opcao)
            
            if 1 <= opcao <= len(espacos):
                # Editar espaço contínuo/inteiro
                param = list(espacos.keys())[opcao-1]
                intervalo = espacos[param]
                
                print(f"\nEditando espaço para: {param}")
                print(f"Intervalo atual: {intervalo}")
                
                try:
                    min_val = input(f"Novo valor mínimo [{intervalo[0]}]: ") or intervalo[0]
                    max_val = input(f"Novo valor máximo [{intervalo[1]}]: ") or intervalo[1]
                    
                    if isinstance(intervalo[0], int):
                        min_val = int(min_val)
                        max_val = int(max_val)
                        tipo = 'inteiro'
                    else:
                        min_val = float(min_val)
                        max_val = float(max_val)
                        tipo = 'continuo'
                    
                    novo_intervalo = (min_val, max_val)
                    config.definir_espaco_busca_personalizado(param, novo_intervalo, tipo)
                    
                except ValueError as e:
                    print(f"Erro: {e}")
                    print("Por favor, insira valores numéricos válidos.")
            
            elif len(espacos) < opcao <= len(espacos) + len(espacos_cat):
                # Editar espaço categórico
                idx = opcao - len(espacos) - 1
                param = list(espacos_cat.keys())[idx]
                valores = espacos_cat[param]
                
                print(f"\nEditando espaço para: {param}")
                print(f"Valores atuais: {valores}")
                
                valores_str = input("Novos valores (separados por vírgula): ")
                novos_valores = [val.strip() for val in valores_str.split(',')]
                
                # Converter para booleanos ou números se apropriado
                converted_valores = []
                for val in novos_valores:
                    if val.lower() in ['true', 'false']:
                        converted_valores.append(val.lower() == 'true')
                    else:
                        try:
                            # Tentar converter para número
                            if '.' in val:
                                converted_valores.append(float(val))
                            else:
                                converted_valores.append(int(val))
                        except ValueError:
                            # Manter como string
                            converted_valores.append(val)
                
                config.definir_espaco_busca_personalizado(param, converted_valores, 'categorico')
            
            else:
                print("\nOpção inválida!")
                
        except ValueError as e:
            print(f"\nErro ao modificar espaço de busca: {e}")
            print("Por favor, tente novamente com um valor válido.")
        except IndexError:
            print("\nÍndice inválido!")

def configurar_indicadores(config):
    """
    Menu para configurar indicadores técnicos.
    
    Args:
        config: Instância de ConfiguracaoAvancada
    """
    print("\n--- CONFIGURAÇÃO DE INDICADORES TÉCNICOS ---")
    
    while True:
        print("\nIndicadores disponíveis:")
        indicadores = [k for k in config.indicadores_config.keys() if k != 'indicadores_personalizados']
        for i, ind in enumerate(indicadores, 1):
            print(f"[{i}] {ind}")
        
        print("\n[A] Adicionar indicador personalizado")
        print("[0] Voltar ao menu principal")
        
        opcao = input("\nEscolha um indicador para configurar (0 para voltar): ")
        
        if opcao == '0':
            break
            
        if opcao.upper() == 'A':
            adicionar_indicador_personalizado(config)
            continue
            
        try:
            opcao = int(opcao)
            
            if 1 <= opcao <= len(indicadores):
                indicador = indicadores[opcao-1]
                configurar_parametros_indicador(config, indicador)
            else:
                print("\nOpção inválida!")
                
        except ValueError:
            print("\nOpção inválida! Por favor, digite um número.")

def configurar_parametros_indicador(config, indicador):
    """
    Menu para configurar parâmetros de um indicador técnico.
    
    Args:
        config: Instância de ConfiguracaoAvancada
        indicador: Nome do indicador a configurar
    """
    print(f"\n--- CONFIGURAÇÃO DO INDICADOR {indicador.upper()} ---")
    
    while True:
        print("\nParâmetros atuais:")
        params = config.indicadores_config[indicador]
        for i, (param, valor) in enumerate(params.items(), 1):
            print(f"[{i}] {param}: {valor}")
        
        print("\n[0] Voltar")
        
        try:
            opcao = int(input("\nEscolha o parâmetro a modificar (0 para voltar): "))
            
            if opcao == 0:
                break
                
            if 1 <= opcao <= len(params):
                param = list(params.keys())[opcao-1]
                valor_atual = params[param]
                
                print(f"\nModificando: {param}")
                print(f"Valor atual: {valor_atual}")
                
                novo_valor = input("Novo valor: ")
                
                # Converter para o tipo correto
                if isinstance(valor_atual, bool):
                    novo_valor = novo_valor.lower() in ('s', 'sim', 'true', 't', 'yes', 'y', '1')
                elif isinstance(valor_atual, int):
                    novo_valor = int(novo_valor)
                elif isinstance(valor_atual, float):
                    novo_valor = float(novo_valor)
                
                # Atualizar configuração
                config.modificar_config_indicadores(indicador, **{param: novo_valor})
                print(f"\nParâmetro {param} atualizado para: {novo_valor}")
            else:
                print("\nOpção inválida!")
                
        except ValueError as e:
            print(f"\nErro ao modificar parâmetro: {e}")
            print("Por favor, tente novamente com um valor válido.")

def adicionar_indicador_personalizado(config):
    """
    Adiciona um indicador técnico personalizado.
    
    Args:
        config: Instância de ConfiguracaoAvancada
    """
    print("\n--- ADICIONAR INDICADOR PERSONALIZADO ---")
    
    nome = input("Nome do indicador: ")
    
    parametros = {}
    print("\nAdicione os parâmetros (deixe em branco para finalizar):")
    
    while True:
        param_nome = input("\nNome do parâmetro (ou vazio para finalizar): ")
        if not param_nome:
            break
        
        tipo = input("Tipo (int/float/bool): ").lower()
        valor = input("Valor: ")
        
        if tipo == 'int':
            parametros[param_nome] = int(valor)
        elif tipo == 'float':
            parametros[param_nome] = float(valor)
        elif tipo == 'bool':
            parametros[param_nome] = valor.lower() in ('s', 'sim', 'true', 't', 'yes', 'y', '1')
        else:
            parametros[param_nome] = valor
    
    if parametros:
        config.adicionar_indicador_personalizado(nome, parametros)
        print(f"\nIndicador personalizado '{nome}' adicionado com sucesso!")
    else:
        print("\nNenhum parâmetro adicionado. Operação cancelada.")

def main():
    """Função principal do menu de configuração avançada."""
    # Criar configuração
    config = ConfiguracaoAvancada()
    
    while True:
        opcao = exibir_menu_principal()
        
        if opcao == 0:  # Sair
            print("\nSaindo e aplicando configurações...")
            break
            
        elif opcao == 1:  # Configurar backtest
            configurar_backtest(config)
            
        elif opcao == 2:  # Configurar minerador
            configurar_minerador(config)
            
        elif opcao == 3:  # Configurar otimização
            configurar_otimizacao(config)
            
        elif opcao == 4:  # Configurar indicadores
            configurar_indicadores(config)
            
        elif opcao == 5:  # Assistente interativo
            config = configuracao_interativa()
            
        elif opcao == 6:  # Carregar configuração
            arquivo = input("\nCaminho do arquivo de configuração: ")
            if os.path.exists(arquivo):
                config.carregar_configuracoes(arquivo)
                print(f"\nConfiguração carregada de: {arquivo}")
            else:
                print(f"\nArquivo não encontrado: {arquivo}")
            
        elif opcao == 7:  # Salvar configuração
            arquivo = input("\nCaminho para salvar a configuração: ")
            config.salvar_configuracoes(arquivo)
            print(f"\nConfiguração salva em: {arquivo}")
            
        elif opcao == 8:  # Exportar para .env
            arquivo = input("\nCaminho para salvar o arquivo .env (padrão: .env.config): ") or ".env.config"
            config.exportar_para_env(arquivo)
            print(f"\nConfiguração exportada para: {arquivo}")
            
        elif opcao == 9:  # Imprimir configuração
            config.imprimir_configuracoes()
            
        else:
            print("\nOpção inválida! Por favor, escolha novamente.")
    
    # Retornar configuração para uso no programa principal
    return config

if __name__ == "__main__":
    # Executar menu quando o script é executado diretamente
    config = main()
    
    # Imprimir configuração final
    print("\nConfiguração final:")
    config.imprimir_configuracoes()
    
    # Perguntar se deseja salvar
    salvar = input("\nDeseja salvar esta configuração? (s/n): ")
    if salvar.lower() == 's':
        arquivo = input("Nome do arquivo [config_final.json]: ") or "config_final.json"
        config.salvar_configuracoes(arquivo)
        print(f"\nConfiguração salva em: {arquivo}")
        
        # Perguntar se deseja exportar para .env
        exportar = input("\nDeseja exportar para arquivo .env? (s/n): ")
        if exportar.lower() == 's':
            arquivo_env = input("Nome do arquivo [.env.config]: ") or ".env.config"
            config.exportar_para_env(arquivo_env)
            print(f"\nConfiguração exportada para: {arquivo_env}")
    
    print("\nAté logo!") 