#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monitoramento de recursos do sistema durante a execução do bot.

Este módulo fornece funções para monitorar o uso de CPU, memória e outras 
métricas de sistema durante a execução do bot de trading com ML.
"""

import os
import time
import logging
import threading
import datetime
from collections import deque
import psutil

class MonitorRecursos:
    """
    Classe para monitorar recursos do sistema durante a execução do bot.
    
    Mantém registro de uso de CPU, memória e outros recursos, com capacidade
    para exportar relatórios e alertar sobre condições críticas.
    """
    
    def __init__(self, intervalo_segundos=5, historico_maximo=720):
        """
        Inicializa o monitor de recursos.
        
        Args:
            intervalo_segundos (int): Intervalo entre medições em segundos (default: 5)
            historico_maximo (int): Número máximo de registros a manter (default: 720) 
                                   720 * 5s = 1 hora de histórico
        """
        self.intervalo = intervalo_segundos
        self.historico_max = historico_maximo
        self.rodando = False
        self.thread = None
        
        # Histórico de métricas
        self.historico_cpu = deque(maxlen=historico_maximo)
        self.historico_memoria = deque(maxlen=historico_maximo)
        self.historico_disco = deque(maxlen=historico_maximo)
        self.historico_rede = deque(maxlen=historico_maximo)
        self.timestamps = deque(maxlen=historico_maximo)
        
        # Configurar logger
        self.logger = logging.getLogger('monitor_recursos')
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/recursos_sistema.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Verificar se o diretório de logs existe
        os.makedirs('logs', exist_ok=True)
        
        # Obter informações do sistema
        self.info_sistema = self._obter_info_sistema()
        
    def _obter_info_sistema(self):
        """
        Obtém informações gerais sobre o sistema.
        
        Returns:
            dict: Dicionário com informações do sistema
        """
        # Obter informações de disco corretamente
        disco_total = {}
        try:
            for disk in psutil.disk_partitions(all=False):
                if os.name != 'nt' or 'cdrom' not in disk.opts.lower():
                    try:
                        usage = psutil.disk_usage(disk.mountpoint)
                        disco_total[disk.mountpoint] = usage.total / (1024 * 1024 * 1024)  # GB
                    except (PermissionError, FileNotFoundError):
                        pass
        except Exception as e:
            self.logger.error(f"Erro ao obter informações de disco: {e}")
            disco_total = {"erro": str(e)}
        
        info = {
            'sistema': f"{os.name} - {psutil.os.name}",  # Corrigido: removido () pois não é uma função
            'processador': psutil.cpu_count(logical=True),
            'cpu_fisicos': psutil.cpu_count(logical=False),
            'memoria_total': psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
            'disco_total': disco_total,
            'data_inicio': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.logger.info(f"Informações do sistema: {info}")
        return info
        
    def iniciar(self):
        """
        Inicia o monitoramento em uma thread separada.
        """
        if self.rodando:
            self.logger.warning("Monitoramento já está em execução")
            return
            
        self.rodando = True
        self.thread = threading.Thread(target=self._loop_monitoramento, daemon=True)
        self.thread.start()
        self.logger.info("Monitoramento de recursos iniciado")
        
    def parar(self):
        """
        Para o monitoramento.
        """
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2*self.intervalo)
        self.logger.info("Monitoramento de recursos parado")
        
    def _loop_monitoramento(self):
        """
        Loop principal de monitoramento que coleta métricas periodicamente.
        """
        # Inicializar contadores de rede
        bytes_enviados_anterior = psutil.net_io_counters().bytes_sent
        bytes_recebidos_anterior = psutil.net_io_counters().bytes_recv
        
        while self.rodando:
            try:
                # Coletar métricas
                uso_cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                uso_mem = mem.percent
                uso_mem_gb = mem.used / (1024 * 1024 * 1024)  # GB
                
                # Estatísticas de disco
                uso_disco = {}
                try:
                    for disk in psutil.disk_partitions(all=False):
                        if os.name != 'nt' or 'cdrom' not in disk.opts.lower():
                            try:
                                uso = psutil.disk_usage(disk.mountpoint)
                                uso_disco[disk.mountpoint] = {
                                    'percentual': uso.percent,
                                    'usado_gb': uso.used / (1024 * 1024 * 1024)
                                }
                            except (PermissionError, FileNotFoundError):
                                pass
                except Exception as e:
                    self.logger.error(f"Erro ao coletar uso de disco: {e}")
                
                # Estatísticas de rede
                try:
                    contadores_rede = psutil.net_io_counters()
                    bytes_enviados = contadores_rede.bytes_sent
                    bytes_recebidos = contadores_rede.bytes_recv
                    
                    # Calcular taxa em KB/s
                    enviados_kb = (bytes_enviados - bytes_enviados_anterior) / 1024
                    recebidos_kb = (bytes_recebidos - bytes_recebidos_anterior) / 1024
                    
                    bytes_enviados_anterior = bytes_enviados
                    bytes_recebidos_anterior = bytes_recebidos
                    
                    uso_rede = {
                        'enviados_kb': enviados_kb / self.intervalo,
                        'recebidos_kb': recebidos_kb / self.intervalo
                    }
                except Exception as e:
                    uso_rede = {'erro': str(e)}
                    self.logger.error(f"Erro ao coletar estatísticas de rede: {e}")
                
                # Registrar métricas
                timestamp = datetime.datetime.now()
                self.historico_cpu.append(uso_cpu)
                self.historico_memoria.append((uso_mem, uso_mem_gb))
                self.historico_disco.append(uso_disco)
                self.historico_rede.append(uso_rede)
                self.timestamps.append(timestamp)
                
                # Log periódico (a cada 12 medições = ~1 minuto com intervalo de 5s)
                if len(self.historico_cpu) % 12 == 0:
                    self.logger.info(
                        f"CPU: {uso_cpu:.1f}% | Memória: {uso_mem:.1f}% ({uso_mem_gb:.2f} GB) | "
                        f"Rede: ↑{uso_rede.get('enviados_kb', 0):.1f} KB/s ↓{uso_rede.get('recebidos_kb', 0):.1f} KB/s"
                    )
                
                # Verificar condições críticas
                self._verificar_alertas(uso_cpu, uso_mem)
                
                # Aguardar próximo intervalo
                time.sleep(self.intervalo)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(self.intervalo)
    
    def _verificar_alertas(self, cpu, memoria):
        """
        Verifica condições críticas e gera alertas.
        
        Args:
            cpu (float): Percentual de uso da CPU
            memoria (float): Percentual de uso da memória
        """
        # Alerta para alto uso de CPU
        if cpu > 90:
            # Amostra sustentada? Verifique as últimas 3 medições
            if len(self.historico_cpu) >= 3 and all(c > 85 for c in list(self.historico_cpu)[-3:]):
                self.logger.warning(f"ALERTA: Uso sustentado de CPU elevado: {cpu:.1f}%")
        
        # Alerta para alto uso de memória
        if memoria > 90:
            self.logger.warning(f"ALERTA: Uso de memória crítico: {memoria:.1f}%")
    
    def obter_estatisticas(self):
        """
        Obtém estatísticas resumidas do período monitorado.
        
        Returns:
            dict: Estatísticas de uso de recursos
        """
        if not self.historico_cpu:
            return {"erro": "Sem dados de monitoramento disponíveis"}
        
        # Calcular médias
        media_cpu = sum(self.historico_cpu) / len(self.historico_cpu)
        media_mem = sum(m[0] for m in self.historico_memoria) / len(self.historico_memoria)
        media_mem_gb = sum(m[1] for m in self.historico_memoria) / len(self.historico_memoria)
        
        # Obter máximos
        max_cpu = max(self.historico_cpu)
        max_mem = max(m[0] for m in self.historico_memoria)
        max_mem_gb = max(m[1] for m in self.historico_memoria)
        
        # Calcular média de transferência de rede
        if self.historico_rede and 'enviados_kb' in self.historico_rede[0]:
            media_enviados_kb = sum(r.get('enviados_kb', 0) for r in self.historico_rede) / len(self.historico_rede)
            media_recebidos_kb = sum(r.get('recebidos_kb', 0) for r in self.historico_rede) / len(self.historico_rede)
        else:
            media_enviados_kb = media_recebidos_kb = 0
        
        # Montar estatísticas
        estatisticas = {
            "periodo": {
                "inicio": self.timestamps[0].strftime('%Y-%m-%d %H:%M:%S'),
                "fim": self.timestamps[-1].strftime('%Y-%m-%d %H:%M:%S'),
                "amostras": len(self.historico_cpu)
            },
            "cpu": {
                "media": round(media_cpu, 1),
                "max": round(max_cpu, 1)
            },
            "memoria": {
                "media_percentual": round(media_mem, 1),
                "max_percentual": round(max_mem, 1),
                "media_gb": round(media_mem_gb, 2),
                "max_gb": round(max_mem_gb, 2),
                "total_gb": round(self.info_sistema['memoria_total'], 2)
            },
            "rede": {
                "media_envio_kb": round(media_enviados_kb, 1),
                "media_recebimento_kb": round(media_recebidos_kb, 1)
            },
            "sistema": self.info_sistema
        }
        
        return estatisticas
    
    def exportar_relatorio(self, caminho_arquivo=None):
        """
        Exporta um relatório com as estatísticas de uso de recursos.
        
        Args:
            caminho_arquivo (str, optional): Caminho para salvar o relatório.
                Se None, gera um arquivo baseado na data/hora atual.
                
        Returns:
            str: Caminho do arquivo salvo
        """
        import json
        
        if not caminho_arquivo:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho_arquivo = f"logs/relatorio_recursos_{timestamp}.json"
        
        # Garantir que o diretório exista
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        
        # Obter estatísticas
        estatisticas = self.obter_estatisticas()
        
        # Salvar para arquivo
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(estatisticas, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Relatório de recursos exportado para: {caminho_arquivo}")
        return caminho_arquivo

# Exemplo de uso
if __name__ == "__main__":
    import time
    
    # Configurar logging para console também
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('monitor_recursos').addHandler(console)
    
    monitor = MonitorRecursos(intervalo_segundos=2)
    monitor.iniciar()
    
    try:
        print("Monitorando recursos do sistema. Pressione Ctrl+C para parar.")
        
        # Simular carga de CPU para teste
        for i in range(5):
            print(f"Simulando carga {i+1}/5...")
            for _ in range(1000000):
                _ = 2 ** 10000
            time.sleep(2)
        
        # Continuar monitorando
        time.sleep(10)
        
        # Exportar relatório
        relatorio = monitor.exportar_relatorio()
        print(f"Relatório salvo em: {relatorio}")
        
        # Mostrar estatísticas
        print("\nEstatísticas de uso:")
        estatisticas = monitor.obter_estatisticas()
        print(f"CPU média: {estatisticas['cpu']['media']}%")
        print(f"Memória média: {estatisticas['memoria']['media_percentual']}%")
        print(f"Memória média: {estatisticas['memoria']['media_gb']} GB")
        
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido pelo usuário.")
    finally:
        monitor.parar()
        print("Monitoramento finalizado.") 