import sys
import threading
import json
from src.node import Node
from src.sort import merge_sort_nodes


# Pergunta os IDs dos nós que vão estar rodando seus sockets nesse computador
node_ids_input = input("Digite uma lista de IDs dos nós que vão estar executando nesse computador, separados por vírgula: ")
try:
    node_ids = [int(id.strip()) for id in node_ids_input.split(',')]
except ValueError:
    print("Precisa ser uma lista de números inteiros separados por vírgula.")
    sys.exit(1)

# Nessa variável vão ficar armazenados os nós encontrados durante a configuração
nodes = []

# Carregar topologia dos nós
with open('./topologia.txt', 'r') as arquivo:
    for line in arquivo:
        id, known_hosts = line.split(':')
        if (int(id) in node_ids):
            node = Node(id=id)
            known_hosts = [Node(id=num.strip()) for num in known_hosts.split(',')]
            node.add_known_node(known_hosts)
            nodes.append(node)
    # merge_sort_nodes(nodes)

# Carregar configuração dos nós
with open('./config.txt', 'r') as arquivo:
    for line in arquivo:
        id, host, port, transfer_rate = line.split(' ')
        for node in nodes:
            if (id[:-1] == node.id):
                node.configure_node(host=host[:-1], port=port[:-1], transfer_rate=transfer_rate.replace('\n',''))
            else:
                for known_node in node.known_nodes:
                    if (id[:-1] == known_node.id):
                        known_node.configure_node(host=host[:-1], port=port[:-1], transfer_rate=transfer_rate)

# Essa variável representará o tempo de busca no nodo
TIMEOUT = 2

# Função para iniciar o cliente de um nó em uma thread separada
def start_node_udp_socket(node):
    node.create_udp_socket()

# Cria e inicia uma thread para cada ID de nó recebido
for node in nodes:
    thread = threading.Thread(target=start_node_udp_socket, args=(node, ))
    thread.daemon = True
    thread.start()

# Recebe e procura o arquivo
while True:
    # if (len(nodes) == 1):
    #     print("Digite o caminho do arquivo desejado para começar a busca ou [sair] para encerrar o programa.")
    # else:
    #     print("Digite o nó que vai procurar o arquivo e o caminho do arquivo desejado para começar a busca ou [sair] para encerrar o programa.")

    command = input().split()
    if (command[0] == 'sair'):
        print("Encerrando programa.")
        sys.exit(0)
    else:
        if (command):
            if (len(command) == 2):
                search_node_id = command[0]
                for node in nodes:
                    if (node.id == search_node_id):
                        search_node = node
            else:
                search_node = nodes[0]

            file_path = command[-1]
            # Carregar arquivo desejado
            with open(file_path, 'r') as file:
                linhas = file.readlines()
                file_wanted = linhas[0].strip()
                chunks = int(linhas[1].strip())
                flooding = int(linhas[2].strip())
    
            search_node.configure_known_chunks(file_wanted)
            message_sent = {
                'type_client': 'searching_file',
                'file_wanted': file_wanted,
                'address': (search_node.host, search_node.port),
                'original_address': (search_node.host, search_node.port),
                'flooding': flooding
            }
            message_json = json.dumps(message_sent)

            for known_node in search_node.known_nodes:
                search_node.create_udp_client(known_node.host, known_node.port, message_json)

            threading.Thread(target=search_node.search_chunks, args=(chunks, TIMEOUT)).start()
