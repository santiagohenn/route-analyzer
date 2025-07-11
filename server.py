import socket
import time
import threading
import os
import re
import json
from datetime import datetime
import argparse
import configparser

class UDPServer:
    def __init__(self, host='::', port=12345, timeout=30, batch_size=100, max_lines=10000):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.batch_size = batch_size
        self.max_lines = max_lines
        self.packets = []
        self.file_counter = 1
        self.last_received_time = time.time_ns()
        self.lock = threading.Lock()
        self.running = True
        self.received_something = False
        self.total_packets = 0

        # Create storage directory if it doesn't exist
        base_dir = 'results_server'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # Find next experiment number
        exp_dirs = [d for d in os.listdir(base_dir) if re.match(r'exp_\d+$', d)]
        exp_nums = [int(d.split('_')[1]) for d in exp_dirs]
        next_exp = max(exp_nums, default=0) + 1
        self.exp_dir = os.path.join(base_dir, f'exp_{next_exp}')
        os.makedirs(self.exp_dir)

        # Log server configuration to JSON
        self.config_dict = {
            "host": self.host,
            "port": self.port,
            "timeout": self.timeout,
            "batch_size": self.batch_size,
            "max_lines": self.max_lines,
            "experiment_starts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.config_path = os.path.join(self.exp_dir, "server_config.json")
        with open(self.config_path, "w") as f:
            json.dump(self.config_dict, f, indent=4)

        # Start timeout checker
        threading.Thread(target=self.check_timeout, daemon=True).start()

    def check_timeout(self):
        while self.running:
            if time.time() - self.last_received_time > self.timeout:
                print("Timeout exit [ I heard no one in a while :( ]")
                self.save_packets(force=True)
                self.running = False
                # Log experiment end time
                self.config_dict["experiment_ends"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.config_path, "w") as f:
                    json.dump(self.config_dict, f, indent=4)
                os._exit(0)
            time.sleep(1)

    def save_packets(self, force=False):
        with self.lock:
            if not self.packets:
                return

            if force or len(self.packets) >= self.batch_size:
                print("Still receiving packets. Current packet count:", self.total_packets)
                filename = os.path.join(self.exp_dir, f'packets_{self.file_counter}.psv')
                line_count = 0

                # Check if current file exists and count lines
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        line_count = sum(1 for _ in f)

                # If current file would exceed max_lines, create new file
                if line_count + len(self.packets) > self.max_lines:
                    remaining_space = self.max_lines - line_count
                    self.file_counter += 1
                    filename = os.path.join(self.exp_dir, f'packets_{self.file_counter}.psv')

                    # Save remaining packets that fit in current file
                    if remaining_space > 0:
                        with open(os.path.join(self.exp_dir, f'packets_{self.file_counter-1}.psv'), 'a') as f:
                            for packet in self.packets[:remaining_space]:
                                f.write(packet + '\n')
                        self.packets = self.packets[remaining_space:]

                # Save packets to file
                with open(filename, 'a') as f:
                    for packet in self.packets:
                        f.write(packet + '\n')
                self.packets = []

    def handle_packet(self, data, addr):
        current_time = str(time.time_ns())
        self.total_packets += 1
        client_host = addr[0]
        client_port = addr[1]

        if not self.received_something:
            self.received_something = True
            print("Packets incoming!")

        modified_data = f"{data.decode('utf-8')}|{current_time}"

        # Send response back to the same client port
        response_addr = (client_host, client_port, 0, 0)
        self.sock.sendto(modified_data.encode('utf-8'), response_addr)

        # Store the packet
        with self.lock:
            self.packets.append(modified_data)
            self.last_received_time = time.time()

            if len(self.packets) >= self.batch_size:
                threading.Thread(target=self.save_packets).start()

    def start(self):
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.sock.bind((self.host, self.port))
        print(f"Server listening on [{self.host}]:{self.port}")

        try:
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    threading.Thread(target=self.handle_packet, args=(data, addr)).start()
                except socket.error:
                    if self.running:
                        raise
        except KeyboardInterrupt:
            print("Server shutting down...")
            self.running = False
            self.save_packets(force=True)
            # Log experiment end time
            self.config_dict["experiment_ends"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.config_path, "w") as f:
                json.dump(self.config_dict, f, indent=4)
        finally:
            self.sock.close()

def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    cfg = {}
    if 'server' in config:
        s = config['server']
        if 'host' in s: cfg['host'] = s['host']
        if 'port' in s: cfg['port'] = int(s['port'])
        if 'timeout' in s: cfg['timeout'] = int(s['timeout'])
        if 'batch_size' in s: cfg['batch_size'] = int(s['batch_size'])
        if 'max_lines' in s: cfg['max_lines'] = int(s['max_lines'])
    return cfg

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Server")
    parser.add_argument('--config', type=str, help='Path to config file (INI format)')
    parser.add_argument('--host', type=str, help='Host/IP to bind')
    parser.add_argument('--port', type=int, help='Port to bind')
    parser.add_argument('--timeout', type=int, help='Timeout in seconds')
    parser.add_argument('--batch-size', type=int, help='Batch size for saving packets')
    parser.add_argument('--max-lines', type=int, help='Max lines per file')
    args = parser.parse_args()

    config = {}
    if args.config:
        config = load_config(args.config)

    # Command-line args override config file
    host = args.host or config.get('host', '::')
    port = args.port or config.get('port', 2222)
    timeout = args.timeout or config.get('timeout', 60)
    batch_size = args.batch_size or config.get('batch_size', 100)
    max_lines = args.max_lines or config.get('max_lines', 10000)

    server = UDPServer(
        host=host,
        port=port,
        timeout=timeout,
        batch_size=batch_size,
        max_lines=max_lines
    )
    server.start()