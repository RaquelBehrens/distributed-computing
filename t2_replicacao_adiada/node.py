import threading
import socket
import json
import time


PRINT_LOGS = True; TIMEOUT = 120


class Node():
    def __init__(self, id, host, port):
        super().__init__()
        self.id = id
        self.host = host
        self.port = port

        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.bind((self.host, int(self.port)))
        PRINT_LOGS and print(f"Node {self.id} listening UDP in {self.host}:{self.port}.")
        threading.Thread(target=self.handle_udp_client, args=(self.broadcast_socket, )).start()

    def configure_node(self, host, port):
        self.host = host
        self.port = port

    def create_tcp_socket(self, result=None):
            PRINT_LOGS and print(f"Node {self.id} trying to create TCP connection on {self.host}:{self.port}.")
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
                PRINT_LOGS and print(f"TCP Connection of Node {self.id} closed")
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
            PRINT_LOGS and print(f"TCP Connection of Node {self.id} closed")
            client_socket.close()

            if item['type'] == 'send_transaction':
                if (data_dict):
                    return tuple(item['transaction']) + tuple(data_dict)
            elif item['type'] == 'result':
                return data_dict


    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            PRINT_LOGS and print(f"Broadcast received! Node {self.id}, with {self.host}:{self.port}, received: {message!r} from {address}")

            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            self.server(False, data_dict)
