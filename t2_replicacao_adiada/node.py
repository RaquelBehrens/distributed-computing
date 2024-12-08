import threading
import socket
import random
import json
import time


PRINT_LOGS = True; TIMEOUT = 120


class Node():
    def __init__(self, id, host, port):
        super().__init__()
        self.id = id
        self.host = host
        self.port = port

    def configure_node(self, host, port):
        self.host = host
        self.port = port

    def create_tcp_socket(self):
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
                self.handle_tcp_client(conn, addr)  # Chama a função para lidar com a conexão
                server_socket.close()  # Fecha o socket após a conexão
            except socket.timeout:
                PRINT_LOGS and print(f"Node {self.id} exceeded time limit while waiting for TCP connection.")
            except Exception as e:
                PRINT_LOGS and print(f"Error while accepting connection: {e}")

    def handle_tcp_client(self, conn, addr):
        try:
            with conn:
                PRINT_LOGS and print(f"Node {self.id} TCP received connection")
                data = conn.recv(1024)
                
                PRINT_LOGS and print(f"Data received and saved.")

                data_str = data.decode('utf-8')
                data_dict = json.loads(data_str)

                try:
                    db_data = self.db[data_dict]
                    item_json = json.dumps(db_data).encode('utf-8')  # item é o dicionário

                except KeyError:
                    PRINT_LOGS and print(f"Item not found in DB.")

                    item_json = json.dumps(None).encode('utf-8')  # item é o dicionário

                conn.send(item_json)

        except Exception as e:
            PRINT_LOGS and print(f"Error during file reception from {addr}: {e}")

    def create_tcp_client(self, original_host, original_port, item):
        # Cria o socket TCP do cliente
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        PRINT_LOGS and print(f"Node {self.id} is trying to connect to TCP {original_host}:{original_port}")
        client_socket.connect((original_host, int(original_port)))
        PRINT_LOGS and print(f"Node {self.id} connected to TCP {original_host}:{original_port}")

        PRINT_LOGS and print(f"Node {self.id} will try to send item")
        time.sleep(3)
        try:
            item_json = json.dumps(item).encode('utf-8')  # item é o dicionário
            client_socket.send(item_json)
            PRINT_LOGS and print("Item sent successfully")

            data = client_socket.recv(1024)
            data_str = data.decode('utf-8')
            data_dict = json.loads(data_str)

        except Exception as e:
            PRINT_LOGS and print(f"Error during transmission: {e}")
        finally:
            client_socket.close()

            if (data_dict):
                return tuple(item) + tuple(data_dict)


class ServerNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.db = {'x':(10,)} #  {item1: (valor1, versao1), item2: (valor2, versao2)}

    def save_in_db(self, data):
        data_str = data.decode('utf-8')
        data_dict = json.loads(data_str)

        self.db[data_dict[0]] = tuple(data_dict[1:])

    def server(self):
        last_committed = 0
        # # ???
        
        # recebe (client_id, (read, item)) do cliente c
        self.create_tcp_socket()
    #     # ???
    #     # recebe mensagem por abcast
    #     i = j = 0
    #     abort = False
        
    #     while (i < len(read_server)):
    #         if ():
    #             # ???
    #             abort = True
    #             break
    #         i += 1

    #     if (not abort):
    #         last_committed += 1
    #         while (j < len(write_server)):
    #             # ???
    #             # ???
    #             j += 1


class ClientNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
    
    def isInWrite(self, read_item, write_list):
        for value in write_list:
            if (read_item == value[0]):
                return (True, value[1])
            
        return (False, None)

    def select_server(self, id_server, list_servers):
        for server in list_servers:
            if server.id == id_server:
                return server

    # transactions = [('read',x), ('write',y), ('commit')]
    def transaction(self, servers, transactions):
        write_server = []
        read_server = []
        i = 0

        server_s = self.select_server(random.randint(0,len(servers)-1), servers)
        while (transactions[i][0] != 'commit' and transactions[i][0] != 'abort'):        
            current_transaction = transactions[i]
            
            if (current_transaction[0] == 'write'):
                write_server.append(current_transaction[1:])

            if (current_transaction[0] == 'read'):
                in_write_server = self.isInWrite(current_transaction[1], write_server)
                if (in_write_server[0]):
                    return_value = in_write_server[1]
                else:
                    server_thread = threading.Thread(target=server_s.server)
                    server_thread.start()

                    result = self.create_tcp_client(server_s.host, server_s.port, current_transaction[1])
                    if (result):
                        read_server.append(result)

            i += 1

        if (transactions[i][0] == 'commit'):
            # envio por abcast
            # recebe (cliente_id, outcome) de server_s
            transaction_result = 'outcome' # outcome recebido
        else:
            transaction_result = 'abort'

