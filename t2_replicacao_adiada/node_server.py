import threading
import random
import json

from node import Node


PRINT_LOGS = True; TIMEOUT = 120


class ServerNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.db = {'x':(0,0), 'y': (0,0)} #  {item1: (valor1, versao1), item2: (valor2, versao2)}

    def save_in_db(self, data):
        data_str = data.decode('utf-8')
        data_dict = json.loads(data_str)

        self.db[data_dict[0]] = tuple(data_dict[1:])

    def server(self, consult=False, deliver=None):
        last_committed = 0
        
        if consult:
            # recebe (client_id, (read, item)) do cliente c
            self.create_tcp_socket()
        else:
            while True:
                # recebe mensagem por abcast
                # deliver from UDP broadcast

                i = j = 0
                abort = False

                read_server = deliver['rs']
                write_server = deliver['ws']
                transactions = deliver['transactions']
                
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
                