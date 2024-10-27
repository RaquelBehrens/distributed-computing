import json
import os
import socket
import threading
import time


class Node:
    def __init__(self, id, host, port, transfer_rate):
        self.id = id
        self.host = host
        self.port = port
        self.transfer_rate = transfer_rate
        self.known_nodes = []

    def add_known_node(self, known_nodes):
        self.known_nodes += known_nodes

    def create_udp_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.host, int(self.port)))
        # s.listen()
        print(f"Node {self.id} listening in {self.host}:{self.port}")
        # conn, addr = s.accept()
        # print(f"Connected by {addr}")

        # while True:
        #     message, address = socket.recvfrom(1024)
        #     message = message.upper()
        threading.Thread(target=self.handle_udp_client, args=(server_socket, )).start()

    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            message = message.upper()
            print(f"Received: {message!r}")
            print(f"From: {address}")

            # Converte os bytes para string
            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            file_wanted = data_dict['FILE_WANTED']
            original_address = data_dict['ADDRES']
            flooding = data_dict['FLOODING']

            matching_files = self.look_for_chunks(file_wanted)

            # Caso matching_files seja uma lista não vazia, responder com a taxa de transferência
            if matching_files:
                message_sent = {
                    'files_found': matching_files,
                    'address': (self.host, self.port),
                    'transfer_rate': self.transfer_rate
                }
                message_json = json.dumps(message_sent)
                server_socket.sendto(message_json.encode('utf-8'), original_address)

            # Caso o flooding seja maior que 0, criar conexão UDP pra procurar nos known_nodes se tem aquele arquivo
            if flooding > 0:
                for node in self.known_nodes:
                    node.create_client(original_address.host, original_address.port, file_wanted, flooding-1)

            # with conn:
            #     while True:
            #         data = conn.recv(1024)
            #         if not data:
            #             break
            #         print(f"Received: {data!r}")
            #         conn.sendall(data)


    def look_for_chunks(self, file_wanted):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        files_in_directory = os.listdir(current_directory)
        matching_files = [f for f in files_in_directory if f.startswith(file_wanted)]
        return matching_files


    def create_client(self, other_host, other_port, file_wanted, flooding):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5.0)
        start = time.time()

        message_sent = {
            'file_wanted': file_wanted,
            'addres': (self.host, self.port),
            'flooding': flooding
        }
        message_json = json.dumps(message_sent)

        for pings in range(10):
            client_socket.sendto(message_json.encode('utf-8'), (other_host, int(other_port)))

            try:
                data, server = client_socket.recvfrom(1024)
                end = time.time()
                elapsed = end - start
                print(f'{data} {pings} {elapsed}')
                break
            except socket.timeout:
                print('REQUEST TIMED OUT')
            finally:
                client_socket.close()
        
            
        
        # try:
        #     s.connect((other_host, int(other_port)))
        #     s.sendall(b"Hello, world")
        #     data = s.recv(1024)
        #     print(f"Received {data!r}")
        # except ConnectionRefusedError:
        #     print(f"Connection refused for {self.host}:{self.port}")
