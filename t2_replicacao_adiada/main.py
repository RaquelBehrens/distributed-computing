import socket
import random


def isInWrite(read_item, write_list):
    for value in write_list:
        if (read_item == value[0]):
            return (True, value[1])
        
    return (False, None)

def transaction(num_servers, client, transactions):
    write_server = []
    read_server = []
    i = 0

    server_s = random.randint(0,num_servers-1)
    while (transactions[i][0] != 'commit' and transactions[i][0] != 'abort'):
        current_transaction = transactions[i]
        
        if (current_transaction[0] == 'write'):
            write_server.append(current_transaction[1:])

        if (current_transaction[0] == 'read'):
            in_write_server = isInWrite(current_transaction[1], write_server)
            if (in_write_server[0]):
                return_value = in_write_server[1]
            else:
                # envia (client_id, (read, item)) para server_s
                # recebe (cliente_id, (item, valor, versao)) de server_s
                read_server.append()

        i += 1

    if (transactions[i][0] == 'commit'):
        # envio por abcast
        # recebe (cliente_id, outcome) de server_s
        transaction_result = # outcome recebido
    else:
        transaction_result = 'abort'

def server(server_id):
    last_committed = 0
    # ???
    while (True):
        # recebe (client_id, (read, item)) do cliente c
        # ???
        # recebe mensagem por abcast
        i = j = 0
        abort = False
        
        while (i < len(read_server)):
            if ():
                # ???
                abort = True
                break
            i += 1

        if (not abort):
            last_committed += 1
            while (j < len(write_server)):
                # ???
                # ???
                j += 1


if __name__ == '__main__':
    pass
