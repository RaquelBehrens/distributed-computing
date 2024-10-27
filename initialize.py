import sys
import threading
from src.node import Node
from src.sort import merge_sort_nodes

# Recebe a lista de inteiros passada pela linha de comando
if len(sys.argv) > 1:
    node_ids = [int(arg) for arg in sys.argv[1:]]
else:
    print("Por favor, passe uma lista de inteiros representando IDs dos nós.")
    sys.exit(1)

nodes = []

# Carregar configuração dos nós
with open('./config.txt', 'r') as arquivo:
    for line in arquivo:
        id, host, port, transfer_rate = line.split(' ')
        nodo = Node(id=id[:-1], host=host[:-1], port=port[:-1], transfer_rate=transfer_rate)
        nodes.append(nodo)
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
    node = nodes[node_id]
    thread = threading.Thread(target=start_node_udp_socket, args=(node,))
    thread.start()


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
