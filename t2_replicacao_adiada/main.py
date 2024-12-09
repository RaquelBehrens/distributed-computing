from node_client import ClientNode
from node_server import ServerNode


if __name__ == '__main__':
    client = ClientNode(0, '127.0.0.1', 6000)
    servers = [ServerNode(1, '127.0.0.1', 6001), ServerNode(2, '127.0.0.1', 6002), ServerNode(3, '127.0.0.1', 6003)]

    client.transaction(servers, [('read','x'),('write','x',2),('commit',)])

    for server in servers:
        print(server.db)
