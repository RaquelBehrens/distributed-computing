import sys

from node_client import ClientNode
from node_server import ServerNode

clients = []
servers = []

with open('./config/server.txt', 'r') as arquivo:
    for line in arquivo:
        line = line.strip()
        if not line:
            continue
        id, host, port = line.split(' ')
        servers.append(ServerNode(id=int(id[:-1]), host=host[:-1], port=port.strip()))

with open('./config/client.txt', 'r') as arquivo:
    for line in arquivo:
        ine = line.strip()
        if not line:
            continue
        id, host, port = line.split(' ')
        clients.append(ClientNode(id=int(id[:-1]), host=host[:-1], port=port.strip()))

if __name__ == '__main__':
    for server in servers:
        server.initialize()

    print("Digite o id do cliente que deseja fazer uma transação e a transação desejada.")
    print("Formato: 0; read,x; write,x,2; commit")
    print("Para encerrar, digite: Encerrar")
    print()
    
    operation = input().split('; ')
    transactions = []

    for client in clients:
        while (operation[0].upper() != 'ENCERRAR'):
            for element in operation[1:]:
                current_tuple = ()
                for value in element.split(','):
                    current_tuple += (value,)
                transactions.append(current_tuple)

            client.transaction(servers, transactions)

            for server in servers:
                print(f"Result of DB {server.id}: {server.db}")
            print()

            operation = input().split('; ')
            transactions = []

    sys.exit(0)
