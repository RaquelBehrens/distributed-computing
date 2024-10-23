class Node:
    def __init__(self, id, lala):
        self.id = id
        self.lala = lala

def merge_sort_nodes(lista):
    if len(lista) <= 1:
        return lista

    meio = len(lista) // 2
    esquerda = lista[:meio]
    direita = lista[meio:]

    esquerda = merge_sort_nodes(esquerda)
    direita = merge_sort_nodes(direita)

    return merge_nodes(esquerda, direita)

def merge_nodes(esquerda, direita):
    resultado = []
    i = j = 0

    while i < len(esquerda) and j < len(direita):
        if esquerda[i].id < direita[j].id:
            resultado.append(esquerda[i])
            i += 1
        else:
            resultado.append(direita[j])
            j += 1

    resultado.extend(esquerda[i:])
    resultado.extend(direita[j:])

    return resultado

# Exemplo de uso com objetos Node
nodes = [Node(38, 1), Node(27, 2), Node(43, 3), Node(3, 4), Node(9, 5), Node(82, 6), Node(10, 5)]
nodes_ordenados = merge_sort_nodes(nodes)

# Imprimir os ids dos nodes ordenados
print("Nodes ordenados por id:", [node.id for node in nodes_ordenados])
