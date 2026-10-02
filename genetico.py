import random

from jogo import PASSOS, correr


def dna_aleatorio():
    return random.choices([0, 1], weights=[95, 5], k=PASSOS)

# método selecionar: ESCOLHER UM PAI
# Quem vai mais longe tem que ter mais filhos, mas não só o melhor
# senão todos viram cópia dele. Seleção: entre 3 dos melhores
# fica o que foi mais longe
def selecionar(dinos, notas):
    # dinos: os 100 DNA's ([0,0,0,0,01,0,0,1...])
    # notas[i] é até qual passo o dinossauro i (dino[i]) chegou

    #sorteio QUALQUER dino do range e atribuo como vencedor
    vencedor = random.randrange(len(dinos))

    for _ in range (2):
        rival = random.randrange(len(dinos))
        if notas[rival] > notas[vencedor]:
            vencedor = rival
    return dinos[vencedor]

# com esta seleção tivemos quase 3x mais sucesso no primeiro cacto 

def cruzar(pai, mae):
    # sorteia o ponto de corte, randrange (1,400) dá 1 a 399
    # começamos em 1 para pegar no minimo um gene do pai

    corte = random.randrange(1, len(pai))
    # fatia da lista: slicing [inicio:fim], copio um pedaço da lista original
    # como nao tem nada no começo [##vazio##:corte], ele pega do começo até ANTES do corte,
    # mesma coisa com a mãe, comeca no corte e dps até o final, porque tá como vazio mae[corte:##vazio##]
    # dessa forma, os pedaçoes vão formar os 400 genes, um dino completo
    return pai[:corte] + mae[corte:]

# Mutar significa que de vez em quado (taxa %) troca aleatóriamente
def mutar(dna, taxa): 
    for i in range(len(dna)):
        # random.random() sorteia um numero entre 0 e 1 (0.654)
        if random.random() < taxa:
            dna[i] = 1 - dna[i]
    return dna

# Criar o ciclo inteiro, geração após geração

def evoluir(
    tamanho=100, # dinossauros por geração
    geracoes=100, # quantas voltas do ciclo
    taxa = 0.01, # chance de cada gene mudar
    elite = True, # response se o campeão passa direto
    semente = 1 # fixar a ordem dos sorteios e todos verem o mesmo resultado
):
    # para fixar os sorteios: com a mesma seed, saem os mesmos numeros na mesma ordem
    random.seed(semente)

    # list comprehension - criar uma nova lista, a partir de uma pré existente
    # fazendo ou nao modificações nos itens
    # sintaxe = [EXPRESSÃO, FOR, CONDICAO]
    dinos = [dna_aleatorio() for _ in range(tamanho)]


    historico = []

    # cada loop do for gerencia uma geração
    for geracao in range(geracoes):
        # cada um correrá a pista. Notas fica na mesma ordem de dinos
        # notas [0] é a nota de dinos [0]
        notas = [correr(dna) for dna in dinos]
        # o que tem que guardar aqui:
        # o mais longe que um dino chegou
        # quantos chegaram no 400
        # os 100 DNA's
        historico.append((max(notas), notas.count(PASSOS), dinos))

        nova = []
        # Elite: o melhor entra direto, sem cruzar e sem mutar
        if elite:
            campeao = notas.index(max(notas))
            nova.append(dinos[campeao])

        while len(nova) < tamanho:
            pai = selecionar(dinos,notas)
            mae = selecionar(dinos,notas)
            filho = cruzar(pai, mae)

            nova.append(mutar(filho,taxa))

        dinos = nova
    return historico

