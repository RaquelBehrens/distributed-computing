import sys
import json
from node_client import ClientNode
from node_server import ServerNode

clients = []
servers = []

# Função para inicializar servidores a partir de um arquivo de configuração
def initialize_servers(servers_data):
    global servers
    servers = []
    for server_data in servers_data:
        servers.append(ServerNode(id=server_data['node_id'], host=server_data['host'], port=server_data['port']))
    
    for server in servers:
        server.initialize()

# Função para inicializar clientes a partir de um arquivo de configuração
def initialize_clients(clients_data):
    global clients
    clients = []
    for client_data in clients_data:
        clients.append(ClientNode(id=client_data['node_id'], host=client_data['host'], port=client_data['port']))

# Função para rodar transações para um cliente
def run_transactions_for_client(client, events):
    transactions = []
    for event in events:
        for message in event['messages']:
            command = message['command']
            item = message['item']
            value = message['value']
            transactions.append((command, item, value))
        
        result = client.transaction(servers, transactions)
        transactions.clear()
        return result

# Função principal que lê o arquivo de testes e executa os testes
def run_tests(test_file):
    with open(test_file, 'r') as file:
        test_data = json.load(file)
    
    for test_case in test_data['test_cases']:
        print(f"Running test: {test_case['name']}")
        result = None
        
        # Inicializar servidores e clientes conforme especificado no teste
        initialize_servers(test_case['servers'])
        initialize_clients(test_case['clients'])
        
        # Rodar as transações para os clientes
        for event in test_case['events']:
            client = None
            for c in clients:
                if c.id == event['node_id']:
                    client = c
                    break
            
            if client:
                result = run_transactions_for_client(client, [event])
            else:
                print(f"Cliente com id {event['node_id']} não encontrado.")
        
        # Verificar o resultado esperado
        if client:
            # Aqui você pode adicionar a lógica de verificação de estado ou resposta final
            print(f"Resultado esperado: {test_case['result']}")
            if test_case['result'] == result:
                print('SUCCESS!')
        else:
            print(f"Falha ao encontrar o cliente para o teste {test_case['name']}")

if __name__ == '__main__':
    # Digite o nome do arquivo de teste
    print("Digite o nome do arquivo de teste (exemplo: tests.json):")
    test_file = input().strip()
    
    # Rodar os testes definidos no arquivo JSON
    run_tests(test_file)

    sys.exit(0)
