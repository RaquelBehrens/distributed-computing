import threading
import socket
import json
from node import Node
from settings import PRINT_LOGS


class ServerNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.db = {'x':(0,0), 'y': (0,0)} #  {item1: (valor1, versao1), item2: (valor2, versao2)}

    def initialize(self):
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.bind((self.host, int(self.port)))
        
        PRINT_LOGS and print(f"Node {self.id} listening UDP in {self.host}:{self.port}.")
        
        thread_broadcast = threading.Thread(target=self.server)
        thread_broadcast.daemon = True
        thread_broadcast.start()

        thread_tcp = threading.Thread(target=self.server, args=(True,))
        thread_tcp.daemon = True
        thread_tcp.start()

    def save_in_db(self, data):
        data_str = data.decode('utf-8')
        data_dict = json.loads(data_str)

        self.db[data_dict[0]] = tuple(data_dict[1:])

    def server(self, consult=False):
        last_committed = 0
        
        if (consult):
            while True:
                self.create_tcp_socket()
        else:
            while True:
                PRINT_LOGS and print(f"Deliver in Node {self.id}.")
                # recebe mensagem por abcast
                # deliver from UDP broadcast
                deliver, address = self.handle_udp_client(self.broadcast_socket)

                i = j = 0
                abort = False

                read_server = deliver['rs']
                write_server = deliver['ws']
                transactions = deliver['transactions']

                result = None
                
                while (i < len(read_server)):
                    if (self.db[read_server[i][0]][1] > read_server[i][2]):
                        print(f"entrou no abort, Node {self.id}")
                        # mandar pro cliente que a operação resultou em abort
                        # self.create_tcp_socket('abort')
                        abort = True
                        transactions.clear()
                        result = "abort"
                    i += 1

                if (not abort):
                    last_committed += 1
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
                result_message = json.dumps({'result': result})
                self.broadcast_socket.sendto(result_message.encode('utf-8'), address)

                print(f"Result of DB {self.id}: {self.db}")
                
    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            PRINT_LOGS and print(f"Broadcast received! Node {self.id}, with {self.host}:{self.port}, received: {message!r} from {address}")

            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            return data_dict, address
