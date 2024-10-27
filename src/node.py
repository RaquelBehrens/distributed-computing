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
        print(f"Node {self.id} listening UDP in {self.host}:{self.port}")
        # conn, addr = s.accept()
        # print(f"Connected by {addr}")

        # while True:
        #     message, address = socket.recvfrom(1024)
        #     message = message.upper()
        # threading.Thread(target=self.handle_udp_client, args=(server_socket, )).start()
        self.handle_udp_client(server_socket)

    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            message = message.upper()
            print(f"Node {self.id}, with {self.host}:{self.port}, received: {message!r} from {address}")

            # Envia confirmação de recebimento de mensagem ao sender
            ack_message = json.dumps({'status': 'received'})
            server_socket.sendto(ack_message.encode('utf-8'), address)

            # Converte os bytes para string
            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            try:
                file_wanted = data_dict['FILE_WANTED']
                sender_address = data_dict['ADDRESS']
                original_address = data_dict['ORIGINAL_ADDRESS']
                flooding = data_dict['FLOODING']

                print(f"Adress: {original_address}")
                print(f"Remaining flooding: {flooding}")

                matching_files = self.look_for_chunks(file_wanted)

                # Caso matching_files seja uma lista não vazia, responder com a taxa de transferência
                if matching_files:
                    message_sent = {
                        'files_found': matching_files,
                        'address': (self.host, self.port),
                        'transfer_rate': self.transfer_rate
                    }
                    message_json = json.dumps(message_sent)
                    self.create_client(original_address[0], int(original_address[1]), message_json)

                # Caso o flooding seja maior que 0, criar conexão UDP pra procurar nos known_nodes se tem aquele arquivo
                if flooding > 0:
                    message_sent = {
                        'file_wanted': file_wanted,
                        'address': (self.host, self.port),
                        'original_address': (original_address[0], original_address[1]),
                        'flooding': flooding-1
                    }
                    message_json = json.dumps(message_sent)

                    for node in self.known_nodes:
                        # Verifica se a requisição não está sendo feita para o nodo original ou para o nodo requisitor
                        if (node.host != original_address[0] or node.port != original_address[1]) and \
                            (node.host != sender_address[0] or node.port != sender_address[1]):
                            self.create_client(node.host, node.port, message_json)
                else:
                    print("Flooding encerrado.")

            except KeyError:
                # Tratamento dos arquivos recebidos!!!
                print(f'Node {self.id}')
                print(data_dict)
                pass

            # with conn:
            #     while True:
            #         data = conn.recv(1024)
            #         if not data:
            #             break
            #         print(f"Received: {data!r}")
            #         conn.sendall(data)


    def look_for_chunks(self, file_wanted):
        current_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        files_in_directory = os.listdir(current_directory)
        matching_files = [f for f in files_in_directory if f.startswith(file_wanted.lower())]
        return matching_files


    def create_client(self, other_host, other_port, message_sent):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5.0)

        max_attempts = 10
        start = time.time()
        
        # Tenta 10 vezes
        for pings in range(max_attempts):
            print(f'Ping {pings}: Host {self.id} - {self.host}:{self.port} sending message to {other_host}:{other_port}')
            client_socket.sendto(message_sent.encode('utf-8'), (other_host, int(other_port)))

            try:
                data, server = client_socket.recvfrom(1024)
                ack = json.loads(data.decode('utf-8'))
                if ack.get('status') == 'received':
                    print(f"Node {self.id} received confirmation from {server[0]}:{server[1]}")
                    break
            except socket.timeout:
                print(f'REQUEST TIMED OUT FOR CLIENT {self.id} - no acknowledgment received from {other_host}:{other_port}')    
            finally:
                if pings == max_attempts - 1:
                    print("Max attempts reached, no acknowledgment received.")

                end = time.time()
                elapsed = end - start
                print(f'Pings: {pings}, Elapsed: {elapsed}')

                client_socket.close()
                break
            
        
        # try:
        #     s.connect((other_host, int(other_port)))
        #     s.sendall(b"Hello, world")
        #     data = s.recv(1024)
        #     print(f"Received {data!r}")
        # except ConnectionRefusedError:
        #     print(f"Connection refused for {self.host}:{self.port}")
