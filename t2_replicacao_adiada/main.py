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


print("Digite quais clientes você gostaria de inicializar nesse terminal.")
print("Formato: 0; 1; 2")
print()

input_clients = input().split('; ')
with open('./config/client.txt', 'r') as arquivo:
    for line in arquivo:
        ine = line.strip()
        if not line:
            continue
        id, host, port = line.split(' ')
        if id[:-1] in input_clients:
            clients.append(ClientNode(id=int(id[:-1]), host=host[:-1], port=port.strip()))


if __name__ == '__main__':
    print("Digite quais servidores você gostaria de inicializar nesse terminal.")
    print("Formato: 0; 1; 2")
    print()

    input_servers = input().split('; ')
    for server in servers:
        if str(server.id) in input_servers:
            server.initialize()

    print("Digite o id do cliente que deseja fazer uma transação e a transação desejada.")
    print("Formato: 0; read,x; write,x,2; commit")
    print("Para encerrar, digite: Encerrar")
    print()
    
    operation = input().split('; ')
    transactions = []
    current_client = None

    while (operation[0].upper() != 'ENCERRAR'):
        for element in operation[1:]:
            current_tuple = ()
            for value in element.split(','):
                current_tuple += (value,)
            transactions.append(current_tuple)

        for client in clients:
            if str(client.id) == operation[0]:
                current_client = client
        
        if current_client != None:
            client.transaction(servers, transactions)
        else:
            print("Erro no input.")
            break

        operation = input().split('; ')
        transactions = []
        current_client = None

    sys.exit(0)
