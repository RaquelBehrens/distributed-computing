from node import Node, ServerNode, ClientNode
import threading


if __name__ == '__main__':
    client = ClientNode(0, '127.0.0.1', 6000)
    servers = [ServerNode(0, '127.0.0.1', 6001), ServerNode(1, '127.0.0.1', 6002), ServerNode(2, '127.0.0.1', 6003)]

    for server in servers:
        threading.Thread(target=server.server).start()

    client.transaction(servers, [('read','x'),('write','x',2),('commit',)])

    for server in servers:
        print(server.db)
