from node import Node
from sort import merge_sort_nodes

nodes = []
id = Node

with open('./config.txt', 'r') as arquivo:
    for line in arquivo:
        id, host, port, transfer_rate = line.split(' ')
        nodo = Node(id=id[:-1], host=host[:-1], port=port[:-1], transfer_rate=transfer_rate)
        nodes.append(nodo)
    merge_sort_nodes(nodes)


with open('./topologia.txt', 'r') as arquivo:
    for line in arquivo:
        id, known_hosts = line.split(':')
        known_hosts = [int(num.strip()) for num in known_hosts.split(',')]
        nodes[int(id)].add_known_node(known_hosts)
        id = int(id)
        

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

    
