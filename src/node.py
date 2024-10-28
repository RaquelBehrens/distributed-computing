import json
import os
import socket
import time
import math
import re

PRINT_LOGS = False; MAX_REQ_RECV = 1024; TIMEOUT = 120

class Node:
    def __init__(self, id):
        self.id = id
        self.host = None
        self.port = None
        self.transfer_rate = None
        self.known_nodes = []
        self.chunks_found = {}
        self.transfered_files = 0

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

    def create_udp_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.host, int(self.port)))
        PRINT_LOGS and print(f"Node {self.id} listening UDP in {self.host}:{self.port}.")
        self.handle_udp_client(server_socket)

    def create_tcp_socket(self, file):
        timeout = 15
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, int(self.port)))
        server_socket.listen()
        server_socket.settimeout(timeout)
        PRINT_LOGS and print(f"Node {self.id} listening TCP on {self.host}:{self.port} for {timeout} seconds")

        try:
            PRINT_LOGS and print(f"Node {self.id} TCP is waiting for connection")
            conn, addr = server_socket.accept()
            PRINT_LOGS and print(f"Connected TCP: {self.id} - {self.host}:{self.port} received connection from {addr}")
            self.handle_tcp_client(conn, addr, file)  # Chama a função para lidar com a conexão
            server_socket.close()  # Fecha o socket após a conexão
        except socket.timeout:
            PRINT_LOGS and print(f"Node {self.id} exceeded time limit while waiting for TCP connection.")
        except Exception as e:
            PRINT_LOGS and print(f"Error while accepting connection: {e}")

    def handle_tcp_client(self, conn, addr, file_path):
        # Cria o diretório se não existir
        save_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        os.makedirs(save_directory, exist_ok=True)
        full_file_path = os.path.join(save_directory, file_path)

        try:
            with conn:
                PRINT_LOGS and print(f"Node {self.id} TCP received connection")
                with open(full_file_path, 'wb') as file:  # Abre o arquivo em modo de escrita binária
                    while True:
                        data = conn.recv(MAX_REQ_RECV)
                        if not data:
                            break  # Sai do loop se não houver mais dados
                        file.write(data)  # Escreve os dados recebidos no arquivo

            self.transfered_files += 1
            PRINT_LOGS and print(f"File received and saved to {full_file_path}")
        except Exception as e:
            PRINT_LOGS and print(f"Error during file reception from {addr}: {e}")

    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            message = message.upper()
            PRINT_LOGS and print(f"Node {self.id}, with {self.host}:{self.port}, received: {message!r} from {address}")

            # Envia confirmação de recebimento de mensagem ao sender
            ack_message = json.dumps({'status': 'received'})
            server_socket.sendto(ack_message.encode('utf-8'), address)

            # Converte os bytes para string
            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            type = data_dict['TYPE_CLIENT']
            PRINT_LOGS and print(f"Node {self.id} received from {address} type of connection: {type}")

            if type == 'SEARCHING_FILE':
                file_wanted = data_dict['FILE_WANTED']
                sender_address = data_dict['ADDRESS']
                original_address = data_dict['ORIGINAL_ADDRESS']
                flooding = data_dict['FLOODING']

                PRINT_LOGS and print(f"Address: {original_address}")
                PRINT_LOGS and print(f"Remaining flooding: {flooding}")

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
                    PRINT_LOGS and print(f"Node {self.id} is sending files found {matching_files} to {original_address[0]}:{original_address[1]}")
                    time.sleep(1) # Para efeito da simulação, cada nodo que for transmitir uma mensagem de descoberta de arquivo deve atrasar a retransmissão em 1s
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
                            PRINT_LOGS and print(f"Node {self.id} is sending search to {node.host}:{node.port}")
                            self.create_udp_client(node.host, node.port, message_json)
                else:
                    PRINT_LOGS and print("Flooding ended.")

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
                sender_address = data_dict['ADDRESS']
                
                max_attempts = 10
                start = time.time()
                
                # Tenta conexão com o socket TCP 10 vezes, pois pode ser que o socket ainda não esteja aberto
                for pings in range(max_attempts):
                    PRINT_LOGS and print(f"TRYING TO CONNECT TO TCP Ping {pings}: Node {self.id} is creating TCP client to {sender_address}")
                    try:
                        self.create_tcp_client(sender_address[0], sender_address[1], file)
                        break
                    except ConnectionRefusedError as e:
                        PRINT_LOGS and print(f"TCP Connection refused between node {self.id} and {sender_address[0]}:{sender_address[1]}: {e}")
                        if pings == max_attempts - 1:
                            PRINT_LOGS and print("Max attempts reached, no acknowledgment received.")

                            end = time.time()
                            elapsed = end - start
                            PRINT_LOGS and print(f'TRYING TO CONNECT TO TCP Pings: {pings}, Elapsed: {elapsed}')
                            break


    def look_for_chunks(self, file_wanted):
        current_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        files_in_directory = os.listdir(current_directory)

        # Expressão regular para verificar se o arquivo termina com .ch seguido de um número
        pattern = re.compile(rf"^{file_wanted.lower()}\.ch\d+$")
        
        matching_files = [f for f in files_in_directory if pattern.match(f.lower())]
        return matching_files
        
    def transfer_file(self, file, transfer_node):        
        # Informar ao nó que vai transferir, que a conexão TCP foi aberta
        message_sent = {
            'type_client': 'send_file',
            'address': (self.host, self.port),
            'file': file
        }
        message_json = json.dumps(message_sent)
        self.create_udp_client(transfer_node[0][0], int(transfer_node[0][1]), message_json)

        try:
            #Criar conexão tcp que espera o arquivo
            self.create_tcp_socket(file)
        except OSError as e:
            print(f"ERRO: {e}")
            print(f"Encerre esse terminal, abra outro, e tente novamente.")

    def create_udp_client(self, other_host, other_port, message_sent):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5.0)

        max_attempts = 5
        start = time.time()
        
        # Tenta 5 vezes enviar mensagem ao socket UDP
        for pings in range(max_attempts):
            PRINT_LOGS and print(f'TRYING TO SEND UDP Ping {pings}: Host {self.id} - {self.host}:{self.port} sending message {message_sent} to {other_host}:{other_port}')
            client_socket.sendto(message_sent.encode('utf-8'), (other_host, int(other_port)))

            try:
                data, server = client_socket.recvfrom(1024)
                ack = json.loads(data.decode('utf-8'))
                if ack.get('status') == 'received':
                    PRINT_LOGS and print(f"Node {self.id} received confirmation from {server[0]}:{server[1]}")
                    break
            except socket.timeout:
                PRINT_LOGS and print(f'REQUEST TIMED OUT FOR CLIENT {self.id} - no acknowledgment received from {other_host}:{other_port}')    
            
        if pings == max_attempts - 1:
            PRINT_LOGS and print("Max attempts reached, no acknowledgment received.")

        end = time.time()
        elapsed = end - start
        PRINT_LOGS and print(f'Pings: {pings}, Elapsed: {elapsed}')

        client_socket.close()

    def create_tcp_client(self, original_host, original_port, file_name):
        # Cria o socket TCP do cliente
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        PRINT_LOGS and print(f"Node {self.id} is trying to connect to TCP {original_host}:{original_port}")
        client_socket.connect((original_host, int(original_port)))
        PRINT_LOGS and print(f"Node {self.id} connected to TCP {original_host}:{original_port}")

        # Define diretório do arquivo
        save_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        file_path = os.path.join(save_directory, file_name.lower())

        # Calcula o tempo de espera necessário para cada chunk de chunk_size bytes
        chunk_size = int(self.transfer_rate)
        time_per_chunk = chunk_size / int(self.transfer_rate)  # Tempo necessário para enviar cada chunk

        PRINT_LOGS and print(f"Node {self.id} will try to send chunks")
        try:
            PRINT_LOGS and print(f"Node {self.id} is opening file {file_path}")
            with open(file_path, 'rb') as file:
                PRINT_LOGS and print(f"Node {self.id} is reading file {file_path}")
                total_size = os.path.getsize(file_path)
                current_size = chunk_size
                while chunk := file.read(chunk_size):  # Lê o arquivo em blocos de chunk_size bytes
                    PRINT_LOGS and  print(f"Node {self.id} sent a chunk of {chunk_size} bytes to {original_host}:{original_port}")
                    print(f"Chunk {file_name} {current_size*100/total_size:.2f}% transferred.")
                    client_socket.sendall(chunk)
                    time.sleep(time_per_chunk)  # Pausa para limitar a taxa de transferência

                    if (current_size+chunk_size <= total_size):
                        current_size += chunk_size
                    else:
                        current_size = total_size 

            PRINT_LOGS and print("File sent successfully")
        except IOError as e:
            PRINT_LOGS and print(f"Error reading the file: {e}")
        except Exception as e:
            PRINT_LOGS and print(f"Error during file transmission: {e}")
        finally:
            client_socket.close()

    # Função para busca de chunks em uma thread separada
    def search_chunks(self, num_chunks_required, file_wanted, timeout=TIMEOUT):
        start_time = time.time()
        first_search = True
        PRINT_LOGS and print(f"Node {self.id} is starting to investigate received files")
        PRINT_LOGS and print(f"Node {self.id} is waiting for files")

        result_timeout = False

        while len(self.look_for_chunks(file_wanted)) < num_chunks_required:
            # Verifica se o tempo decorrido excedeu o timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                PRINT_LOGS and print(f"Timeout reached. Node {self.id} stopped searching.")
                result_timeout = True
                break

            if self.chunks_found:  # Só entra quando encontrar o primeiro arquivo
                if first_search:
                    PRINT_LOGS and print(f"Node {self.id} received first file and is waiting 10 seconds to decide")
                    time.sleep(10)  # Espera 10 segundos na primeira vez
                    first_search = False

                is_possible = True
                address_search = {}

                # Decide qual chunk de qual endereço a melhor opção
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
                    PRINT_LOGS and print(address_search.items())
                    print(f"PERCENTAGE OF THE FILE ALREADY TRANSFERRED: {(self.transfered_files/num_chunks_required)*100}%")
                    for key, value in address_search.items():
                        if value[1] == math.inf:
                            PRINT_LOGS and print(f"Node {self.id} already had {key} previosly.")
                            self.transfered_files += 1
                        else:
                            PRINT_LOGS and print(f"Searching file {key} in {value[0][0]}:{value[0][1]} with transfer rate {value[1]} bytes/s.")
                            self.transfer_file(key, value)
                        print(f"PERCENTAGE OF THE FILE ALREADY TRANSFERRED: {(self.transfered_files/num_chunks_required)*100}%")
                else:
                    PRINT_LOGS and print("It was not possible to collect all file's chunks.")

        matching_files = self.look_for_chunks(file_wanted)

        print(f"PERCENTAGE OF THE FILE ALREADY TRANSFERRED: {(len(matching_files)/num_chunks_required)*100}%")

        if result_timeout and len(matching_files) < num_chunks_required :
            print("TIMEOUT ERROR: Did not find all chunks.")
        else:
            PRINT_LOGS and print("SUCCESS: Found all chunks!")
            self.merge_files(file_wanted, num_chunks_required)
    
    def merge_files(self, file_wanted, num_chunks):
        PRINT_LOGS and print("Merging files")

        # Caminho do diretório onde os chunks estão armazenados
        chunks_directory = f"{os.path.dirname(os.path.abspath(__file__))}/../nodes/{self.id}"
        
        # Nome do arquivo de saída
        output_file = os.path.join(chunks_directory, f"{file_wanted}")

        with open(output_file, 'wb') as outfile:
            for i in range(0, num_chunks):
                PRINT_LOGS and print(f"Merging file {file_wanted}.ch{i}")
                chunk_name = os.path.join(chunks_directory, f"{file_wanted}.ch{i}")
                if os.path.exists(chunk_name):
                    with open(chunk_name, 'rb') as infile:
                        outfile.write(infile.read())
                else:
                    PRINT_LOGS and print(f"Chunk {chunk_name} not found!")
                    break

        PRINT_LOGS and print(f"Files merged into {output_file}")
        print(f"SUCCESS: File {output_file} ready!")

