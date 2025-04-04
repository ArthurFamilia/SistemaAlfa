import os
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

# Inicializa o colorama para suportar cores no terminal
init(autoreset=True)

class Logger:
    """
    Classe responsável por gerenciar logs do bot de trading.
    
    Fornece métodos para exibir e salvar diferentes tipos de logs:
    - Mensagens informativas
    - Mensagens de erro
    - Dados de operações
    - Dados de mercado
    """
    
    def __init__(self, log_dir="logs"):
        """
        Inicializa o logger.
        
        Args:
            log_dir (str): Diretório onde os logs serão salvos
        """
        self.log_dir = log_dir
        self.operations = []
        self.market_data = []
        self.errors = []
        
        # Criar diretório de logs se não existir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Arquivos de log
        self.operations_file = os.path.join(log_dir, "operations.log")
        self.market_file = os.path.join(log_dir, "market_data.log")
        self.error_file = os.path.join(log_dir, "errors.log")
    
    def log_message(self, message):
        """
        Exibe uma mensagem informativa no terminal.
        
        Args:
            message (str): Mensagem a ser exibida
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.CYAN}[{timestamp}] {Fore.WHITE}{message}{Style.RESET_ALL}")
    
    def log_info(self, message):
        """
        Exibe uma mensagem informativa com destaque no terminal.
        
        Args:
            message (str): Mensagem informativa a ser exibida
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.BLUE}[{timestamp}] INFO: {Fore.WHITE}{message}{Style.RESET_ALL}")
    
    def log_warning(self, message):
        """
        Exibe uma mensagem de aviso com destaque amarelo no terminal.
        
        Args:
            message (str): Mensagem de aviso a ser exibida
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.YELLOW}[{timestamp}] WARNING: {Fore.WHITE}{message}{Style.RESET_ALL}")
    
    def log_error(self, error_message):
        """
        Exibe e registra uma mensagem de erro.
        
        Args:
            error_message (str): Mensagem de erro a ser exibida e registrada
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_log = {
            "timestamp": timestamp,
            "error": error_message
        }
        
        # Exibe no terminal
        print(f"{Fore.RED}[{timestamp}] ERROR: {Fore.WHITE}{error_message}{Style.RESET_ALL}")
        
        # Adiciona à lista de erros
        self.errors.append(error_log)
        
        # Salva no arquivo de log
        try:
            with open(self.error_file, "a") as f:
                f.write(json.dumps(error_log) + "\n")
        except Exception as e:
            print(f"{Fore.RED}Falha ao salvar log de erro: {str(e)}{Style.RESET_ALL}")
    
    def log_operation(self, operation_data):
        """
        Registra dados de uma operação de trading.
        
        Args:
            operation_data (dict): Dados da operação a serem registrados
        """
        # Adiciona timestamp se não existir
        if "timestamp" not in operation_data:
            operation_data["timestamp"] = datetime.now().isoformat()
            
        # Adiciona à lista de operações
        self.operations.append(operation_data)
        
        # Salva no arquivo de log
        try:
            with open(self.operations_file, "a") as f:
                f.write(json.dumps(operation_data) + "\n")
        except Exception as e:
            print(f"{Fore.RED}Falha ao salvar log de operação: {str(e)}{Style.RESET_ALL}")
    
    def log_market_data(self, data):
        """
        Exibe e registra dados de mercado.
        
        Args:
            data (dict): Dados de mercado a serem exibidos e registrados
        """
        # Extrair os valores do dicionário (com valores padrão caso estejam ausentes)
        adx = data.get('adx', 'N/A')
        di_plus = data.get('di_plus', 'N/A')
        di_minus = data.get('di_minus', 'N/A')
        atr = data.get('atr', 'N/A')
        bid_price = data.get('bid_price', 'N/A')
        ask_price = data.get('ask_price', 'N/A')
        volume_24h = data.get('volume_24h', 'N/A')
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Formatar o valor do ADX com cor baseada no valor
        if isinstance(adx, (int, float)):
            if float(adx) >= 20:
                adx_formatted = f"{Fore.GREEN}{adx:.2f}{Style.RESET_ALL}"
            else:
                adx_formatted = f"{Fore.RED}{adx:.2f}{Style.RESET_ALL}"
        else:
            adx_formatted = f"{Fore.WHITE}N/A{Style.RESET_ALL}"
        
        # Determinar a tendência baseada em DI+ e DI-
        if isinstance(di_plus, (int, float)) and isinstance(di_minus, (int, float)):
            if float(di_plus) > float(di_minus):
                trend = f"{Fore.GREEN}BULLISH{Style.RESET_ALL}"
            elif float(di_minus) > float(di_plus):
                trend = f"{Fore.RED}BEARISH{Style.RESET_ALL}"
            else:
                trend = f"{Fore.YELLOW}LATERAL{Style.RESET_ALL}"
        else:
            trend = f"{Fore.WHITE}UNDEFINED{Style.RESET_ALL}"
        
        # Formatar valores dos indicadores para evitar erros de formatação
        di_plus_formatted = f"{di_plus:.2f}" if isinstance(di_plus, (int, float)) else 'N/A'
        di_minus_formatted = f"{di_minus:.2f}" if isinstance(di_minus, (int, float)) else 'N/A'
        atr_formatted = f"{atr:.5f}" if isinstance(atr, (int, float)) else 'N/A'
        bid_formatted = f"{bid_price:.5f}" if isinstance(bid_price, (int, float)) else 'N/A'
        ask_formatted = f"{ask_price:.5f}" if isinstance(ask_price, (int, float)) else 'N/A'
        
        # Calcular o spread
        if isinstance(bid_price, (int, float)) and isinstance(ask_price, (int, float)):
            spread = float(ask_price) - float(bid_price)
            spread_pct = (spread / float(bid_price)) * 100
            spread_formatted = f"{spread:.5f} ({spread_pct:.3f}%)"
        else:
            spread_formatted = "N/A"
        
        # Preparar strings formatadas para exibição
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Exibir os dados no terminal
        print(f"\n{Fore.CYAN}======== DADOS DE MERCADO {symbol} @ {timestamp} ========{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}ADX: {adx_formatted} | Tendência: {trend} | Volume: {Fore.YELLOW}{volume_24h}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}DI+: {Fore.GREEN if isinstance(di_plus, (int, float)) else Fore.WHITE}{di_plus_formatted} | " + 
              f"DI-: {Fore.RED if isinstance(di_minus, (int, float)) else Fore.WHITE}{di_minus_formatted} | " + 
              f"ATR: {Fore.YELLOW if isinstance(atr, (int, float)) else Fore.WHITE}{atr_formatted}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Bid: {Fore.RED if isinstance(bid_price, (int, float)) else Fore.WHITE}{bid_formatted} | " + 
              f"Ask: {Fore.GREEN if isinstance(ask_price, (int, float)) else Fore.WHITE}{ask_formatted} | " + 
              f"Spread: {Fore.YELLOW}{spread_formatted}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}==============================================={Style.RESET_ALL}")
        
        # Adicionar à lista de dados de mercado
        self.market_data.append(data)
        
        # Salvar no arquivo de log
        try:
            with open(self.market_file, "a") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            print(f"{Fore.RED}Falha ao salvar log de dados de mercado: {str(e)}{Style.RESET_ALL}")
    
    def save_all_logs(self):
        """Força o salvamento de todos os logs pendentes."""
        try:
            # Salvar operações
            with open(self.operations_file, "w") as f:
                for operation in self.operations:
                    f.write(json.dumps(operation) + "\n")
            
            # Salvar dados de mercado
            with open(self.market_file, "w") as f:
                for market_data in self.market_data:
                    f.write(json.dumps(market_data) + "\n")
            
            # Salvar erros
            with open(self.error_file, "w") as f:
                for error in self.errors:
                    f.write(json.dumps(error) + "\n")
                    
            self.log_info("Todos os logs foram salvos com sucesso")
            
        except Exception as e:
            print(f"{Fore.RED}Falha ao salvar logs: {str(e)}{Style.RESET_ALL}")
            
    def clear_logs(self):
        """Limpa todos os logs em memória (não afeta arquivos)."""
        self.operations = []
        self.market_data = []
        self.errors = []
        self.log_info("Logs em memória foram limpos")

    def log_network_stats(self, stats):
        """
        Exibe e registra estatísticas de rede (latência e ping).
        
        Args:
            stats (dict): Estatísticas de rede a serem exibidas e registradas.
                          Deve conter as chaves 'latencia' e 'ping'.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Adicionar timestamp ao dicionário
        stats['timestamp'] = timestamp
        
        # Extrair valores do dicionário
        latencia = stats.get('latencia', {})
        ping = stats.get('ping', {})
        
        # Exibir no terminal
        print(f"\n{Fore.CYAN}======== ESTATÍSTICAS DE REDE @ {datetime.now().strftime('%H:%M:%S')} ========{Style.RESET_ALL}")
        
        # Latência
        lat_min = latencia.get('min', 0)
        lat_max = latencia.get('max', 0)
        lat_media = latencia.get('media', 0)
        lat_amostras = latencia.get('amostras', 0)
        
        print(f"{Fore.MAGENTA}LATÊNCIA:{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Mínima:{Style.RESET_ALL} {lat_min:.2f} ms")
        print(f"  {Fore.YELLOW}Máxima:{Style.RESET_ALL} {lat_max:.2f} ms")
        print(f"  {Fore.YELLOW}Média:{Style.RESET_ALL} {lat_media:.2f} ms")
        print(f"  {Fore.YELLOW}Amostras:{Style.RESET_ALL} {lat_amostras}")
        
        # Ping
        ping_min = ping.get('min', 0)
        ping_max = ping.get('max', 0)
        ping_media = ping.get('media', 0)
        ping_amostras = ping.get('amostras', 0)
        
        print(f"{Fore.MAGENTA}PING:{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Mínimo:{Style.RESET_ALL} {ping_min:.2f} ms")
        print(f"  {Fore.YELLOW}Máximo:{Style.RESET_ALL} {ping_max:.2f} ms")
        print(f"  {Fore.YELLOW}Médio:{Style.RESET_ALL} {ping_media:.2f} ms")
        print(f"  {Fore.YELLOW}Amostras:{Style.RESET_ALL} {ping_amostras}")
        
        # Classificar desempenho
        if lat_media < 50:
            lat_status = f"{Fore.GREEN}EXCELENTE{Style.RESET_ALL}"
        elif lat_media < 100:
            lat_status = f"{Fore.BLUE}BOM{Style.RESET_ALL}"
        elif lat_media < 200:
            lat_status = f"{Fore.YELLOW}ACEITÁVEL{Style.RESET_ALL}"
        else:
            lat_status = f"{Fore.RED}RUIM{Style.RESET_ALL}"
            
        print(f"{Fore.MAGENTA}STATUS DE REDE:{Style.RESET_ALL} {lat_status}")
        print(f"{Fore.CYAN}==============================================={Style.RESET_ALL}")
        
        # Salvar em arquivo de log dedicado
        network_file = os.path.join(self.log_dir, "network_stats.log")
        try:
            with open(network_file, "a") as f:
                f.write(json.dumps(stats) + "\n")
        except Exception as e:
            print(f"{Fore.RED}Falha ao salvar estatísticas de rede: {str(e)}{Style.RESET_ALL}")
        
        return stats 