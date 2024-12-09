import sys

from node_client import ClientNode
from node_server import ServerNode


if __name__ == '__main__':
    client = ClientNode(0, '127.0.0.1', 6000)
    servers = [ServerNode(1, '127.0.0.1', 6001), ServerNode(2, '127.0.0.1', 6002), ServerNode(3, '127.0.0.1', 6003)]
    for serve in servers:
        serve.initialize()

    print("Digite o id do cliente que deseja fazer uma transação e a transação desejada.")
    print("Formato: 0; read,x; write,x,2; commit")
    print("Para encerrar, digite: Encerrar")
    print()
    
    operation = input().split('; ')
    transactions = []

    while (operation[0] != 'Encerrar'):
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
