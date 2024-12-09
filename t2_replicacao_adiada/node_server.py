import threading
import socket
import json
from node import Node
from settings import PRINT_LOGS


class ServerNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.message_buffer = []

    def initialize(self):
        self.db = {'x':(0,0), 'y': (0,0)} #  {item1: (valor1, versao1), item2: (valor2, versao2)}

        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.bind((self.host, int(self.port)))
        
        PRINT_LOGS and print(f"Node {self.id} listening UDP in {self.host}:{self.port}.")
        
        thread_server = threading.Thread(target=self.server)
        thread_server.daemon = True
        thread_server.start()

    def save_in_db(self, data):
        data_str = data.decode('utf-8')
        data_dict = json.loads(data_str)

        self.db[data_dict[0]] = tuple(data_dict[1:])

    def server(self, consult=False):
        last_committed = 0
        
        if (consult):
            self.create_tcp_socket()
        else:
            while True:
                PRINT_LOGS and print(f"Deliver in Node {self.id}.")
                # recebe mensagem por abcast
                # deliver from UDP broadcast
                deliver, address = self.handle_udp_client(self.broadcast_socket)

                #Atualiza o relógio local
                self.logical_clock = max(self.logical_clock, deliver["timestamp"]) + 1

                # Adicionar mensagem ao buffer
                PRINT_LOGS and print(f"Add message to buffer of node {self.id}")
                self.message_buffer.append(deliver)

                # Ordenar buffer por timestamp
                self.message_buffer.sort(key=lambda m: m["timestamp"])

                # Entregar mensagens na ordem
                while self.message_buffer:
                    next_message = self.message_buffer[0]
                    PRINT_LOGS and print(f"Check timestamp {next_message['timestamp']} if equal to {last_committed+1}")
                    if next_message["timestamp"] == last_committed + 1:
                        self.process_message(next_message, address)
                        last_committed = next_message["timestamp"]
                        self.message_buffer.pop(0)
                    else:
                        break

    def process_message(self, deliver, address):
        PRINT_LOGS and print(f"Begin to process deliver in node {self.id}")

        i = j = 0
        abort = False

        read_server = deliver['rs']
        write_server = deliver['ws']
        transactions = deliver['transactions']

        result = None
        
        while (i < len(read_server)):
            if (self.db[read_server[i][0]][1] > read_server[i][2]):
                abort = True
                transactions.clear()
                result = "abort"
            i += 1

        if (not abort):
            # write server = [[x, 0], [x,3], [y, 3]]
            # {item1: (valor1, versao1), item2: (valor2, versao2)}
            while (j < len(write_server)):
                version = self.db[write_server[j][0]][1] + 1
                value = int(write_server[j][1])
                self.db[write_server[j][0]] = (value, version)
                
                j += 1
        
            result = "commit"

        PRINT_LOGS and print(f"Sending result of node {self.id}, with {self.host}:{self.port}, to {address}: {result}")
        # Envia confirmação de recebimento de mensagem ao sender
        result_message = json.dumps(
            {
                'result': result,
                'node': self.id
             
             })
        self.broadcast_socket.sendto(result_message.encode('utf-8'), address)

    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            PRINT_LOGS and print(f"Broadcast received! Node {self.id}, with {self.host}:{self.port}, received: {message!r} from {address}")

            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            return data_dict, address
