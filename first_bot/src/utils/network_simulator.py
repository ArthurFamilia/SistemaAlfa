"""
Módulo para simulação de latência e ping no bot de trading.

Este módulo permite simular condições de rede reais durante o
backtest e mineração de estratégias, ajudando a identificar 
potenciais problemas relacionados à latência em operações reais.
"""

import time
import random
import requests
from datetime import datetime
import statistics
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env, se existir
load_dotenv()

class NetworkSimulator:
    def __init__(self):
        # Configurações padrão
        self.latencia_base = float(os.getenv('LATENCIA_BASE', '50'))  # ms
        self.variacao_latencia = float(os.getenv('VARIACAO_LATENCIA', '30'))  # ms
        self.prob_latencia_alta = float(os.getenv('PROB_LATENCIA_ALTA', '0.05'))
        self.multiplicador_pico = float(os.getenv('MULTIPLICADOR_PICO', '10'))
        self.simular_ativo = os.getenv('SIMULAR_LATENCIA', 'TRUE').upper() == 'TRUE'
        
        # Estatísticas de latência
        self.latencias = []
        self.pings = []
        self.max_latencia = 0
        self.min_latencia = float('inf')
        
    def medir_latencia_real(self, host='api.binance.com'):
        """
        Mede a latência real para um host específico, incluindo tempo de processamento.
        A diferença entre ping e latência é que a latência inclui o tempo de processamento
        no servidor, enquanto o ping apenas mede o tempo de ida e volta.
        
        Args:
            host (str): Host para medir a latência
            
        Returns:
            float: Tempo de latência em milissegundos
        """
        try:
            inicio = time.time()
            # Fazer uma requisição mais completa que simula uma operação real
            response = requests.get(f'https://{host}/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            response.json()  # Forçar processamento do JSON (parte da latência real)
            fim = time.time()
            
            # Calcular tempo em milissegundos
            latencia_ms = (fim - inicio) * 1000
            
            # Armazenar para estatísticas
            self.latencias.append(latencia_ms)
            self.max_latencia = max(self.max_latencia, latencia_ms)
            self.min_latencia = min(self.min_latencia, latencia_ms)
            
            return latencia_ms
        except Exception as e:
            print(f"Erro ao medir latência para {host}: {str(e)}")
            # Retornar um valor padrão em vez de 0
            return 50.0  # Valor padrão razoável
    
    def aplicar_latencia(self):
        """
        Aplica uma latência simulada baseada nos parâmetros configurados.
        Se a simulação estiver desativada, tenta medir a latência real.
        
        Returns:
            float: Latência aplicada em milissegundos
        """
        # Se simulação desativada, medir latência real
        if not self.simular_ativo:
            if os.getenv('USAR_LATENCIA_REAL', 'TRUE').upper() == 'TRUE':
                return self.medir_latencia_real()
            return 0
        
        # Determinar se é um pico de latência
        pico = random.random() < self.prob_latencia_alta
        
        # Calcular latência base com variação aleatória
        if pico:
            # Simular pico de latência (ex: congestionamento de rede)
            latencia = self.latencia_base * self.multiplicador_pico + random.uniform(0, self.variacao_latencia * 2)
        else:
            # Latência normal com variação
            latencia = self.latencia_base + random.uniform(-self.variacao_latencia, self.variacao_latencia)
            
        # Garantir que a latência não seja negativa
        latencia = max(0, latencia)
        
        # Converter ms para segundos e aplicar espera
        time.sleep(latencia / 1000)
        
        # Atualizar estatísticas
        self.latencias.append(latencia)
        self.max_latencia = max(self.max_latencia, latencia)
        self.min_latencia = min(self.min_latencia, latencia)
        
        return latencia
        
    def medir_ping_real(self, host='api.binance.com'):
        """
        Mede o ping real para um host específico.
        
        Args:
            host (str): Host para medir o ping
            
        Returns:
            float: Tempo de ping em milissegundos
        """
        try:
            inicio = time.time()
            requests.get(f'https://{host}/api/v3/ping', timeout=5)
            fim = time.time()
            
            # Calcular tempo em milissegundos
            ping_ms = (fim - inicio) * 1000
            
            # Armazenar para estatísticas
            self.pings.append(ping_ms)
            
            return ping_ms
        except Exception as e:
            print(f"Erro ao medir ping para {host}: {str(e)}")
            # Retornar um valor padrão em vez de None
            return 0.0
    
    def simular_ping(self):
        """
        Simula um tempo de ping baseado nos parâmetros de latência,
        mas com menor variação (ping é geralmente mais estável que latência).
        
        Returns:
            float: Ping simulado em milissegundos
        """
        if not self.simular_ativo:
            return 0
            
        # Ping geralmente é mais estável que latência total
        variacao_ping = self.variacao_latencia * 0.5
        ping = self.latencia_base * 0.7 + random.uniform(-variacao_ping, variacao_ping)
        
        # Garantir que o ping não seja negativo
        ping = max(0, ping)
        
        # Armazenar para estatísticas
        self.pings.append(ping)
        
        return ping
    
    def medir_ou_simular_ping(self, usar_ping_real=False, host='api.binance.com'):
        """
        Mede o ping real ou simula, dependendo da configuração.
        
        Args:
            usar_ping_real (bool): Se True, mede o ping real; senão, simula
            host (str): Host para medir o ping real
            
        Returns:
            float: Tempo de ping em milissegundos
        """
        if usar_ping_real:
            ping = self.medir_ping_real(host)
            # Garantir que não seja None
            return ping if ping is not None else 0.0
        else:
            return self.simular_ping()
            
    def medir_ou_simular_latencia(self, usar_latencia_real=False, host='api.binance.com'):
        """
        Mede a latência real ou simula, dependendo da configuração.
        
        Args:
            usar_latencia_real (bool): Se True, mede a latência real; senão, simula
            host (str): Host para medir a latência real
            
        Returns:
            float: Tempo de latência em milissegundos
        """
        if usar_latencia_real:
            return self.medir_latencia_real(host)
        else:
            # Usar a função aplicar_latencia, mas sem aplicar o sleep
            if not self.simular_ativo:
                return 0
                
            # Determinar se é um pico de latência
            pico = random.random() < self.prob_latencia_alta
            
            # Calcular latência base com variação aleatória
            if pico:
                # Simular pico de latência
                latencia = self.latencia_base * self.multiplicador_pico + random.uniform(0, self.variacao_latencia * 2)
            else:
                # Latência normal com variação
                latencia = self.latencia_base + random.uniform(-self.variacao_latencia, self.variacao_latencia)
                
            # Garantir que a latência não seja negativa
            latencia = max(0, latencia)
            
            # Atualizar estatísticas
            self.latencias.append(latencia)
            self.max_latencia = max(self.max_latencia, latencia)
            self.min_latencia = min(self.min_latencia, latencia)
            
            return latencia
    
    def obter_estatisticas(self):
        """
        Retorna estatísticas sobre as latências aplicadas.
        
        Returns:
            dict: Estatísticas de latência e ping
        """
        stats = {}
        
        # Estatísticas de latência
        if self.latencias:
            stats["latencia"] = {
                "min": min(self.latencias),
                "max": max(self.latencias),
                "media": statistics.mean(self.latencias),
                "mediana": statistics.median(self.latencias),
                "desvio_padrao": statistics.stdev(self.latencias) if len(self.latencias) > 1 else 0,
                "amostras": len(self.latencias)
            }
        else:
            stats["latencia"] = {
                "min": 0, "max": 0, "media": 0, "mediana": 0, "desvio_padrao": 0, "amostras": 0
            }
            
        # Estatísticas de ping
        if self.pings:
            stats["ping"] = {
                "min": min(self.pings),
                "max": max(self.pings),
                "media": statistics.mean(self.pings),
                "mediana": statistics.median(self.pings),
                "desvio_padrao": statistics.stdev(self.pings) if len(self.pings) > 1 else 0,
                "amostras": len(self.pings)
            }
        else:
            stats["ping"] = {
                "min": 0, "max": 0, "media": 0, "mediana": 0, "desvio_padrao": 0, "amostras": 0
            }
            
        return stats
    
    def gerar_relatorio(self):
        """
        Gera um relatório formatado sobre as condições de rede simuladas.
        
        Returns:
            str: Relatório formatado
        """
        stats = self.obter_estatisticas()
        
        relatorio = [
            "============================================",
            "RELATÓRIO DE CONDIÇÕES DE REDE",
            f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "============================================",
            f"Status da Simulação: {'ATIVO' if self.simular_ativo else 'DESATIVADO'}",
            f"Latência Base: {self.latencia_base} ms",
            f"Variação de Latência: ±{self.variacao_latencia} ms",
            f"Probabilidade de Picos: {self.prob_latencia_alta * 100}%",
            "--------------------------------------------",
            "ESTATÍSTICAS DE LATÊNCIA:",
            f"Mínima: {stats['latencia']['min']:.2f} ms",
            f"Máxima: {stats['latencia']['max']:.2f} ms",
            f"Média: {stats['latencia']['media']:.2f} ms",
            f"Mediana: {stats['latencia']['mediana']:.2f} ms",
            f"Desvio Padrão: {stats['latencia']['desvio_padrao']:.2f} ms",
            f"Amostras: {stats['latencia']['amostras']}",
            "--------------------------------------------",
            "ESTATÍSTICAS DE PING:",
            f"Mínimo: {stats['ping']['min']:.2f} ms",
            f"Máximo: {stats['ping']['max']:.2f} ms",
            f"Médio: {stats['ping']['media']:.2f} ms",
            f"Mediana: {stats['ping']['mediana']:.2f} ms",
            f"Desvio Padrão: {stats['ping']['desvio_padrao']:.2f} ms",
            f"Amostras: {stats['ping']['amostras']}",
            "============================================"
        ]
        
        return "\n".join(relatorio)

    def obter_estatisticas_para_logger(self):
        """
        Retorna as estatísticas de rede em formato adequado para o logger.
        
        Returns:
            dict: Estatísticas formatadas para o logger
        """
        stats = self.obter_estatisticas()
        
        # Adicionar informações sobre a configuração
        return {
            "latencia": stats["latencia"],
            "ping": stats["ping"],
            "configuracao": {
                "simular_ativo": self.simular_ativo,
                "latencia_base": self.latencia_base,
                "variacao_latencia": self.variacao_latencia,
                "prob_latencia_alta": self.prob_latencia_alta,
                "multiplicador_pico": self.multiplicador_pico
            }
        }

# Teste simples do módulo
if __name__ == "__main__":
    # Criar instância do simulador
    simulator = NetworkSimulator()
    
    # Executar 10 simulações
    print("Simulando 10 operações com latência...")
    for i in range(10):
        latencia = simulator.aplicar_latencia()
        ping = simulator.medir_ou_simular_ping(usar_ping_real=(i % 2 == 0))
        print(f"Operação {i+1}: Latência={latencia:.2f}ms, Ping={ping:.2f}ms")
    
    # Exibir relatório
    print("\n" + simulator.gerar_relatorio()) 