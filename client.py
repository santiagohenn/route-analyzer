import socket
import time
import threading
import random
import string
import os
import re
import json
from datetime import datetime
import argparse
import configparser

class UDPClient:
    def __init__(self, server_host='::1', server_port=12345,
                 client_host='::', client_port=0, 
                 send_interval=1000, total_packets=1000, 
                 response_timeout=10, random_length=10,
                 batch_size=100, max_lines=10000):
        self.server_host = server_host
        self.server_port = server_port
        self.client_host = client_host
        self.client_port = client_port
        self.send_interval = send_interval / 1000  # convert ms to seconds
        self.total_packets = total_packets
        self.response_timeout = response_timeout
        self.random_length = random_length
        self.batch_size = batch_size
        self.max_lines = max_lines
        self.responses = []
        self.file_counter = 1
        self.packets_sent = 0
        self.lock = threading.Lock()
        self.running = True
        self.server_ack = False
        self.first_run = True

        # Create storage directory if it doesn't exist
        base_dir = 'results_client'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # Find next experiment number
        exp_dirs = [d for d in os.listdir(base_dir) if re.match(r'exp_\d+$', d)]
        exp_nums = [int(d.split('_')[1]) for d in exp_dirs]
        next_exp = max(exp_nums, default=0) + 1
        self.exp_dir = os.path.join(base_dir, f'exp_{next_exp}')
        os.makedirs(self.exp_dir)

        # Log client configuration to JSON
        self.config_dict = {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "client_host": self.client_host,
            "client_port": self.client_port,
            "send_interval_ms": int(send_interval),
            "total_packets": self.total_packets,
            "response_timeout": self.response_timeout,
            "random_length": self.random_length,
            "batch_size": self.batch_size,
            "max_lines": self.max_lines,
            "experiment_starts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.config_path = os.path.join(self.exp_dir, "client_config.json")
        with open(self.config_path, "w") as f:
            json.dump(self.config_dict, f, indent=4)

        # Create a single socket for both sending and receiving
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.sock.bind((self.client_host, self.client_port))
        self.client_port = self.sock.getsockname()[1]  # update to actual port

    def generate_random_string(self, length):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def save_responses(self, force=False):
        with self.lock:
            if not self.responses:
                return
            
            # If first run, start a new file
            if self.first_run:
                self.first_run = False
                filename = os.path.join(self.exp_dir, f'series_{self.file_counter}.csv')
                while os.path.exists(filename):
                    self.file_counter += 1
                    filename = os.path.join(self.exp_dir, f'series_{self.file_counter}.csv')
                
            if force or len(self.responses) >= self.batch_size:
                filename = os.path.join(self.exp_dir, f'series_{self.file_counter}.csv')
                line_count = 0
                
                # Check if current file exists and count lines
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        line_count = sum(1 for _ in f)
                
                # If current file would exceed max_lines or its the first run, create new file
                if line_count + len(self.responses) > self.max_lines:
                    remaining_space = self.max_lines - line_count
                    self.file_counter += 1
                    filename = os.path.join(self.exp_dir, f'series_{self.file_counter}.csv')
                    
                    # Save remaining responses that fit in current file
                    if remaining_space > 0:
                        with open(os.path.join(self.exp_dir, f'series_{self.file_counter-1}.csv'), 'a') as f:
                            for response in self.responses[:remaining_space]:
                                f.write(response + '\n')
                        self.responses = self.responses[remaining_space:]
                
                # Save responses to file
                with open(filename, 'a') as f:
                    for response in self.responses:
                        f.write(response + '\n')
                self.responses = []
    
    def listen_for_responses(self):
        try:
            while self.running:
                try:
                    data, _ = self.sock.recvfrom(1024)
                    current_time = str(time.time_ns())

                    if not self.server_ack:
                        self.server_ack = True
                        print("Server responses incoming ... ")

                    modified_data = f"{data.decode('utf-8')}|{current_time}"
                    modified_data = modified_data.replace('|', ",")  # Replace '|' with ',' for CSV format
                    
                    with self.lock:
                        self.responses.append(modified_data)
                        if len(self.responses) >= self.batch_size:
                            threading.Thread(target=self.save_responses).start()
                except socket.error:
                    if self.running:
                        raise
        finally:
            self.sock.close()

    def send_packets(self):
        print(f"Client sending from port {self.client_port}")

        try:
            for seq in range(1, self.total_packets + 1):
                if not self.running:
                    break
                    
                random_str = self.generate_random_string(self.random_length)

                # Get time just before assembling the packet
                current_time = str(time.time_ns())
                payload = f"{seq}|{current_time}|{random_str}"
                
                self.sock.sendto(payload.encode('utf-8'), (self.server_host, self.server_port))
                self.packets_sent += 1
                
                if seq % 500 == 0:
                    print(f"Sent {seq} packets")
                
                time.sleep(self.send_interval)
            
            # After sending all packets, wait for responses
            print(f"All packets sent. Waiting {self.response_timeout} seconds for responses...")
            time.sleep(self.response_timeout)
            self.running = False
            self.save_responses(force=True)
            # Log experiment end time
            self.config_dict["experiment_ends"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.config_path, "w") as f:
                json.dump(self.config_dict, f, indent=4)
            print("Client finished.")
        finally:
            self.sock.close()
    
    def start(self):

        print("Sending packets to", self.server_host, "at port", self.server_port)

        # Start response listener thread
        threading.Thread(target=self.listen_for_responses, daemon=True).start()
        
        # Start sending packets
        self.send_packets()

def load_config(config_file, section):
    config = configparser.ConfigParser()
    config.read(config_file)
    cfg = {}
    if section in config:
        s = config[section]
        if 'server_host' in s: cfg['server_host'] = s['server_host']
        if 'server_port' in s: cfg['server_port'] = int(s['server_port'])
        if 'send_interval_ms' in s: cfg['send_interval_ms'] = int(s['send_interval_ms'])
        if 'total_packets' in s: cfg['total_packets'] = int(s['total_packets'])
        if 'response_timeout' in s: cfg['response_timeout'] = int(s['response_timeout'])
        if 'random_length' in s: cfg['random_length'] = int(s['random_length'])
        if 'batch_size' in s: cfg['batch_size'] = int(s['batch_size'])
        if 'max_lines' in s: cfg['max_lines'] = int(s['max_lines'])
    return cfg

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Client")
    parser.add_argument('--config', type=str, help='Path to config file (INI format)')
    parser.add_argument('--server-host', type=str, help='Server host/IP')
    parser.add_argument('--server-port', type=int, help='Server port')
    parser.add_argument('--send-interval', type=int, help='Interval between packets (ms)')
    parser.add_argument('--total-packets', type=int, help='Total packets to send')
    parser.add_argument('--response-timeout', type=int, help='Wait time for responses (s)')
    parser.add_argument('--random-length', type=int, help='Random string length')
    parser.add_argument('--batch-size', type=int, help='Batch size for saving responses')
    parser.add_argument('--max-lines', type=int, help='Max lines per file')
    args = parser.parse_args()

    config = {}
    if args.config:
        config = load_config(args.config, 'client')

    # Command-line args override config file
    server_host = args.server_host or config.get('server_host', '::1')
    server_port = args.server_port or config.get('server_port', 2222)
    send_interval = args.send_interval or config.get('send_interval_ms', 100)
    total_packets = args.total_packets or config.get('total_packets', 500)
    response_timeout = args.response_timeout or config.get('response_timeout', 5)
    random_length = args.random_length or config.get('random_length', 20)
    batch_size = args.batch_size or config.get('batch_size', 100)
    max_lines = args.max_lines or config.get('max_lines', 10000)

    client = UDPClient(
        server_host=server_host,
        server_port=server_port,
        send_interval=send_interval,
        total_packets=total_packets,
        response_timeout=response_timeout,
        random_length=random_length,
        batch_size=batch_size,
        max_lines=max_lines
    )
    client.start()