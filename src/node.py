import json
import os
import socket
import threading
import time
import math


class Node:
    def __init__(self, id):
        self.id = id
        self.host = None
        self.port = None
        self.transfer_rate = None
        self.known_nodes = []

        self.chunks_found = {}

    def configure_node(self, host, port, transfer_rate):
        self.host = host
        self.port = port
        self.transfer_rate = transfer_rate

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

    def create_udp_socket(self, timeout):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.host, int(self.port)))
        server_socket.settimeout(timeout)
        print(f"Node {self.id} listening UDP in {self.host}:{self.port} for {timeout} seconds.")
        self.handle_udp_client(server_socket)

    def create_tcp_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, int(self.port)))
        server_socket.listen()
        print(f"Node {self.id} listening TCP on {self.host}:{self.port}")

        try:
            conn, addr = server_socket.accept()
            print(f"Connected TCP: {self.id} - {self.host}:{self.port} received connection from {addr}")
            self.handle_tcp_client(conn, addr)  # Chama a função para lidar com a conexão
        except socket.timeout:
            print(f"Node {self.id} exceeded time limit while waiting for TCP connection.")
        except Exception as e:
            print(f"Error while accepting connection: {e}")
        finally:
            server_socket.close()  # Fecha o socket após a conexão

    def handle_tcp_client(self, conn, addr):
        # Cria o diretório se não existir
        save_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        os.makedirs(save_directory, exist_ok=True)

        # Lê o nome do arquivo enviado pelo cliente
        file_name = conn.recv(1024).decode('utf-8').strip()  # Lê o nome do arquivo até a nova linha
        file_path = os.path.join(save_directory, file_name)  # Define o caminho do arquivo a ser salvo

        try:
            with conn:
                with open(file_path, 'wb') as file:  # Abre o arquivo em modo de escrita binária
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break  # Sai do loop se não houver mais dados
                        file.write(data)  # Escreve os dados recebidos no arquivo

            print(f"File {file_name} received and saved to {file_path}")
        except Exception as e:
            print(f"Error during file reception from {addr}: {e}")

    def handle_udp_client(self, server_socket):
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

                type = data_dict['TYPE_CLIENT']
                print(f"Node {self.id} received from {address} type of connection: {type}")

                if type == 'SEARCHING_FILE':
                    file_wanted = data_dict['FILE_WANTED']
                    sender_address = data_dict['ADDRESS']
                    original_address = data_dict['ORIGINAL_ADDRESS']
                    flooding = data_dict['FLOODING']

                    print(f"Address: {original_address}")
                    print(f"Remaining flooding: {flooding}")

                    matching_files = self.look_for_chunks(file_wanted)

                    # Caso matching_files seja uma lista não vazia, responder com a taxa de transferência
                    if matching_files:
                        message_sent = {
                            'type_client': 'found_file',
                            'file_wanted': file_wanted,
                            'files_found': matching_files,
                            'address': (self.host, self.port),
                            'transfer_rate': self.transfer_rate
                        }
                        message_json = json.dumps(message_sent)
                        self.create_udp_client(original_address[0], int(original_address[1]), message_json)

                    # Caso o flooding seja maior que 0, criar conexão UDP pra procurar nos known_nodes se tem aquele arquivo
                    if flooding > 0:
                        message_sent = {
                            'type_client': 'searching_file',
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
                                self.create_udp_client(node.host, node.port, message_json)
                    else:
                        print("Flooding ended.")

                elif type == 'FOUND_FILE':
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

                elif type == 'SEND_FILE':
                    file = data_dict['FILE']
                    transfer_rate =  data_dict['TRANSFER_RATE']

                    self.create_tcp_client(address[0], address[1], file, transfer_rate)
            
            except socket.timeout:
                print("Exceeded searching files time limit")

    def look_for_chunks(self, file_wanted):
        current_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        files_in_directory = os.listdir(current_directory)
        matching_files = [f for f in files_in_directory if f.startswith(file_wanted.lower())]
        return matching_files
    
    def transfer_file(self, file, transfer_node):
        threading.Thread(target=self.create_tcp_socket, args=()).start()
        
        # Informar ao nó que vai transferir, que a conexão TCP foi aberta
        message_sent = {
            'type_client': 'send_file',
            'file': file,
            'transfer_rate': transfer_node[1]
        }
        message_json = json.dumps(message_sent)
        self.create_udp_client(transfer_node[0][0], int(transfer_node[0][1]), message_json)

    def create_udp_client(self, other_host, other_port, message_sent):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5.0)

        max_attempts = 10
        start = time.time()
        
        # Tenta 10 vezes
        for pings in range(max_attempts):
            print(f'Ping {pings}: Host {self.id} - {self.host}:{self.port} sending message {message_sent} to {other_host}:{other_port}')
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

    def create_tcp_client(self, original_host, original_port, file_path, transfer_rate):
        # Cria o socket TCP do cliente
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((original_host, original_port))

        # Calcula o tempo de espera necessário para cada chunk de 1024 bytes
        chunk_size = 1024
        time_per_chunk = chunk_size / transfer_rate  # Tempo necessário para enviar cada chunk

        try:
            with open(file_path, 'rb') as file:
                while chunk := file.read(chunk_size):  # Lê o arquivo em blocos de 1024 bytes
                    client_socket.sendall(chunk)
                    print(f"Sent a chunk of {chunk_size} bytes to {original_host}:{original_port}")
                    time.sleep(time_per_chunk)  # Pausa para limitar a taxa de transferência

            print("File sent successfully")
        except IOError:
            print("Error reading the file.")
        except Exception as e:
            print(f"Error during file transmission: {e}")
        finally:
            client_socket.close()

    # Função para busca de chunks em uma thread separada
    def search_chunks(self, num_chunks_required):
        first_search = True
        print(f"Node {self.id} is starting to investigate received files")

        while True:
            print(f"Node {self.id} is waiting for files")
            if self.chunks_found:  # Só entra quando encontrar o primeiro arquivo
                if first_search:
                    print(f"Node {self.id} received first file and is waiting 10 seconds to decide")
                    time.sleep(10)  # Espera 10 segundos na primeira vez
                    first_search = False

                is_possible = True
                address_search = {}

                for part in range(num_chunks_required):
                    if (part in self.chunks_found):
                        for i, chunk_info in enumerate(self.chunks_found[part]):
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
                        if value[1] == math.inf:
                            print(f"Node {self.id} already had {key} previosly.")
                        else:
                            print(f"Searching file {key} in {value[0][0]}:{value[0][1]} with transfer rate {value[1]} bytes/s.")
                            self.transfer_file(key, value)
                else:
                    print("It was not possible to collect all file's chunks.")
            
            # Aguarda a chegada de novos arquivos para verificar novamente
            time.sleep(2)
