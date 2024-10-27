import sys
import threading
from src.node import Node
from src.sort import merge_sort_nodes

# Pergunta o ID do nó que vai procurar o arquivo
search_node = input("Digite o nó que vai procurar o arquivo: ")
try:
    search_node = int(search_node)
except ValueError:
    print("O nó precisa ser representado por um inteiro.")

# Pergunta os IDs dos nós que vão estar rodando seus sockets nesse computador
node_ids_input = input("Digite uma lista de IDs dos nós que vão estar executando nesse computador, separados por vírgula: ")
try:
    node_ids = [int(id.strip()) for id in node_ids_input.split(',')]
except ValueError:
    print("Precisa ser uma lista de números inteiros separados por vírgula.")
    sys.exit(1)

# Nessa variável vão ficar armazenados os nós encontrados durante a configuração
nodes = []

# Carregar configuração dos nós
with open('./config.txt', 'r') as arquivo:
    for line in arquivo:
        id, host, port, transfer_rate = line.split(' ')
        node = Node(id=id[:-1], host=host[:-1], port=port[:-1], transfer_rate=transfer_rate)
        nodes.append(node)
    merge_sort_nodes(nodes)

# Carregar topologia dos nós
with open('./topologia.txt', 'r') as arquivo:
    for line in arquivo:
        id, known_hosts = line.split(':')
        known_hosts = [int(num.strip()) for num in known_hosts.split(',')]
        nodes[int(id)].add_known_node(known_hosts)

# Carregar arquivo desejado
with open('./image.png.p2p', 'r') as arquivo:
    linhas = arquivo.readlines()
    file_wanted = linhas[0].strip()
    chunks = linhas[1].strip()
    flooding = linhas[2].strip()

# Função para iniciar o cliente de um nó em uma thread separada
def start_node_udp_socket(node):
    node.create_udp_socket()

# Criar e iniciar uma thread para cada ID de nó recebido
for node_id in node_ids:
    if node_id < len(nodes):
        node = nodes[node_id]
        thread = threading.Thread(target=start_node_udp_socket, args=(node,))
        thread.start()
    else:
        print(f"Nó com ID {node_id} não encontrado.")


# current_node = nodes[id]

# current_node.create_udp_socket()
# # nodes[id].create_client()

# with open('./image.png.p2p', 'r') as arquivo:
#     linhas = arquivo.readlines()

#     file_wanted = linhas[0].strip()
#     chunks = linhas[1].strip()
#     flooding = linhas[2].strip()

#     file_chunks = []
#     for i in range(chunks):
#         chunk_wanted = f"{file_wanted}.ch{i}"

#         for known_node in current_node.known_nodes:
#             current_node.create_client(known_node.host, known_node.port, chunk_wanted, flooding)
