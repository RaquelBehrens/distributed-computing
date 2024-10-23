from node import Node
from sort import merge_sort_nodes

nodes = []


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
        

# for node in nodes:
#     print(node.id + ' ' + node.host + ' ' + node.port + ' ' + node.transfer_rate)
#     print(node.known_nodes)
        

# Initialize servers
for node in nodes:
    node.create_socket()

# Initialize clients
for node in nodes:
    node.create_client()