import time
import random
import socket
import json
from node import Node
from settings import PRINT_LOGS


class ClientNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def isInWrite(self, read_item, write_list):
        return_value = None
        for value in write_list:
            if (read_item == value[0]):
                return_value = (True, value[1])
        
        if (return_value == None):
            return (False, None)
        
        return return_value

    def select_server(self, id_server, list_servers):
        for server in list_servers:
            if int(server.id) == int(id_server):
                return server
        return None

    # transactions = [('read',x), ('write',y, 2), ('commit')]
    def transaction(self, servers, transactions):
        write_server = []
        read_server = []
        i = 0

        server_s = self.select_server(random.choice(servers).id, servers)
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
                    message = {
                        'type': 'send_transaction',
                        'transaction': current_transaction[1]
                    }

                    max_attempts = 10
                    result = None
                    for pings in range(max_attempts):
                        PRINT_LOGS and print(f"TRYING TO CONNECT TO TCP Ping {pings}")
                        try:
                            result = self.create_tcp_client(server_s.host, server_s.port, message)
                            break
                        except ConnectionRefusedError as e:
                            PRINT_LOGS and print(f"TCP Connection refused: {e}")
                            if pings == max_attempts - 1:
                                PRINT_LOGS and print("Max attempts reached, no acknowledgment received.")
                                break

                    if (result):
                        read_server.append(result)
            i += 1

        PRINT_LOGS and print(f"Transaction {i}: {transactions[i]}")
        if (transactions[i][0] == 'commit'):    
            # envio por abcast
            self.broadcast(servers, write_server, read_server, transactions)
            results = self.handle_udp_answer(servers)
            if results:
                transaction_result = results[server_s.id] # outcome recebido
            else:
                transaction_result = None
        else:
            transaction_result = 'abort'

        print(f"Result of transaction = {transaction_result}")
        return transaction_result

    def broadcast(self, nodes, ws, rs, transactions):
        current_timestamp = time.time()

        message_sent = {
        'ws': ws,
        'rs': rs,
        'transactions': transactions,
        "timestamp": current_timestamp,
        "sender": self.id
        }

        item_json = json.dumps(message_sent).encode('utf-8')
        
        for node in nodes:
            PRINT_LOGS and print(f"Broadcast from {self.host}:{self.port} to {node.host}:{node.port}")
            self.udp_socket.sendto(item_json, (node.host, int(node.port)))

    def handle_udp_answer(self, servers):
        results = {}
        timeout = 5
        self.udp_socket.settimeout(timeout)

        for _ in range(len(servers)):
            try:
                data, server = self.udp_socket.recvfrom(1024)
                answer = json.loads(data.decode('utf-8'))
                result = answer['result']
                node = answer['node']
                if result:
                    PRINT_LOGS and print(f"Result of broadcast from {self.host}:{self.port} to {server[0]}:{server[1]}: {result}")
                    results[node] = result
            except socket.timeout:
                PRINT_LOGS and print(f'BROADCAST TIMED OUT FOR NODE {node.id} - no result received from {node.host}:{node.port}')    
        return results
        