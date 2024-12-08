import socket
import json

PRINT_LOGS = True; 

class AtomicDiffusion:
    def __init__(self, id, host, port):
        self.id = id
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, int(self.port+10)))
        self.server_socket.listen()

    def broadcast(self, nodes, ws, rs, transactions):
        for node in nodes:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((node.host, int(node.port+10)))

            message_sent = {
            'ws': ws,
            'rs': rs,
            'transactions': transactions
            }

            item_json = json.dumps(message_sent).encode('utf-8')
            client_socket.send(item_json)

    def deliver(self):
        try:
            conn, addr = self.server_socket.accept()
            PRINT_LOGS and print(f"Connected TCP: {self.id} - {self.host}:{self.port+10} received connection from {addr}")

            try:
                with conn:
                    PRINT_LOGS and print(f"Node {self.id} TCP received connection")

                    data = conn.recv(1024)
                    PRINT_LOGS and print(f"Data received.")

                    data_str = data.decode('utf-8')
                    data_dict = json.loads(data_str)
                    return data_dict

            except Exception as e:
                PRINT_LOGS and print(f"Error during file reception from {addr}: {e}")

            self.server_socket.close()  # Fecha o socket após a conexão
        except socket.timeout:
            PRINT_LOGS and print(f"Node {self.id} exceeded time limit while waiting for TCP connection.")
        except Exception as e:
            PRINT_LOGS and print(f"Error while accepting connection: {e}")
