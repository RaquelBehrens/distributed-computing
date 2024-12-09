import threading
import socket
import json
from node import Node
from settings import PRINT_LOGS


class ServerNode(Node):
    def __init__(self, id, host, port):
        super().__init__(id, host, port)
        self.message_buffer = []
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

                # Atualiza o relógio local (relógio lógico)
                # O relógio é incrementado com base no timestamp da mensagem recebida.
                # Isso garante que a ordem total seja mantida, pois o relógio lógico é ajustado
                # para ser maior que o valor anterior (maximiza o valor entre o relógio local e o timestamp recebido).
                self.logical_clock = max(self.logical_clock, deliver["timestamp"]) + 1

                # Adicionar mensagem ao buffer
                PRINT_LOGS and print(f"Add message to buffer of node {self.id}")
                self.message_buffer.append(deliver)

                # Ordena o buffer por timestamp
                # Isso garante que as mensagens serão processadas na ordem correta de acordo com seu timestamp,
                # estabelecendo a ordem total. Mesmo que as mensagens cheguem fora de ordem devido a latência de rede,
                # elas serão ordenadas aqui para que o processamento aconteça na ordem esperada.
                self.message_buffer.sort(key=lambda m: m["timestamp"])

                # Processa as mensagens na ordem correta
                while self.message_buffer:
                    # Obtém a próxima mensagem na fila
                    next_message = self.message_buffer[0]
                    PRINT_LOGS and print(f"Check timestamp {next_message['timestamp']} if equal to {last_committed+1}")
                    
                    # A mensagem é processada se seu timestamp for o próximo esperado
                    # 'last_committed' é o timestamp da última transação confirmada. Se o próximo timestamp na fila
                    # for o próximo valor esperado (last_committed + 1), isso indica que a ordem está sendo respeitada.
                    if next_message["timestamp"] == last_committed + 1:
                        # Processa a mensagem
                        self.process_message(next_message, address)

                        # Atualiza 'last_committed' para refletir o timestamp da transação processada
                        last_committed = next_message["timestamp"]

                        # Remove a mensagem processada do buffer
                        self.message_buffer.pop(0)
                    else:
                        # Se o timestamp for menor que o esperado (transação desordenada),
                        # remove a mensagem do buffer sem processá-la
                        if next_message["timestamp"] < last_committed + 1:
                            PRINT_LOGS and print(f"Discarding message with out-of-order timestamp: {next_message['timestamp']} (expected: {last_committed + 1})")
                            self.message_buffer.pop(0)  # Remove a mensagem desordenada
                        
                        # Se a ordem não for a esperada (timestamp descontinuado), quebra o loop e aguarda mais mensagens
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
        print(f"Result of DB {self.id}: {self.db}")

    def handle_udp_client(self, server_socket):
        while True:
            message, address = server_socket.recvfrom(1024)
            PRINT_LOGS and print(f"Broadcast received! Node {self.id}, with {self.host}:{self.port}, received: {message!r} from {address}")

            data_str = message.decode('utf-8')
            data_dict = json.loads(data_str)

            return data_dict, address
