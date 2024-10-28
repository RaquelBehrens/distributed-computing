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
