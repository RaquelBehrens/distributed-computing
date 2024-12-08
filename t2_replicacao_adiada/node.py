import threading
import socket
import random
import json
import time
from broadcast import AtomicDiffusion 


PRINT_LOGS = True; TIMEOUT = 120


class Node():
    def __init__(self, id, host, port):
        super().__init__()
        self.id = id
        self.host = host
        self.port = port
        self.ad = AtomicDiffusion(id, host, port)

    def configure_node(self, host, port):
        self.host = host
        self.port = port

    def create_tcp_socket(self, result=None):
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
                self.handle_tcp_client(conn, addr, result)  # Chama a função para lidar com a conexão
                server_socket.close()  # Fecha o socket após a conexão
            except socket.timeout:
                PRINT_LOGS and print(f"Node {self.id} exceeded time limit while waiting for TCP connection.")
            except Exception as e:
                PRINT_LOGS and print(f"Error while accepting connection: {e}")

    def handle_tcp_client(self, conn, addr, result):
        try:
            with conn:
                PRINT_LOGS and print(f"Node {self.id} TCP received connection")
                data = conn.recv(1024)
                
                PRINT_LOGS and print(f"Data received and saved.")

                data_str = data.decode('utf-8')
                data_dict = json.loads(data_str)

                type = data_dict['type']

                if type == 'send_transaction':
                    transaction_data = data_dict['transaction']
                    try:
                        db_data = self.db[transaction_data]
                        item_json = json.dumps(db_data).encode('utf-8')  # item é o dicionário

                    except KeyError:
                        PRINT_LOGS and print(f"Item not found in DB.")

                        item_json = json.dumps(None).encode('utf-8')  # item é o dicionário

                    conn.send(item_json)

                elif type == 'result':
                    result_json = json.dumps(result).encode('utf-8')

                    conn.send(result_json)

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
            item_json = json.dumps(item).encode('utf-8')
            client_socket.send(item_json)
            PRINT_LOGS and print("Item sent successfully")

            data = client_socket.recv(1024)
            data_str = data.decode('utf-8')
            data_dict = json.loads(data_str)

        except Exception as e:
            PRINT_LOGS and print(f"Error during transmission: {e}")
        finally:
            client_socket.close()

            if item['type'] == 'send_transaction':
                if (data_dict):
                    return tuple(item['transaction']) + tuple(data_dict)
            elif item['type'] == 'result':
                return data_dict


class ServerNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.db = {'x':(0,0), 'y': (0,0)} #  {item1: (valor1, versao1), item2: (valor2, versao2)}

    def save_in_db(self, data):
        data_str = data.decode('utf-8')
        data_dict = json.loads(data_str)

        self.db[data_dict[0]] = tuple(data_dict[1:])

    def server(self, consult=False):
        last_committed = 0
        
        if consult:
            # recebe (client_id, (read, item)) do cliente c
            self.create_tcp_socket()
        else:
            while True:
                # recebe mensagem por abcast
                received = self.ad.deliver()
                i = j = 0
                abort = False

                read_server = received['rs']
                write_server = received['ws']
                transactions = received['transactions']
                
                while (i < len(read_server)):
                    if (self.db[read_server[i][0]][1] > read_server[i][2]):
                        # mandar pro cliente que a operação resultou em abort
                        self.create_tcp_socket('abort')
                        abort = True
                        transactions.clear()
                        break
                    i += 1

                if (not abort):
                    last_committed += 1
                    # write server = [[x, 0], [x,3], [y, 3]]
                    # {item1: (valor1, versao1), item2: (valor2, versao2)}
                    while (j < len(write_server)):
                        version = self.db[write_server[j][0]][1] + 1
                        value = write_server[j][1]
                        self.db[write_server[j][0]] = (value, version)
                        
                        j += 1
                    
                    self.create_tcp_socket('commit')
                


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

    # transactions = [('read',x), ('write',y, 2), ('commit')]
    def transaction(self, servers, transactions):
        write_server = []
        read_server = []
        i = 0

        server_s = self.select_server(random.randint(0,len(servers)-1), servers)
        while (transactions[i][0] != 'commit' and transactions[i][0] != 'abort'):        
            current_transaction = transactions[i]
            
            if (current_transaction[0] == 'write'):
                write_server.append(current_transaction[1:]) #[item, valor]

            if (current_transaction[0] == 'read'):
                in_write_server = self.isInWrite(current_transaction[1], write_server)
                if (in_write_server[0]):
                    print(f"Value {in_write_server[1]} of {current_transaction[1]} is up to date.")
                else:
                    server_thread = threading.Thread(target=server_s.server, args=(True,))
                    server_thread.start()

                    message = {
                        'type': 'send_transaction',
                        'transaction': current_transaction[1]
                    }

                    result = self.create_tcp_client(server_s.host, server_s.port, message)
                    if (result):
                        read_server.append(result)

            i += 1

        if (transactions[i][0] == 'commit'):
            # envio por abcast
            self.ad.broadcast(servers, write_server, read_server, transactions)

            message = {
                'type': 'result',
            }

            outcome = self.create_tcp_client(server_s.host, server_s.port, message)
            # recebe (cliente_id, outcome) de server_s
            transaction_result = outcome # outcome recebido
        else:
            transaction_result = 'abort'

        print(f"Result of transaction = {transaction_result}")
