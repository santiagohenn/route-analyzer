import socket
import time
import threading
import random
import string
import os
from datetime import datetime

class UDPClient:
    def __init__(self, server_host='::1', server_port=12345,
                 client_host='::1', client_port=0, 
                 send_interval=1, total_packets=1000, 
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
        
        # Create storage directory if it doesn't exist
        if not os.path.exists('client_responses'):
            os.makedirs('client_responses')
    
    def generate_random_string(self, length):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def save_responses(self, force=False):
        with self.lock:
            if not self.responses:
                return
                
            if force or len(self.responses) >= self.batch_size:
                filename = f'client_responses/responses_{self.file_counter}.txt'
                line_count = 0
                
                # Check if current file exists and count lines
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        line_count = sum(1 for _ in f)
                
                # If current file would exceed max_lines, create new file
                if line_count + len(self.responses) > self.max_lines:
                    remaining_space = self.max_lines - line_count
                    self.file_counter += 1
                    filename = f'client_responses/responses_{self.file_counter}.txt'
                    
                    # Save remaining responses that fit in current file
                    if remaining_space > 0:
                        with open(f'client_responses/responses_{self.file_counter-1}.txt', 'a') as f:
                            for response in self.responses[:remaining_space]:
                                f.write(response + '\n')
                        self.responses = self.responses[remaining_space:]
                
                # Save responses to file
                with open(filename, 'a') as f:
                    for response in self.responses:
                        f.write(response + '\n')
                self.responses = []
    
    def listen_for_responses(self):

        self.response_sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.response_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.response_sock.bind((self.client_host, self.client_port))
        
        try:
            while self.running:
                try:
                    data, _ = self.response_sock.recvfrom(1024)
                    current_time = str(time.time_ns())

                    if not self.server_ack:
                        self.server_ack = True
                        print("Server responses incoming ... ")

                    modified_data = f"{data.decode('utf-8')}|{current_time}"
                    
                    with self.lock:
                        self.responses.append(modified_data)
                        if len(self.responses) >= self.batch_size:
                            threading.Thread(target=self.save_responses).start()
                except socket.error:
                    if self.running:
                        raise
        finally:
            self.response_sock.close()

    def send_packets(self):

        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.sock.bind(('::1', 0))

        print(f"Client sending from port {self.sock.getsockname()[1]}")

        try:
            for seq in range(1, self.total_packets + 1):
                if not self.running:
                    break
                    
                current_time = str(time.time_ns())
                random_str = self.generate_random_string(self.random_length)
                payload = f"{seq}|{current_time}|{random_str}"
                
                self.sock.sendto(payload.encode('utf-8'), (self.server_host, self.server_port))
                self.packets_sent += 1
                
                if seq % 100 == 0:
                    print(f"Sent {seq} packets")
                
                time.sleep(self.send_interval)
            
            # After sending all packets, wait for responses
            print(f"All packets sent. Waiting {self.response_timeout} seconds for responses...")
            time.sleep(self.response_timeout)
            self.running = False
            self.save_responses(force=True)
            print("Client finished.")
        finally:
            self.sock.close()
    
    def start(self):

        print("Sending packets to", self.server_host, "at port", self.server_port)

        # Start response listener thread
        threading.Thread(target=self.listen_for_responses, daemon=True).start()
        
        # Start sending packets
        self.send_packets()

if __name__ == "__main__":
    client = UDPClient(
        server_host='::1',  # IPv6 localhost
        server_port=12345,
        send_interval=100,  # 100ms between packets
        total_packets=500,  # Send 500 packets
        response_timeout=5,  # Wait 5 seconds after sending
        random_length=20,    # 20 random chars
        batch_size=100,      # Save every 100 responses
        max_lines=10000      # 10,000 lines per file
    )
    client.start()