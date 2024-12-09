import threading
import random
import socket
import json
import time

from node import Node

PRINT_LOGS = True; TIMEOUT = 120


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

        server_s = self.select_server(random.randint(1,len(servers)), servers)
        while (transactions[i][0] != 'commit' and transactions[i][0] != 'abort'):
            current_transaction = transactions[i]
            PRINT_LOGS and print(f"Transaction {i}: {transactions[i]}")
            print(current_transaction)
            
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

        PRINT_LOGS and print(f"Transaction {i}: {transactions[i]}")
        if (transactions[i][0] == 'commit'):    
            # envio por abcast
            self.broadcast(servers, write_server, read_server, transactions)

            # server_thread = threading.Thread(target=server_s.server, args=(True,))
            # server_thread.start()


            conexoes_tcp = []

            for server in servers:
                try:
                    with socket.create_connection((server.host, server.port), 10):
                        conexoes_tcp.append(True)
                except (socket.timeout, ConnectionRefusedError, OSError):
                    conexoes_tcp.append(False)


            try:
                with socket.create_connection((self.host, self.port), 10):
                    conexoes_tcp.append(True)
            except (socket.timeout, ConnectionRefusedError, OSError):
                conexoes_tcp.append(False)


            print(conexoes_tcp)
            time.sleep(30)


            message = {
                'type': 'result',
            }

            PRINT_LOGS and print(f"Creating TCP {server_s.host}:{server_s.port} to receive outcome")
            outcome = self.create_tcp_client(server_s.host, server_s.port, message)
            # recebe (cliente_id, outcome) de server_s
            transaction_result = outcome # outcome recebido
        else:
            transaction_result = 'abort'

        print(f"Result of transaction = {transaction_result}")

    def broadcast(self, nodes, ws, rs, transactions):
        for node in nodes:
            PRINT_LOGS and print(f"Broadcast from {self.host}:{self.port} to {node.host}:{node.port}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            message_sent = {
            'ws': ws,
            'rs': rs,
            'transactions': transactions
            }

            item_json = json.dumps(message_sent).encode('utf-8')
            client_socket.sendto(item_json, (node.host, int(node.port)))
