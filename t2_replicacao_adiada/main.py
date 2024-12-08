from node import Node, ServerNode, ClientNode


if __name__ == '__main__':
    client = ClientNode(0, '127.0.0.1', 6000)
    servers = [ServerNode(0, '127.0.0.1', 6001), ServerNode(1, '127.0.0.1', 6002), ServerNode(2, '127.0.0.1', 6003)]

    client.transaction(servers, [('read','x',12),('commit',None)])
