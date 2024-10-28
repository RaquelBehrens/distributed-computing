import json
import os
import socket
import threading
import time
import math


class Node:
    def __init__(self, id, host, port, transfer_rate):
        self.id = id
        self.host = host
        self.port = port
        self.transfer_rate = transfer_rate
        self.known_nodes = []

        self.chunks_found = {}

    def add_known_node(self, known_nodes):
        self.known_nodes += known_nodes

    def configure_known_chunks(self, file_wanted):
        # Adicionar os chunks atuais na lista.
        current_files = self.look_for_chunks(file_wanted)
        for chunk in current_files:
            chunk_part = int(chunk[len(file_wanted)+3:])
            # Taxa de transferência infinita simbolizando que o arquivo está presente.
            new_chunk = [chunk.upper(), [self.host, self.port], math.inf]
            if chunk_part in self.chunks_found:
                if (new_chunk not in self.chunks_found[chunk_part]):
                    self.chunks_found[chunk_part].append(new_chunk)
            else:
                self.chunks_found[chunk_part] = [new_chunk]

    def create_udp_socket(self, timeout, num_chunks_required):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.host, int(self.port)))

        server_socket.settimeout(timeout)
        print(f"Node {self.id} listening UDP in {self.host}:{self.port} for {timeout} seconds.")

        self.handle_udp_client(server_socket, num_chunks_required)

    def handle_udp_client(self, server_socket, num_chunks_required):
        while True:
            try:
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
                            'file_wanted': file_wanted,
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
                    # print(f'Node {self.id}')
                    # print(data_dict)

                    # Tratamento dos arquivos/chunks recebidos
                    file_wanted = data_dict['FILE_WANTED']
                    files_found = data_dict['FILES_FOUND']
                    sender_address = data_dict['ADDRESS']
                    transfer_rate = data_dict['TRANSFER_RATE']

                    for chunk in files_found:
                        # Nome do arquivo + .ch
                        chunk_part = int(chunk[len(file_wanted)+3:])
                        new_chunk = [chunk, sender_address, float(transfer_rate)]
                        if chunk_part in self.chunks_found:
                            if (new_chunk not in self.chunks_found[chunk_part]):
                                self.chunks_found[chunk_part].append(new_chunk)
                        else:
                            self.chunks_found[chunk_part] = [new_chunk]
            
            except socket.timeout:
                # Ao encerrar o timeout, começa a decidir de quais nodos vai buscar o arquivo.
                is_possible = True
                address_search = {}
                if (self.chunks_found): # Trocar por comparação c/ endereço original
                    for part in range(num_chunks_required):
                        if (part in self.chunks_found):
                            for i, chunk_info in enumerate(self.chunks_found[part]):
                                # chunk_info = [arquivo, [ip, porta], taxa de transferência]
                                if (i == 0):
                                    best_option = i
                                    best_address = chunk_info[1]
                                    best_rate = chunk_info[2]
                                else:
                                    if (chunk_info[2] > best_rate):
                                        best_option = i
                                        best_address = chunk_info[1]
                                        best_rate = chunk_info[2]
                            address_search[self.chunks_found[part][best_option][0].lower()] = [best_address, best_rate]
                        else:
                            is_possible = False
                            break

                    if is_possible:
                        for key, value in address_search.items():
                            if (value[1] == math.inf):
                                print(f"Nodo {self.id} já possuia arquivo {key} previamente.")
                            else:
                                print(f"Busca de arquivo {key} em {value[0][0]}:{value[0][1]} com taxa de {value[1]} bytes/s.")
                    else:
                        print("Não foi possível coletar todos os chunks do arquivo.")

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
