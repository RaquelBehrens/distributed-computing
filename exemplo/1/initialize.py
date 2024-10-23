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

for node in nodes:
    print(node.id + ' ' + node.host + ' ' + node.port + ' ' + node.transfer_rate)
    print(node.known_nodes)
        

nodes[id].create_udp_socket()
# nodes[id].create_client()